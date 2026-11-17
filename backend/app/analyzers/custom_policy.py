import os
import yaml
from typing import List, Dict, Any

class CustomPolicyEvaluator:
    """
    Evaluates project-level custom security and compliance policies defined in .stackdoctor.yml.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def evaluate(self) -> List[Dict[str, Any]]:
        findings = []
        policy_file = os.path.join(self.root_dir, ".stackdoctor.yml")
        if not os.path.exists(policy_file):
            policy_file = os.path.join(self.root_dir, ".stackdoctor.yaml")
            if not os.path.exists(policy_file):
                return findings

        try:
            with open(policy_file, "r", encoding="utf-8", errors="ignore") as f:
                policy = yaml.safe_load(f)

            if not isinstance(policy, dict):
                return findings

            rules = policy.get("policies", {})

            # 1. Required files policy
            required_files = rules.get("required_files", [])
            for rf in required_files:
                if not os.path.exists(os.path.join(self.root_dir, rf)):
                    findings.append({
                        "rule_id": f"POL-REQ-{rf.replace('.', '_')}",
                        "module": "Project Structure",
                        "category": "Project Structure",
                        "title": f"Custom Policy Violation: Missing Required File ({rf})",
                        "description": f"Repository does not contain mandatory file '{rf}' specified by .stackdoctor.yml policy.",
                        "severity": "Medium",
                        "file_path": rf,
                        "explanation": f"The organization or project governance policy requires '{rf}'.",
                        "recommendation": f"Create and commit '{rf}' to satisfy compliance rules.",
                        "scanner": "custom_policy_engine",
                        "confidence": "HIGH",
                        "penalty": 8,
                    })

            # 2. Forbidden packages policy
            forbidden_pkgs = rules.get("forbidden_packages", [])
            if forbidden_pkgs:
                # Check requirements.txt
                req_path = os.path.join(self.root_dir, "requirements.txt")
                if os.path.exists(req_path):
                    with open(req_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().lower()
                    for fpkg in forbidden_pkgs:
                        if fpkg.lower() in content:
                            findings.append({
                                "rule_id": f"POL-FORBIDDEN-{fpkg}",
                                "module": "Dependency Analysis",
                                "category": "Dependencies",
                                "title": f"Custom Policy Violation: Forbidden Package '{fpkg}'",
                                "description": f"Found blacklisted package '{fpkg}' declared in requirements.txt.",
                                "severity": "High",
                                "file_path": "requirements.txt",
                                "explanation": f"Package '{fpkg}' is prohibited by project policy due to known security risks.",
                                "recommendation": f"Remove '{fpkg}' and migrate to an approved alternative.",
                                "scanner": "custom_policy_engine",
                                "confidence": "HIGH",
                                "penalty": 15,
                            })

        except Exception:
            pass

        return findings
