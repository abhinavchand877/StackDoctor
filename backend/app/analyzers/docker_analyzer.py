import os
import re
import json
import yaml
from typing import List, Dict, Any
from app.analyzers.scanner_runner import is_tool_available, run_command_safely

class DockerAnalyzer:
    """
    Module 3: Statically inspects Dockerfiles, Compose manifests, non-root user execution, and base image pinning.
    Integrates Hadolint and Checkov when available.
    """

    def __init__(self, root_dir: str, detected_info: Dict[str, Any]):
        self.root_dir = root_dir
        self.detected_info = detected_info
        self.technologies = detected_info.get("technologies", [])

    def analyze(self) -> List[Dict[str, Any]]:
        findings = []

        dockerfile_candidates = ["Dockerfile", "dockerfile", "Dockerfile.prod", "Dockerfile.dev"]
        dockerfile_paths = [os.path.join(self.root_dir, f) for f in dockerfile_candidates if os.path.exists(os.path.join(self.root_dir, f))]

        compose_candidates = ["docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"]
        compose_paths = [os.path.join(self.root_dir, f) for f in compose_candidates if os.path.exists(os.path.join(self.root_dir, f))]

        # If project has no Docker artifacts at all, provide an informational/recommendation finding
        if not dockerfile_paths and not compose_paths:
            findings.append({
                "rule_id": "DOC-001",
                "module": "Docker Configuration",
                "category": "Docker",
                "title": "Missing Containerization Configuration",
                "description": "No Dockerfile or docker-compose.yml was found in the project.",
                "severity": "Low",
                "file_path": "Dockerfile",
                "explanation": "Containerizing the application provides consistent execution across development, staging, and production environments.",
                "recommendation": "Add a Dockerfile and docker-compose.yml for standardized container deployment.",
                "scanner": "static_rule_engine",
                "confidence": "HIGH",
                "penalty": 3,
            })
            return findings

        # Check .dockerignore when Dockerfile exists
        if dockerfile_paths and not os.path.exists(os.path.join(self.root_dir, ".dockerignore")):
            findings.append({
                "rule_id": "DOC-002",
                "module": "Docker Configuration",
                "category": "Docker",
                "title": "Missing .dockerignore File",
                "description": "A Dockerfile is present, but no .dockerignore file was found in the project root.",
                "severity": "Low",
                "file_path": ".dockerignore",
                "explanation": "Without .dockerignore, local files like node_modules, .git, .env, and build caches are copied into the Docker build context, bloating image size and potentially leaking credentials.",
                "recommendation": "Create a .dockerignore file excluding .git, node_modules, .env, __pycache__, and temporary files.",
                "scanner": "static_rule_engine",
                "confidence": "HIGH",
                "penalty": 3,
            })

        # Analyze each Dockerfile found
        for df_path in dockerfile_paths:
            findings.extend(self._analyze_dockerfile(df_path))
            findings.extend(self._run_hadolint(df_path))

        # Analyze each Compose file found
        for comp_path in compose_paths:
            findings.extend(self._analyze_compose(comp_path))

        # Checkov integration
        findings.extend(self._run_checkov())

        # Normalize finding format
        for f in findings:
            if "category" not in f:
                f["category"] = "Docker"
            if "scanner" not in f:
                f["scanner"] = "static_rule_engine"
            if "confidence" not in f:
                f["confidence"] = "HIGH"

        return findings

    def _run_hadolint(self, df_path: str) -> List[Dict[str, Any]]:
        findings = []
        if not is_tool_available("hadolint"):
            return findings

        rel_path = os.path.relpath(df_path, self.root_dir)
        res = run_command_safely(["hadolint", "-f", "json", df_path], timeout=15)
        if res.get("success") and res.get("stdout"):
            try:
                items = json.loads(res["stdout"])
                sev_map = {"error": "High", "warning": "Medium", "info": "Low", "style": "Low"}
                for item in items[:8]:
                    sev = sev_map.get(item.get("level", "warning").lower(), "Medium")
                    findings.append({
                        "rule_id": f"HADOLINT-{item.get('code', 'DL')}",
                        "module": "Docker Configuration",
                        "category": "Docker",
                        "title": f"Hadolint: {item.get('code')} ({item.get('message')})",
                        "description": item.get("message", "Hadolint lint finding"),
                        "severity": sev,
                        "file_path": rel_path,
                        "line_number": item.get("line"),
                        "explanation": f"Hadolint rule {item.get('code')} flagged Dockerfile line {item.get('line')}.",
                        "recommendation": "Follow Hadolint Dockerfile best practices.",
                        "scanner": "hadolint",
                        "confidence": "HIGH",
                        "penalty": 15 if sev == "High" else 8,
                    })
            except Exception:
                pass
        return findings

    def _run_checkov(self) -> List[Dict[str, Any]]:
        findings = []
        if not is_tool_available("checkov"):
            return findings

        res = run_command_safely(
            ["checkov", "-d", self.root_dir, "--framework", "dockerfile", "--output", "json"],
            timeout=25,
        )
        if res.get("success") and res.get("stdout"):
            try:
                data = json.loads(res["stdout"])
                failed_checks = data.get("results", {}).get("failed_checks", [])
                for check in failed_checks[:8]:
                    findings.append({
                        "rule_id": f"CHECKOV-{check.get('check_id', 'CKV')}",
                        "module": "Docker Configuration",
                        "category": "Docker",
                        "title": f"Checkov: {check.get('check_name')}",
                        "description": check.get("guideline") or check.get("check_name"),
                        "severity": "Medium",
                        "file_path": os.path.relpath(check.get("file_path", "Dockerfile"), self.root_dir),
                        "line_number": check.get("file_line_range", [1])[0] if check.get("file_line_range") else None,
                        "explanation": f"Checkov policy violation {check.get('check_id')}.",
                        "recommendation": check.get("guideline") or "Remediate Dockerfile according to CIS/Checkov security guidelines.",
                        "scanner": "checkov",
                        "confidence": "HIGH",
                        "penalty": 8,
                    })
            except Exception:
                pass
        return findings

    def _analyze_dockerfile(self, file_path: str) -> List[Dict[str, Any]]:
        findings = []
        rel_path = os.path.relpath(file_path, self.root_dir)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f.readlines()]

            # Filter non-comment lines
            instructions = []
            for line in lines:
                if line and not line.startswith("#"):
                    instructions.append(line)

            has_from = False
            has_workdir = False
            has_copy = False
            has_cmd_or_entrypoint = False
            has_user = False
            uses_latest_tag = False
            latest_image_ref = ""

            for inst in instructions:
                upper = inst.upper()
                if upper.startswith("FROM "):
                    has_from = True
                    # Check for :latest tag or unversioned base image
                    parts = inst.split()
                    if len(parts) >= 2:
                        image_part = parts[1]
                        # Disallow multi-stage aliases like 'AS builder'
                        base_image = image_part.split()[0]
                        if ":latest" in base_image or (":" not in base_image and not base_image.startswith("scratch")):
                            uses_latest_tag = True
                            latest_image_ref = base_image

                elif upper.startswith("WORKDIR "):
                    has_workdir = True
                elif upper.startswith("COPY ") or upper.startswith("ADD "):
                    has_copy = True
                elif upper.startswith("CMD ") or upper.startswith("ENTRYPOINT "):
                    has_cmd_or_entrypoint = True
                elif upper.startswith("USER "):
                    has_user = True

            # 1. Missing FROM
            if not has_from:
                findings.append({
                    "rule_id": "DOC-003",
                    "module": "Docker Configuration",
                    "title": "Missing FROM Instruction in Dockerfile",
                    "description": f"Dockerfile at '{rel_path}' does not contain a valid FROM base image directive.",
                    "severity": "Critical",
                    "file_path": rel_path,
                    "explanation": "A Dockerfile must begin with a FROM instruction specifying the base image to build upon.",
                    "recommendation": "Add a valid 'FROM <image>:<tag>' directive at the start of your Dockerfile.",
                    "penalty": 25,
                })

            # 2. Base image unpinned or :latest tag
            if uses_latest_tag:
                findings.append({
                    "rule_id": "DOC-004",
                    "module": "Docker Configuration",
                    "title": "Unpinned or ':latest' Base Image Tag Used",
                    "description": f"Dockerfile references an unversioned or ':latest' base image ('{latest_image_ref}').",
                    "severity": "Medium",
                    "file_path": rel_path,
                    "explanation": "Using ':latest' creates non-reproducible builds. When upstream images receive updates, the container build may fail unexpectedly.",
                    "recommendation": "Pin base images to explicit version tags or digests (e.g., 'python:3.12-slim' or 'node:20-alpine').",
                    "penalty": 8,
                })

            # 3. Missing WORKDIR
            if not has_workdir:
                findings.append({
                    "rule_id": "DOC-005",
                    "module": "Docker Configuration",
                    "title": "Missing WORKDIR Instruction",
                    "description": f"No WORKDIR directive is defined in '{rel_path}'. Files are being placed in the container root.",
                    "severity": "Low",
                    "file_path": rel_path,
                    "explanation": "Operating in the root container directory can overwrite core system directories or cause permission conflicts.",
                    "recommendation": "Define an explicit working directory (e.g., 'WORKDIR /app') before copying code.",
                    "penalty": 3,
                })

            # 4. Missing COPY / ADD
            if not has_copy:
                findings.append({
                    "rule_id": "DOC-006",
                    "module": "Docker Configuration",
                    "title": "Missing COPY or ADD Instruction",
                    "description": f"No COPY or ADD commands found in '{rel_path}'. Application code does not appear to be transferred into the image.",
                    "severity": "High",
                    "file_path": rel_path,
                    "explanation": "Docker images require copying application manifests and source code to package the runtime.",
                    "recommendation": "Add instructions to copy requirements/manifests and application source (e.g. 'COPY . /app').",
                    "penalty": 15,
                })

            # 5. Missing CMD or ENTRYPOINT
            if not has_cmd_or_entrypoint:
                findings.append({
                    "rule_id": "DOC-007",
                    "module": "Docker Configuration",
                    "title": "Missing CMD or ENTRYPOINT Startup Command",
                    "description": f"No default startup instruction (CMD or ENTRYPOINT) is defined in '{rel_path}'.",
                    "severity": "High",
                    "file_path": rel_path,
                    "explanation": "Containers need a designated executable entry point to run as a service.",
                    "recommendation": "Specify a startup command using exec syntax, such as 'CMD [\"gunicorn\", \"--bind\", \"0.0.0.0:5000\", \"run:app\"]'.",
                    "penalty": 15,
                })

            # 6. Container running as root (absence of USER)
            if not has_user:
                findings.append({
                    "rule_id": "DOC-008",
                    "module": "Docker Configuration",
                    "title": "Container Execution as Root User (Missing USER)",
                    "description": f"No explicit non-root USER instruction configured in '{rel_path}'.",
                    "severity": "Medium",
                    "file_path": rel_path,
                    "explanation": "Running processes as container root elevates the severity of container breakout vulnerabilities and violates security best practices.",
                    "recommendation": "Create and switch to an unprivileged system user (e.g. 'RUN useradd -m appuser && USER appuser').",
                    "penalty": 8,
                })

        except Exception as e:
            findings.append({
                "rule_id": "DOC-009",
                "module": "Docker Configuration",
                "title": f"Error Inspecting Dockerfile ({rel_path})",
                "description": f"Failed to analyze Dockerfile: {str(e)}",
                "severity": "Medium",
                "file_path": rel_path,
                "explanation": "The file could not be parsed as text.",
                "recommendation": "Verify Dockerfile encoding and permissions.",
                "penalty": 8,
            })

        return findings

    def _analyze_compose(self, file_path: str) -> List[Dict[str, Any]]:
        findings = []
        rel_path = os.path.relpath(file_path, self.root_dir)

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = yaml.safe_load(f)

            if not isinstance(content, dict):
                findings.append({
                    "rule_id": "DOC-010",
                    "module": "Docker Configuration",
                    "title": f"Invalid Docker Compose Format in '{rel_path}'",
                    "description": "Compose file does not represent a valid YAML mapping.",
                    "severity": "High",
                    "file_path": rel_path,
                    "explanation": "Docker Compose expects a dictionary containing 'services' and configurations.",
                    "recommendation": "Review compose file formatting.",
                    "penalty": 15,
                })
                return findings

            services = content.get("services", {})
            if not services or not isinstance(services, dict):
                findings.append({
                    "rule_id": "DOC-011",
                    "module": "Docker Configuration",
                    "title": f"No Services Defined in Docker Compose ({rel_path})",
                    "description": "Compose file is missing a 'services' mapping or contains zero service definitions.",
                    "severity": "High",
                    "file_path": rel_path,
                    "explanation": "A Docker Compose file must define at least one service container.",
                    "recommendation": "Define your frontend, backend, or database containers under 'services:'.",
                    "penalty": 15,
                })
                return findings

            # Inspect each service
            for sname, sdef in services.items():
                if not isinstance(sdef, dict):
                    continue

                # Check build context existence
                build = sdef.get("build")
                if isinstance(build, str):
                    build_dir = os.path.join(self.root_dir, build)
                    if not os.path.exists(build_dir):
                        findings.append({
                            "rule_id": "DOC-012",
                            "module": "Docker Configuration",
                            "title": f"Non-Existent Build Context for Service '{sname}'",
                            "description": f"Service '{sname}' specifies build context '{build}', which does not exist in the project.",
                            "severity": "High",
                            "file_path": rel_path,
                            "explanation": "Docker Compose cannot build services referencing missing directory paths.",
                            "recommendation": f"Ensure the path '{build}' exists or adjust the 'build' context in {rel_path}.",
                            "penalty": 15,
                        })
                elif isinstance(build, dict):
                    context = build.get("context", ".")
                    build_dir = os.path.join(self.root_dir, context)
                    if not os.path.exists(build_dir):
                        findings.append({
                            "rule_id": "DOC-012",
                            "module": "Docker Configuration",
                            "title": f"Non-Existent Build Context for Service '{sname}'",
                            "description": f"Service '{sname}' specifies build context '{context}', which does not exist in the project.",
                            "severity": "High",
                            "file_path": rel_path,
                            "explanation": "Docker Compose cannot build services referencing missing directory paths.",
                            "recommendation": f"Ensure context path '{context}' exists in {rel_path}.",
                            "penalty": 15,
                        })

                # Check for hardcoded plaintext passwords in environment variables
                env = sdef.get("environment", {})
                env_items = []
                if isinstance(env, dict):
                    env_items = [(k, str(v)) for k, v in env.items()]
                elif isinstance(env, list):
                    for item in env:
                        if "=" in str(item):
                            k, v = str(item).split("=", 1)
                            env_items.append((k, v))

                for k, v in env_items:
                    k_upper = k.upper()
                    if any(term in k_upper for term in ["PASSWORD", "SECRET", "API_KEY", "TOKEN", "PRIVATE_KEY"]):
                        # Check if it looks like a hardcoded secret rather than ${VAR}
                        if v and not v.startswith("${") and not v.startswith("$"):
                            findings.append({
                                "rule_id": "DOC-013",
                                "module": "Docker Configuration",
                                "title": f"Hardcoded Secret in Compose Service '{sname}'",
                                "description": f"Service '{sname}' defines environment variable '{k}' with a static value.",
                                "severity": "High",
                                "file_path": rel_path,
                                "explanation": "Hardcoding credentials in docker-compose.yml exposes secrets to source control.",
                                "recommendation": f"Use environment variable interpolation (e.g., '{k}: ${{SECRET_ENV_VAR}}') instead of static credentials.",
                                "penalty": 15,
                            })
                            break

        except yaml.YAMLError as e:
            findings.append({
                "rule_id": "DOC-014",
                "module": "Docker Configuration",
                "title": f"YAML Syntax Error in Docker Compose ({rel_path})",
                "description": f"Failed to parse Compose YAML: {str(e)}",
                "severity": "Critical",
                "file_path": rel_path,
                "explanation": "Malformed YAML syntax prevents Docker Compose from parsing configurations.",
                "recommendation": "Fix YAML indentation and syntax errors.",
                "penalty": 25,
            })

        return findings
