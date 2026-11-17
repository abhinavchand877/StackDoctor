import os
import re
import json
import tempfile
from typing import List, Dict, Any
from app.analyzers.scanner_runner import is_tool_available, run_command_safely

SECRET_PATTERNS = [
    {
        "id": "SEC-001",
        "name": "OpenAI / Generic AI API Key",
        "regex": re.compile(r"""(?:sk-[a-zA-Z0-9]{20,48}|sk-proj-[a-zA-Z0-9_\-]{30,80})"""),
        "severity": "Critical",
        "penalty": 25,
    },
    {
        "id": "SEC-002",
        "name": "AWS Access Key ID",
        "regex": re.compile(r"""(?:AKIA[0-9A-Z]{16})"""),
        "severity": "Critical",
        "penalty": 25,
    },
    {
        "id": "SEC-003",
        "name": "GitHub Personal Access Token",
        "regex": re.compile(r"""(?:ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59})"""),
        "severity": "Critical",
        "penalty": 25,
    },
    {
        "id": "SEC-004",
        "name": "Generic Private Cryptographic Key Block",
        "regex": re.compile(r"""-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"""),
        "severity": "Critical",
        "penalty": 25,
    },
    {
        "id": "SEC-005",
        "name": "Slack Token / Webhook",
        "regex": re.compile(r"""(?:xox[baprs]-[0-9a-zA-Z]{10,48}|https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+)"""),
        "severity": "High",
        "penalty": 15,
    },
    {
        "id": "SEC-006",
        "name": "Stripe Live Secret Key",
        "regex": re.compile(r"""(?:sk_live_[0-9a-zA-Z]{24,34})"""),
        "severity": "Critical",
        "penalty": 25,
    },
    {
        "id": "SEC-007",
        "name": "Hardcoded Password / Secret Assignment",
        "regex": re.compile(
            r"""(?i)(?:password|secret_key|jwt_secret|api_key|access_token|db_password)\s*[:=]\s*["']([^"'\s]{8,})["']"""
        ),
        "severity": "High",
        "penalty": 15,
    },
]

def mask_secret(value: str) -> str:
    """Masks a secret string preserving only the first 2-3 prefix characters."""
    if not value:
        return "[REDACTED]"
    clean = value.strip()
    if len(clean) <= 6:
        return "******"
    prefix = clean[:3]
    return f"{prefix}{'*' * min(16, len(clean) - 3)}"


