import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from app.analyzers.scanner_runner import is_tool_available, run_command_safely
from packaging.requirements import Requirement, InvalidRequirement

def generate_sbom(root_dir: str, detected_info: Dict[str, Any], project_name: str = "project") -> Dict[str, Any]:
    """
    Generates a Software Bill of Materials (SBOM) in CycloneDX JSON format.
    Uses Syft CLI when installed, with a comprehensive static manifest-parsing fallback.
    """
    if is_tool_available("syft"):
        res = run_command_safely(["syft", root_dir, "-o", "cyclonedx-json"], timeout=25)
        if res.get("success") and res.get("stdout"):
            try:
                return json.loads(res["stdout"])
            except Exception:
                pass

    # Deterministic static CycloneDX 1.5 generator
    components = []
    technologies = detected_info.get("technologies", [])

    # 1. Parse requirements.txt for Python components
    req_path = os.path.join(root_dir, "requirements.txt")
    if os.path.exists(req_path):
        try:
            with open(req_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    cleaned = line.strip()
                    if not cleaned or cleaned.startswith("#") or cleaned.startswith("-"):
                        continue
                    try:
                        req = Requirement(cleaned)
                        version = "latest"
                        for s in req.specifier:
                            if s.operator == "==":
                                version = s.version
                                break
                        components.append({
                            "type": "library",
                            "name": req.name,
                            "version": version,
                            "purl": f"pkg:pypi/{req.name}@{version}",
                            "properties": [{"name": "ecosystem", "value": "pypi"}],
                        })
                    except InvalidRequirement:
                        pass
        except Exception:
            pass

    # 2. Parse package.json for Node.js components
    pkg_path = os.path.join(root_dir, "package.json")
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path, "r", encoding="utf-8", errors="ignore") as f:
                pkg_data = json.load(f)
            deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
            for name, ver in deps.items():
                clean_ver = str(ver).replace("^", "").replace("~", "").strip() or "latest"
                components.append({
                    "type": "library",
                    "name": name,
                    "version": clean_ver,
                    "purl": f"pkg:npm/{name}@{clean_ver}",
                    "properties": [{"name": "ecosystem", "value": "npm"}],
                })
        except Exception:
            pass

    # 3. Parse composer.json for PHP components
    comp_path = os.path.join(root_dir, "composer.json")
    if os.path.exists(comp_path):
        try:
            with open(comp_path, "r", encoding="utf-8", errors="ignore") as f:
                comp_data = json.load(f)
            reqs = comp_data.get("require", {})
            for name, ver in reqs.items():
                if name.lower() != "php":
                    clean_ver = str(ver).replace("^", "").replace("~", "").strip() or "latest"
                    components.append({
                        "type": "library",
                        "name": name,
                        "version": clean_ver,
                        "purl": f"pkg:composer/{name}@{clean_ver}",
                        "properties": [{"name": "ecosystem", "value": "packagist"}],
                    })
        except Exception:
            pass

    # 4. Parse go.mod for Go modules
    gomod_path = os.path.join(root_dir, "go.mod")
    if os.path.exists(gomod_path):
        try:
            with open(gomod_path, "r", encoding="utf-8", errors="ignore") as f:
                in_require = False
                for line in f:
                    line = line.strip()
                    if line.startswith("require ("):
                        in_require = True
                        continue
                    elif in_require and line == ")":
                        in_require = False
                        continue
                    elif in_require or line.startswith("require "):
                        parts = line.replace("require ", "").strip().split()
                        if len(parts) >= 2:
                            mod_name, mod_ver = parts[0], parts[1]
                            components.append({
                                "type": "library",
                                "name": mod_name,
                                "version": mod_ver,
                                "purl": f"pkg:golang/{mod_name}@{mod_ver}",
                                "properties": [{"name": "ecosystem", "value": "golang"}],
                            })
        except Exception:
            pass

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tools": [
                {
                    "vendor": "StackDoctor",
                    "name": "StackDoctor SBOM Engine",
                    "version": "2.0.0",
                }
            ],
            "component": {
                "type": "application",
                "name": project_name,
                "version": "1.0.0",
            },
        },
        "components": components,
    }
