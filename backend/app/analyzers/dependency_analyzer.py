import os
import re
import json
from typing import List, Dict, Any
from packaging.requirements import Requirement, InvalidRequirement
from app.analyzers.scanner_runner import is_tool_available, run_command_safely

class DependencyAnalyzer:
    """
    Module 2: Statically inspects dependency manifests, version pinning, lockfile presence, and syntax.
    Optionally integrates Trivy and OSV-Scanner for CVE discovery when installed.
    """

    def __init__(self, root_dir: str, detected_info: Dict[str, Any]):
        self.root_dir = root_dir
        self.detected_info = detected_info
        self.technologies = detected_info.get("technologies", [])

    def analyze(self) -> List[Dict[str, Any]]:
        findings = []

        if "Python" in self.technologies:
            findings.extend(self._analyze_python_dependencies())

        if "Node.js" in self.technologies or "React" in self.technologies:
            findings.extend(self._analyze_node_dependencies())

        if "Java" in self.technologies:
            findings.extend(self._analyze_java_dependencies())

        if "PHP" in self.technologies:
            findings.extend(self._analyze_php_dependencies())

        if "Go" in self.technologies:
            findings.extend(self._analyze_go_dependencies())

        # External scanner integrations (Trivy / OSV-Scanner)
        findings.extend(self._run_external_scanners())

        # Normalize finding format
        for f in findings:
            if "category" not in f:
                f["category"] = "Dependencies"
            if "scanner" not in f:
                f["scanner"] = "static_rule_engine"
            if "confidence" not in f:
                f["confidence"] = "HIGH"

        return findings

    def _run_external_scanners(self) -> List[Dict[str, Any]]:
        findings = []

        # 1. Trivy vulnerability scanner
        if is_tool_available("trivy"):
            res = run_command_safely(
                ["trivy", "fs", "--format", "json", "--security-checks", "vuln", self.root_dir],
                timeout=25,
            )
            if res.get("success") and res.get("stdout"):
                try:
                    data = json.loads(res["stdout"])
                    results = data.get("Results", [])
                    for r in results:
                        target = r.get("Target", "manifest")
                        rel_target = os.path.relpath(target, self.root_dir) if os.path.isabs(target) else target
                        for vuln in r.get("Vulnerabilities", [])[:10]:
                            severity_map = {"CRITICAL": "Critical", "HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}
                            sev = severity_map.get(vuln.get("Severity", "MEDIUM").upper(), "Medium")
                            findings.append({
                                "rule_id": f"TRIVY-{vuln.get('VulnerabilityID', 'CVE')}",
                                "module": "Dependency Analysis",
                                "category": "Dependencies",
                                "title": f"Known Vulnerability: {vuln.get('PkgName')} ({vuln.get('VulnerabilityID')})",
                                "description": vuln.get("Title") or vuln.get("Description", "Known security vulnerability detected in package."),
                                "severity": sev,
                                "file_path": rel_target,
                                "explanation": f"Package {vuln.get('PkgName')}@{vuln.get('InstalledVersion')} is vulnerable to {vuln.get('VulnerabilityID')}.",
                                "recommendation": f"Upgrade {vuln.get('PkgName')} to version {vuln.get('FixedVersion', 'latest patched version')}.",
                                "scanner": "trivy",
                                "confidence": "HIGH",
                                "penalty": 25 if sev == "Critical" else (15 if sev == "High" else 8),
                            })
                except Exception:
                    pass

        # 2. OSV-Scanner
        if is_tool_available("osv-scanner"):
            res = run_command_safely(
                ["osv-scanner", "--json", "-r", self.root_dir],
                timeout=25,
            )
            if res.get("success") and res.get("stdout"):
                try:
                    data = json.loads(res["stdout"])
                    for result_item in data.get("results", []):
                        package_source = result_item.get("packageSource", {})
                        source_path = package_source.get("path", "manifest")
                        rel_source = os.path.relpath(source_path, self.root_dir) if os.path.isabs(source_path) else source_path
                        for pkg in result_item.get("packages", [])[:10]:
                            for vuln in pkg.get("vulnerabilities", [])[:5]:
                                findings.append({
                                    "rule_id": f"OSV-{vuln.get('id', 'CVE')}",
                                    "module": "Dependency Analysis",
                                    "category": "Dependencies",
                                    "title": f"OSV Advisory: {pkg.get('package', {}).get('name')} ({vuln.get('id')})",
                                    "description": vuln.get("summary") or "Known vulnerability reported by OSV database.",
                                    "severity": "High",
                                    "file_path": rel_source,
                                    "explanation": f"Package {pkg.get('package', {}).get('name')} matches OSV vulnerability advisory {vuln.get('id')}.",
                                    "recommendation": "Update package to the latest secure release.",
                                    "scanner": "osv-scanner",
                                    "confidence": "HIGH",
                                    "penalty": 15,
                                })
                except Exception:
                    pass

        return findings

    def _analyze_java_dependencies(self) -> List[Dict[str, Any]]:
        findings = []
        pom_path = os.path.join(self.root_dir, "pom.xml")
        gradle_path = os.path.join(self.root_dir, "build.gradle")

        if os.path.exists(pom_path):
            try:
                with open(pom_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                # Check for dynamic or latest versions in pom.xml (e.g., LATEST, RELEASE)
                if "<version>LATEST</version>" in content or "<version>RELEASE</version>" in content:
                    findings.append({
                        "rule_id": "DEP-010",
                        "module": "Dependency Analysis",
                        "category": "Dependencies",
                        "title": "Dynamic Versioning in Maven pom.xml",
                        "description": "Maven pom.xml contains dynamic version keywords ('LATEST' or 'RELEASE').",
                        "severity": "High",
                        "file_path": "pom.xml",
                        "explanation": "Using LATEST or RELEASE in Maven dependencies breaks build reproducibility and allows unvetted code into production builds.",
                        "recommendation": "Replace dynamic versions with explicit, pinned release versions.",
                        "penalty": 15,
                    })
            except Exception:
                pass

        if os.path.exists(gradle_path):
            try:
                with open(gradle_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                if "+'" in content or '+"' in content or "latest.release" in content:
                    findings.append({
                        "rule_id": "DEP-011",
                        "module": "Dependency Analysis",
                        "category": "Dependencies",
                        "title": "Dynamic Versioning in Gradle build.gradle",
                        "description": "Gradle build file specifies dynamic dependency versions using '+' or 'latest.release'.",
                        "severity": "High",
                        "file_path": "build.gradle",
                        "explanation": "Dynamic versioning in Gradle causes non-deterministic builds and makes tracking vulnerability regressions difficult.",
                        "recommendation": "Pin specific version numbers for all Gradle dependencies.",
                        "penalty": 15,
                    })
            except Exception:
                pass

        return findings

    def _analyze_php_dependencies(self) -> List[Dict[str, Any]]:
        findings = []
        composer_path = os.path.join(self.root_dir, "composer.json")
        lock_path = os.path.join(self.root_dir, "composer.lock")

        if os.path.exists(composer_path):
            try:
                with open(composer_path, "r", encoding="utf-8", errors="ignore") as f:
                    data = json.load(f)
                require = data.get("require", {})
                wildcards = [pkg for pkg, ver in require.items() if str(ver).strip() in ("*", "dev-master", "latest")]
                if wildcards:
                    findings.append({
                        "rule_id": "DEP-012",
                        "module": "Dependency Analysis",
                        "category": "Dependencies",
                        "title": "Wildcard PHP Dependency Versions in composer.json",
                        "description": f"Detected wildcard or branch versioning for: {', '.join(wildcards[:3])}.",
                        "severity": "High",
                        "file_path": "composer.json",
                        "explanation": "Wildcards in composer.json pull breaking changes automatically without version constraints.",
                        "recommendation": "Specify semver constraints (e.g. ^8.1 or ~2.0) in composer.json.",
                        "penalty": 15,
                    })

                if require and not os.path.exists(lock_path):
                    findings.append({
                        "rule_id": "DEP-013",
                        "module": "Dependency Analysis",
                        "category": "Dependencies",
                        "title": "Missing PHP composer.lock File",
                        "description": "composer.json defines packages, but no composer.lock file is committed.",
                        "severity": "Medium",
                        "file_path": "composer.lock",
                        "explanation": "Without composer.lock, composer install will recalculate versions, leading to inconsistent environments.",
                        "recommendation": "Run 'composer update' and commit the resulting composer.lock file.",
                        "penalty": 8,
                    })
            except Exception:
                pass

        return findings

    def _analyze_go_dependencies(self) -> List[Dict[str, Any]]:
        findings = []
        mod_path = os.path.join(self.root_dir, "go.mod")
        sum_path = os.path.join(self.root_dir, "go.sum")

        if os.path.exists(mod_path):
            try:
                with open(mod_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Check if go.mod has require blocks but go.sum is missing
                if "require" in content and not os.path.exists(sum_path):
                    findings.append({
                        "rule_id": "DEP-014",
                        "module": "Dependency Analysis",
                        "category": "Dependencies",
                        "title": "Missing Go Checksum Database (go.sum)",
                        "description": "go.mod defines external dependencies, but go.sum checksum file is missing.",
                        "severity": "High",
                        "file_path": "go.sum",
                        "explanation": "go.sum contains cryptographic checksums for dependencies to guarantee tamper-proof module downloads.",
                        "recommendation": "Run 'go mod tidy' to generate and commit go.sum.",
                        "penalty": 15,
                    })
            except Exception:
                pass

        return findings

    def _analyze_python_dependencies(self) -> List[Dict[str, Any]]:
        findings = []
        req_path = os.path.join(self.root_dir, "requirements.txt")
        pyproject_path = os.path.join(self.root_dir, "pyproject.toml")

        # 1. Parse requirements.txt
        if os.path.exists(req_path):
            unpinned_packages = []
            invalid_lines = []
            valid_count = 0

            try:
                with open(req_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, start=1):
                        cleaned = line.strip()
                        # Ignore comments and empty lines
                        if not cleaned or cleaned.startswith("#") or cleaned.startswith("-r") or cleaned.startswith("-i"):
                            continue

                        try:
                            # Parse requirement specifier
                            req = Requirement(cleaned)
                            valid_count += 1
                            # Check if specifier is pinned (e.g. ==)
                            has_pin = False
                            for spec in req.specifier:
                                if spec.operator == "==":
                                    has_pin = True
                                    break
                            if not has_pin:
                                unpinned_packages.append((req.name, line_num))
                        except InvalidRequirement:
                            invalid_lines.append((cleaned, line_num))

                if invalid_lines:
                    first_bad, bad_line = invalid_lines[0]
                    findings.append({
                        "rule_id": "DEP-001",
                        "module": "Dependency Analysis",
                        "title": "Invalid Python Dependency Specification",
                        "description": f"Encountered {len(invalid_lines)} malformed dependency specification(s) in requirements.txt (e.g., line {bad_line}: '{first_bad}').",
                        "severity": "High",
                        "file_path": "requirements.txt",
                        "explanation": "Invalid syntax in requirements.txt will break pip installations during container builds and CI steps.",
                        "recommendation": "Correct invalid requirement lines following PEP 508 standards (e.g. 'package==1.2.3').",
                        "penalty": 15,
                    })

                if unpinned_packages:
                    sample = ", ".join(pkg for pkg, _ in unpinned_packages[:4])
                    more = f" and {len(unpinned_packages) - 4} more" if len(unpinned_packages) > 4 else ""
                    findings.append({
                        "rule_id": "DEP-002",
                        "module": "Dependency Analysis",
                        "title": "Unpinned Python Dependencies Detected",
                        "description": f"{len(unpinned_packages)} Python package(s) lack strict version pinning ({sample}{more}).",
                        "severity": "Medium",
                        "file_path": "requirements.txt",
                        "explanation": "Unpinned dependencies allow unpredictable upstream updates, which frequently lead to unexpected breaking changes and deployment failures.",
                        "recommendation": "Pin dependencies with exact versions (e.g., 'flask==3.0.3') or utilize pip-tools / poetry to generate reproducible requirements.",
                        "penalty": 8,
                    })

                if valid_count == 0 and not invalid_lines:
                    findings.append({
                        "rule_id": "DEP-003",
                        "module": "Dependency Analysis",
                        "title": "Empty Python Requirements File",
                        "description": "requirements.txt exists but does not specify any dependencies.",
                        "severity": "Low",
                        "file_path": "requirements.txt",
                        "explanation": "If the project relies on external libraries, they should be listed to enable automated environments.",
                        "recommendation": "List necessary dependencies in requirements.txt or remove the empty file if the project is standard library only.",
                        "penalty": 3,
                    })

            except Exception as e:
                findings.append({
                    "rule_id": "DEP-004",
                    "module": "Dependency Analysis",
                    "title": "Error Reading requirements.txt",
                    "description": f"Failed to read requirements.txt: {str(e)}",
                    "severity": "Medium",
                    "file_path": "requirements.txt",
                    "explanation": "The file could not be parsed as standard text.",
                    "recommendation": "Ensure requirements.txt is saved with UTF-8 encoding.",
                    "penalty": 8,
                })

        # 2. Check pyproject.toml if present
        if os.path.exists(pyproject_path):
            try:
                with open(pyproject_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    # Basic check for poetry/flit/setuptools dependency sections
                    if "dependencies" not in content and "[project]" not in content and "[tool.poetry]" not in content:
                        findings.append({
                            "rule_id": "DEP-005",
                            "module": "Dependency Analysis",
                            "title": "Incomplete pyproject.toml Configuration",
                            "description": "pyproject.toml exists but does not define project build or dependency tables.",
                            "severity": "Low",
                            "file_path": "pyproject.toml",
                            "explanation": "Standard pyproject.toml files specify [project] metadata or build-system specifications according to PEP 621.",
                            "recommendation": "Declare dependencies under [project.dependencies] or configure build backend.",
                            "penalty": 3,
                        })
            except Exception:
                pass

        return findings

    def _analyze_node_dependencies(self) -> List[Dict[str, Any]]:
        findings = []
        pkg_path = os.path.join(self.root_dir, "package.json")

        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, "r", encoding="utf-8", errors="ignore") as f:
                    pkg_data = json.load(f)

                dependencies = pkg_data.get("dependencies", {})
                dev_dependencies = pkg_data.get("devDependencies", {})
                all_deps = {**dependencies, **dev_dependencies}

                wildcard_deps = []
                for dep, ver in all_deps.items():
                    ver_str = str(ver).strip()
                    if ver_str in ["*", "latest", ""]:
                        wildcard_deps.append((dep, ver_str))

                if wildcard_deps:
                    sample = ", ".join(f"{d} ({v})" for d, v in wildcard_deps[:3])
                    findings.append({
                        "rule_id": "DEP-006",
                        "module": "Dependency Analysis",
                        "title": "Wildcard or 'latest' Node Dependency Versions",
                        "description": f"Detected {len(wildcard_deps)} dependency/dependencies declared with wildcard or 'latest' versioning ({sample}).",
                        "severity": "High",
                        "file_path": "package.json",
                        "explanation": "Using wildcard '*' or 'latest' causes automatic downloads of untested major versions that may contain breaking changes or regressions.",
                        "recommendation": "Specify a semver range (e.g. ^18.2.0) or pin exact versions in package.json.",
                        "penalty": 15,
                    })

                # Check lockfile presence
                lockfiles = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"]
                has_lockfile = any(os.path.exists(os.path.join(self.root_dir, lock)) for lock in lockfiles)

                if all_deps and not has_lockfile:
                    findings.append({
                        "rule_id": "DEP-007",
                        "module": "Dependency Analysis",
                        "title": "Missing Package Lockfile",
                        "description": "Dependencies are declared in package.json, but no lockfile (package-lock.json, yarn.lock, or pnpm-lock.yaml) is present.",
                        "severity": "Medium",
                        "file_path": "package-lock.json",
                        "explanation": "A lockfile guarantees deterministic, reproducible installations across developer machines, Docker containers, and CI environments.",
                        "recommendation": "Commit your package-lock.json, yarn.lock, or pnpm-lock.yaml into version control.",
                        "penalty": 8,
                    })

            except json.JSONDecodeError as e:
                findings.append({
                    "rule_id": "DEP-008",
                    "module": "Dependency Analysis",
                    "title": "Invalid package.json Syntax",
                    "description": f"Failed to parse package.json due to a JSON syntax error: {str(e)}",
                    "severity": "Critical",
                    "file_path": "package.json",
                    "explanation": "A malformed package.json prevents npm/yarn commands from executing during deployment and builds.",
                    "recommendation": "Validate and fix JSON syntax errors in package.json.",
                    "penalty": 25,
                })
            except Exception as e:
                findings.append({
                    "rule_id": "DEP-009",
                    "module": "Dependency Analysis",
                    "title": "Error Reading package.json",
                    "description": f"Unexpected error reading package.json: {str(e)}",
                    "severity": "Medium",
                    "file_path": "package.json",
                    "explanation": "The file could not be read properly.",
                    "recommendation": "Ensure package.json is accessible and valid UTF-8 text.",
                    "penalty": 8,
                })

        return findings
