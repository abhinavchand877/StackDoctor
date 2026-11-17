import os
import json
import yaml
from typing import List, Dict, Any
from app.analyzers.scanner_runner import is_tool_available, run_command_safely

class GitHubActionsAnalyzer:
    """
    Module 4: Statically inspects GitHub Actions CI/CD workflows, trigger configurations, automated test steps, and builds.
    Integrates zizmor when installed.
    """

    def __init__(self, root_dir: str, detected_info: Dict[str, Any]):
        self.root_dir = root_dir
        self.detected_info = detected_info
        self.technologies = detected_info.get("technologies", [])

    def analyze(self) -> List[Dict[str, Any]]:
        findings = []
        workflows_dir = os.path.join(self.root_dir, ".github", "workflows")

        # 1. Check directory presence
        if not os.path.isdir(workflows_dir):
            findings.append({
                "rule_id": "GHA-001",
                "module": "GitHub Actions",
                "category": "CI/CD",
                "title": "Missing CI/CD Workflow Directory",
                "description": "No '.github/workflows/' directory found in the repository.",
                "severity": "Medium",
                "file_path": ".github/workflows/",
                "explanation": "Continuous Integration/Continuous Deployment (CI/CD) pipelines automate testing, linting, and build verification upon code changes.",
                "recommendation": "Create a '.github/workflows/ci.yml' workflow to automate tests on push and pull requests.",
                "scanner": "static_rule_engine",
                "confidence": "HIGH",
                "penalty": 8,
            })
            return findings

        # 2. Check workflow files
        workflow_files = [
            f for f in os.listdir(workflows_dir)
            if f.endswith((".yml", ".yaml")) and os.path.isfile(os.path.join(workflows_dir, f))
        ]

        if not workflow_files:
            findings.append({
                "rule_id": "GHA-002",
                "module": "GitHub Actions",
                "category": "CI/CD",
                "title": "Empty Workflows Directory",
                "description": "The '.github/workflows/' directory exists but contains no YAML workflow files.",
                "severity": "Medium",
                "file_path": ".github/workflows/",
                "explanation": "No automated pipelines are actively configured.",
                "recommendation": "Add a valid GitHub Actions workflow file (e.g. 'ci.yml').",
                "scanner": "static_rule_engine",
                "confidence": "HIGH",
                "penalty": 8,
            })
            return findings

        # Track aggregate workflow capabilities across all workflow files
        has_push_trigger = False
        has_pr_trigger = False
        has_test_step = False
        has_install_step = False
        has_docker_step = False
        has_deploy_step = False

        for wf in workflow_files:
            wf_path = os.path.join(workflows_dir, wf)
            rel_path = os.path.relpath(wf_path, self.root_dir)

            try:
                with open(wf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = yaml.safe_load(f)

                if not isinstance(content, dict):
                    findings.append({
                        "rule_id": "GHA-003",
                        "module": "GitHub Actions",
                        "category": "CI/CD",
                        "title": f"Malformed Workflow File ({wf})",
                        "description": f"Workflow '{rel_path}' does not contain a valid YAML dictionary.",
                        "severity": "High",
                        "file_path": rel_path,
                        "explanation": "GitHub Actions expects top-level mappings for triggers and jobs.",
                        "recommendation": "Review workflow structure to ensure valid root-level keys.",
                        "scanner": "static_rule_engine",
                        "confidence": "HIGH",
                        "penalty": 15,
                    })
                    continue

                # Check top-level permissions
                perms = content.get("permissions")
                if perms == "write-all":
                    findings.append({
                        "rule_id": "GHA-009",
                        "module": "GitHub Actions",
                        "category": "CI/CD",
                        "title": f"Excessive Workflow Permissions in '{wf}'",
                        "description": "Workflow grants 'permissions: write-all' globally, violating the principle of least privilege.",
                        "severity": "High",
                        "file_path": rel_path,
                        "explanation": "Overly broad workflow permissions expose the repository to supply-chain attacks if third-party actions are compromised.",
                        "recommendation": "Restrict permissions to 'contents: read' or define specific job-level permissions.",
                        "scanner": "static_rule_engine",
                        "confidence": "HIGH",
                        "penalty": 15,
                    })

                # Safely retrieve triggers ('on' key can be parsed as boolean True in PyYAML)
                triggers = content.get("on")
                if triggers is None and True in content:
                    triggers = content[True]

                # Inspect triggers
                if isinstance(triggers, str):
                    if triggers == "push":
                        has_push_trigger = True
                    elif triggers == "pull_request":
                        has_pr_trigger = True
                    elif triggers == "pull_request_target":
                        findings.append({
                            "rule_id": "GHA-011",
                            "module": "GitHub Actions",
                            "category": "CI/CD",
                            "title": f"Potentially Unsafe pull_request_target in '{wf}'",
                            "description": "Workflow triggers on 'pull_request_target', which runs with write permissions and secret access in the target repository context.",
                            "severity": "Medium",
                            "file_path": rel_path,
                            "explanation": "Checking out untrusted pull request code with 'pull_request_target' can allow hostile contributors to exfiltrate secrets.",
                            "recommendation": "Use 'pull_request' instead unless privileged write access is strictly required.",
                            "scanner": "static_rule_engine",
                            "confidence": "HIGH",
                            "penalty": 8,
                        })
                elif isinstance(triggers, list):
                    if "push" in triggers:
                        has_push_trigger = True
                    if "pull_request" in triggers:
                        has_pr_trigger = True
                elif isinstance(triggers, dict):
                    if "push" in triggers:
                        has_push_trigger = True
                    if "pull_request" in triggers:
                        has_pr_trigger = True
                    if "pull_request_target" in triggers:
                        findings.append({
                            "rule_id": "GHA-011",
                            "module": "GitHub Actions",
                            "category": "CI/CD",
                            "title": f"Potentially Unsafe pull_request_target in '{wf}'",
                            "description": "Workflow triggers on 'pull_request_target', which runs with write permissions and secret access.",
                            "severity": "Medium",
                            "file_path": rel_path,
                            "explanation": "Checking out untrusted code with pull_request_target exposes repository secrets to attacker PRs.",
                            "recommendation": "Use standard 'pull_request' trigger for untrusted workflows.",
                            "scanner": "static_rule_engine",
                            "confidence": "HIGH",
                            "penalty": 8,
                        })

                # Inspect jobs
                jobs = content.get("jobs", {})
                if not jobs or not isinstance(jobs, dict):
                    findings.append({
                        "rule_id": "GHA-004",
                        "module": "GitHub Actions",
                        "category": "CI/CD",
                        "title": f"No Jobs Defined in Workflow ({wf})",
                        "description": f"Workflow '{rel_path}' does not define any executable jobs.",
                        "severity": "High",
                        "file_path": rel_path,
                        "explanation": "Workflows require one or more jobs under 'jobs:' to run actions.",
                        "recommendation": "Define test, build, or deployment jobs in the workflow.",
                        "scanner": "static_rule_engine",
                        "confidence": "HIGH",
                        "penalty": 15,
                    })
                    continue

                # Inspect steps inside jobs
                for jname, jdef in jobs.items():
                    if not isinstance(jdef, dict):
                        continue

                    steps = jdef.get("steps", [])
                    if not isinstance(steps, list):
                        continue

                    for step in steps:
                        if not isinstance(step, dict):
                            continue

                        step_name = str(step.get("name", "")).lower()
                        run_cmd = str(step.get("run", "")).lower()
                        uses_action = str(step.get("uses", "")).lower()

                        combined = f"{step_name} {run_cmd} {uses_action}"

                        # Check secret echo
                        if "echo " in run_cmd and ("${{ secrets." in run_cmd or "${{secrets." in run_cmd):
                            findings.append({
                                "rule_id": "GHA-012",
                                "module": "GitHub Actions",
                                "category": "CI/CD",
                                "title": f"Potential Secret Exposure in Step '{step.get('name', 'step')}'",
                                "description": "Workflow contains an echo command referencing repository secrets, risking secret exposure in build logs.",
                                "severity": "High",
                                "file_path": rel_path,
                                "explanation": "Printing secret expressions to standard output can leak credentials into public CI/CD execution logs.",
                                "recommendation": "Never echo secret tokens or variables in shell run steps.",
                                "scanner": "static_rule_engine",
                                "confidence": "HIGH",
                                "penalty": 15,
                            })

                        # Check unpinned third-party actions
                        if uses_action and not uses_action.startswith("docker://") and not uses_action.startswith("./"):
                            if "@master" in uses_action or "@main" in uses_action:
                                findings.append({
                                    "rule_id": "GHA-010",
                                    "module": "GitHub Actions",
                                    "category": "CI/CD",
                                    "title": f"Unpinned Third-Party Action: '{step.get('uses')}'",
                                    "description": f"Action '{step.get('uses')}' is referenced via mutable branch name (@main or @master).",
                                    "severity": "Medium",
                                    "file_path": rel_path,
                                    "explanation": "Referencing mutable branches allows upstream action changes to execute without approval.",
                                    "recommendation": "Pin third-party GitHub Actions to a full commit SHA or tagged version release.",
                                    "scanner": "static_rule_engine",
                                    "confidence": "HIGH",
                                    "penalty": 8,
                                })

                        # Check install
                        if any(k in combined for k in ["pip install", "npm install", "npm ci", "yarn install", "pnpm install", "poetry install"]):
                            has_install_step = True

                        # Check test
                        if any(k in combined for k in ["pytest", "npm test", "vitest", "jest", "unittest", "go test", "cargo test", "mvn test"]):
                            has_test_step = True

                        # Check docker
                        if any(k in combined for k in ["docker build", "docker/build-push-action", "docker compose", "docker-compose"]):
                            has_docker_step = True

                        # Check deployment
                        if any(k in combined for k in ["deploy", "ssh-action", "aws s3 sync", "kubectl apply", "publish"]):
                            has_deploy_step = True

            except yaml.YAMLError as e:
                findings.append({
                    "rule_id": "GHA-005",
                    "module": "GitHub Actions",
                    "category": "CI/CD",
                    "title": f"YAML Syntax Error in Workflow ({wf})",
                    "description": f"Encountered YAML syntax error in '{rel_path}': {str(e)}",
                    "severity": "Critical",
                    "file_path": rel_path,
                    "explanation": "Syntax errors prevent GitHub Actions from loading and executing the workflow.",
                    "recommendation": "Fix indentation and YAML formatting.",
                    "scanner": "static_rule_engine",
                    "confidence": "HIGH",
                    "penalty": 25,
                })

        # Evaluate overall CI/CD health across workflows
        if not has_push_trigger and not has_pr_trigger:
            findings.append({
                "rule_id": "GHA-006",
                "module": "GitHub Actions",
                "category": "CI/CD",
                "title": "Missing Push/Pull Request CI Triggers",
                "description": "None of the discovered workflows are configured to trigger on 'push' or 'pull_request' events.",
                "severity": "Medium",
                "file_path": ".github/workflows/",
                "explanation": "Workflows should automatically validate commits and PRs to catch defects before code is merged.",
                "recommendation": "Configure 'on: [push, pull_request]' in your workflow configuration.",
                "scanner": "static_rule_engine",
                "confidence": "HIGH",
                "penalty": 8,
            })

        if not has_test_step:
            findings.append({
                "rule_id": "GHA-007",
                "module": "GitHub Actions",
                "category": "CI/CD",
                "title": "Missing Automated Testing in CI Pipeline",
                "description": "Workflows are defined, but no automated testing steps (pytest, npm test, vitest) were detected.",
                "severity": "High",
                "file_path": ".github/workflows/",
                "explanation": "Running automated tests in CI is fundamental to catching regressions early.",
                "recommendation": "Add a test execution step (e.g. 'run: pytest' or 'run: npm test') to the pipeline.",
                "scanner": "static_rule_engine",
                "confidence": "HIGH",
                "penalty": 15,
            })

        if not has_deploy_step:
            findings.append({
                "rule_id": "GHA-008",
                "module": "GitHub Actions",
                "category": "CI/CD",
                "title": "Deployment Automation Not Configured",
                "description": "No deployment steps or release jobs were detected in GitHub Actions workflows.",
                "severity": "Informational",
                "file_path": ".github/workflows/",
                "explanation": "Automated deployment is optional but recommended for continuous delivery readiness.",
                "recommendation": "Configure a deployment job gated on successful tests and main branch merges.",
                "scanner": "static_rule_engine",
                "confidence": "HIGH",
                "penalty": 0,
            })

        # Zizmor integration
        findings.extend(self._run_zizmor(workflows_dir))

        # Normalize format
        for f in findings:
            if "category" not in f:
                f["category"] = "CI/CD"
            if "scanner" not in f:
                f["scanner"] = "static_rule_engine"
            if "confidence" not in f:
                f["confidence"] = "HIGH"

        return findings

    def _run_zizmor(self, workflows_dir: str) -> List[Dict[str, Any]]:
        findings = []
        if not is_tool_available("zizmor"):
            return findings

        res = run_command_safely(["zizmor", "--format", "json", workflows_dir], timeout=15)
        if res.get("success") and res.get("stdout"):
            try:
                data = json.loads(res["stdout"])
                for item in data.get("findings", [])[:8]:
                    rule = item.get("rule", {})
                    findings.append({
                        "rule_id": f"ZIZMOR-{rule.get('id', 'AUDIT')}",
                        "module": "GitHub Actions",
                        "category": "CI/CD",
                        "title": f"Zizmor: {rule.get('name', 'Workflow Security Issue')}",
                        "description": item.get("message", "Zizmor detected a CI/CD security vulnerability."),
                        "severity": "High" if item.get("severity") == "error" else "Medium",
                        "file_path": os.path.relpath(item.get("location", {}).get("path", ".github/workflows/"), self.root_dir),
                        "line_number": item.get("location", {}).get("line"),
                        "explanation": f"Zizmor rule {rule.get('id')} flagged security risk.",
                        "recommendation": "Follow GitHub Actions security hardening guidelines.",
                        "scanner": "zizmor",
                        "confidence": "HIGH",
                        "penalty": 15 if item.get("severity") == "error" else 8,
                    })
            except Exception:
                pass
        return findings