class SecurityAnalyzer:
    """
    Module 5: Statically scans files for committed credentials, secret patterns, exposed environment files, and key files.
    """

    def __init__(self, root_dir: str, detected_info: Dict[str, Any], max_file_size: int = 2 * 1024 * 1024):
        self.root_dir = root_dir
        self.detected_info = detected_info
        self.max_file_size = max_file_size

    def analyze(self) -> List[Dict[str, Any]]:
        findings = []

        # 1. Check for committed .env files containing active environment variables
        env_files = [".env", ".env.local", ".env.production", ".env.staging"]
        for ef in env_files:
            ef_path = os.path.join(self.root_dir, ef)
            if os.path.exists(ef_path):
                findings.append({
                    "rule_id": "SEC-010",
                    "module": "Security Configuration",
                    "title": f"Sensitive Environment File Committed ({ef})",
                    "description": f"Discovered an active environment file '{ef}' directly in the repository archive.",
                    "severity": "High",
                    "file_path": ef,
                    "explanation": "Environment files often contain production credentials, API secrets, and database connection strings. Committing them risks credential compromise.",
                    "recommendation": f"Add '{ef}' to .gitignore and provide a template .env.example with dummy values instead.",
                    "penalty": 15,
                })

        # 2. Check if .gitignore excludes .env
        gitignore_path = os.path.join(self.root_dir, ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                    gi_content = f.read()
                if ".env" not in gi_content and "*.env" not in gi_content:
                    findings.append({
                        "rule_id": "SEC-011",
                        "module": "Security Configuration",
                        "title": "Missing .env in .gitignore",
                        "description": "The .gitignore file does not explicitly ignore '.env' files.",
                        "severity": "Medium",
                        "file_path": ".gitignore",
                        "explanation": "Developers creating local .env files risk inadvertently staging and pushing them if not ignored.",
                        "recommendation": "Add '.env' and '.env.*.local' patterns to .gitignore.",
                        "penalty": 8,
                    })
            except Exception:
                pass

        # 3. Check for raw private key files (.pem, .key, .pfx)
        for root, _, files in os.walk(self.root_dir):
            for file_name in files:
                lower = file_name.lower()
                if lower.endswith((".pem", ".key", ".pfx", ".pkcs12", ".id_rsa", ".id_ed25519")):
                    rel_p = os.path.relpath(os.path.join(root, file_name), self.root_dir)
                    findings.append({
                        "rule_id": "SEC-012",
                        "module": "Security Configuration",
                        "title": f"Private Cryptographic Key File Committed ({file_name})",
                        "description": f"Found private key file '{rel_p}' bundled in the archive.",
                        "severity": "Critical",
                        "file_path": rel_p,
                        "explanation": "Private keys must never be committed to repositories or bundled in deployment archives.",
                        "recommendation": "Remove private key files immediately and revoke any keys that were uploaded.",
                        "penalty": 25,
                    })

        # 4. Content regex scanning for secrets across text files
        skip_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
            ".pdf", ".zip", ".tar", ".gz", ".7z", ".mp4", ".mp3",
            ".woff", ".woff2", ".ttf", ".eot", ".lock", ".lockb"
        }

        # Avoid scanning giant lockfiles for passwords to avoid false positives on package hashes
        skip_files = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock"}

        scanned_count = 0
        max_scannable_files = 300  # Cap file count to keep analysis fast and responsive

        for root, _, files in os.walk(self.root_dir):
            if scanned_count >= max_scannable_files:
                break

            for file_name in files:
                if scanned_count >= max_scannable_files:
                    break

                if file_name in skip_files:
                    continue

                _, ext = os.path.splitext(file_name)
                if ext.lower() in skip_extensions:
                    continue

                full_path = os.path.join(root, file_name)
                try:
                    if os.path.getsize(full_path) > self.max_file_size:
                        continue
                except OSError:
                    continue

                scanned_count += 1
                rel_p = os.path.relpath(full_path, self.root_dir)

                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, start=1):
                            # Skip long lines (minified code / base64)
                            if len(line) > 1000:
                                continue

                            for pattern in SECRET_PATTERNS:
                                match = pattern["regex"].search(line)
                                if match:
                                    raw_val = match.group(0)
                                    masked = mask_secret(raw_val)

                                    findings.append({
                                        "rule_id": pattern["id"],
                                        "module": "Security Configuration",
                                        "category": "Security",
                                        "title": f"Potential {pattern['name']} Exposed",
                                        "description": f"Detected potential hardcoded credential pattern in {rel_p} at line {line_num}: {masked}",
                                        "severity": pattern["severity"],
                                        "file_path": rel_p,
                                        "line_number": line_num,
                                        "masked_evidence": masked,
                                        "explanation": "Static credentials in code can be compromised by unauthorized users or repository leaks.",
                                        "recommendation": "Extract the credential into an external environment variable and reference it via process.env or os.getenv().",
                                        "scanner": "static_rule_engine",
                                        "confidence": "HIGH",
                                        "penalty": pattern["penalty"],
                                    })
                                    # Report at most 1 finding of same pattern per file
                                    break
                except Exception:
                    continue

        # External scanner integrations (Gitleaks and Trivy Secret Scan)
        findings.extend(self._run_gitleaks())
        findings.extend(self._run_trivy_security())

        # Normalize format
        for f in findings:
            if "category" not in f:
                f["category"] = "Security"
            if "scanner" not in f:
                f["scanner"] = "static_rule_engine"
            if "confidence" not in f:
                f["confidence"] = "HIGH"

        return findings

    def _run_gitleaks(self) -> List[Dict[str, Any]]:
        findings = []
        if not is_tool_available("gitleaks"):
            return findings

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as report_file:
            report_path = report_file.name

        try:
            res = run_command_safely(
                ["gitleaks", "detect", "--source", self.root_dir, "--no-git", "--report-format", "json", "--report-path", report_path],
                timeout=25,
            )
            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                with open(report_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                for item in data[:10]:
                    secret_val = item.get("Secret", "")
                    masked = mask_secret(secret_val)
                    findings.append({
                        "rule_id": f"GITLEAKS-{item.get('RuleID', 'SECRET')}",
                        "module": "Security Configuration",
                        "category": "Security",
                        "title": f"Gitleaks: {item.get('Description', 'Exposed Secret')}",
                        "description": f"Gitleaks detected secret matching rule '{item.get('RuleID')}' in {item.get('File')}: {masked}",
                        "severity": "Critical",
                        "file_path": os.path.relpath(item.get("File", "file"), self.root_dir),
                        "line_number": item.get("StartLine"),
                        "masked_evidence": masked,
                        "explanation": f"Gitleaks identified hardcoded secret pattern {item.get('RuleID')}.",
                        "recommendation": "Remove credential immediately, revoke leaked keys, and store secrets in environment variables.",
                        "scanner": "gitleaks",
                        "confidence": "HIGH",
                        "penalty": 25,
                    })
        except Exception:
            pass
        finally:
            if os.path.exists(report_path):
                try:
                    os.remove(report_path)
                except OSError:
                    pass

        return findings

    def _run_trivy_security(self) -> List[Dict[str, Any]]:
        findings = []
        if not is_tool_available("trivy"):
            return findings

        res = run_command_safely(
            ["trivy", "fs", "--format", "json", "--security-checks", "config,secret", self.root_dir],
            timeout=25,
        )
        if res.get("success") and res.get("stdout"):
            try:
                data = json.loads(res["stdout"])
                for r in data.get("Results", []):
                    target = r.get("Target", "file")
                    rel_target = os.path.relpath(target, self.root_dir) if os.path.isabs(target) else target
                    for sec in r.get("Secrets", [])[:5]:
                        findings.append({
                            "rule_id": f"TRIVY-SEC-{sec.get('RuleID', 'SECRET')}",
                            "module": "Security Configuration",
                            "category": "Security",
                            "title": f"Trivy Secret: {sec.get('Title', 'Hardcoded Secret')}",
                            "description": f"Trivy found secret in {rel_target} at line {sec.get('StartLine')}.",
                            "severity": "Critical",
                            "file_path": rel_target,
                            "line_number": sec.get("StartLine"),
                            "masked_evidence": mask_secret(sec.get("Match", "secret")),
                            "explanation": "Trivy secrets scanner identified an exposed credential.",
                            "recommendation": "Revoke and remove secret from source files.",
                            "scanner": "trivy",
                            "confidence": "HIGH",
                            "penalty": 25,
                        })
            except Exception:
                pass

        return findings
