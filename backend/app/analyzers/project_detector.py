import os
import json
from typing import List, Dict, Any

class ProjectDetector:
    """
    Inspects directory structures and configuration files to identify project frameworks and ecosystems.
    """

    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def detect(self) -> Dict[str, Any]:
        """
        Analyzes the root directory and returns a dictionary of detected technologies and metadata.
        """
        detected = []
        details = {}

        # Core programming languages and frameworks
        is_python, py_details = self._check_python()
        if is_python:
            detected.append("Python")
            details["python"] = py_details

        is_node, node_details = self._check_node()
        if is_node:
            detected.append("Node.js")
            details["node"] = node_details

            # React check is a specialization of Node.js
            is_react, react_details = self._check_react(node_details)
            if is_react:
                detected.append("React")
                details["react"] = react_details

        is_java, java_details = self._check_java()
        if is_java:
            detected.append("Java")
            details["java"] = java_details

        is_php, php_details = self._check_php()
        if is_php:
            detected.append("PHP")
            details["php"] = php_details

        is_go, go_details = self._check_go()
        if is_go:
            detected.append("Go")
            details["go"] = go_details

        # Supportive ecosystem indicators
        if self._check_docker():
            detected.append("Docker")

        if self._check_github_actions():
            detected.append("GitHub Actions")

        primary_types = [t for t in detected if t in ["Python", "Node.js", "React", "Java", "PHP", "Go"]]
        if not primary_types:
            supported = False
            message = "Project type could not be identified as Python, Node.js, React, Java, PHP, or Go."
        else:
            supported = True
            message = f"Detected {', '.join(detected)} project configuration."

        return {
            "supported": supported,
            "technologies": detected,
            "primary_types": primary_types,
            "message": message,
            "details": details,
        }

    def _check_python(self) -> tuple[bool, dict]:
        py_files = []
        manifests = []
        
        candidates = ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py", "setup.cfg"]
        for cand in candidates:
            if os.path.exists(os.path.join(self.root_dir, cand)):
                manifests.append(cand)

        # Check for any .py files in root or shallow subdirectories
        for root, dirs, files in os.walk(self.root_dir):
            # Do not traverse too deep for detection
            depth = root[len(self.root_dir):].count(os.sep)
            if depth > 2:
                continue
            for f in files:
                if f.endswith(".py"):
                    py_files.append(f)
                    if len(py_files) >= 5:
                        break
            if len(py_files) >= 5:
                break

        is_python = bool(manifests or py_files)
        return is_python, {"manifests": manifests, "has_py_files": bool(py_files)}

    def _check_node(self) -> tuple[bool, dict]:
        pkg_path = os.path.join(self.root_dir, "package.json")
        has_pkg = os.path.exists(pkg_path)
        
        lockfiles = []
        for lock in ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"]:
            if os.path.exists(os.path.join(self.root_dir, lock)):
                lockfiles.append(lock)

        pkg_data = {}
        if has_pkg:
            try:
                with open(pkg_path, "r", encoding="utf-8", errors="ignore") as f:
                    pkg_data = json.load(f)
            except Exception:
                pkg_data = {}

        is_node = has_pkg or bool(lockfiles)
        return is_node, {"has_package_json": has_pkg, "lockfiles": lockfiles, "package_data": pkg_data}

    def _check_react(self, node_details: dict) -> tuple[bool, dict]:
        pkg_data = node_details.get("package_data", {})
        dependencies = pkg_data.get("dependencies", {})
        dev_dependencies = pkg_data.get("devDependencies", {})
        
        all_deps = {**dependencies, **dev_dependencies}
        
        has_react_dep = "react" in all_deps or "react-dom" in all_deps or "react-scripts" in all_deps
        has_vite_react = "vite" in all_deps and ("@vitejs/plugin-react" in all_deps or "@vitejs/plugin-react-swc" in all_deps)
        
        src_exists = os.path.isdir(os.path.join(self.root_dir, "src"))
        
        vite_config = any(
            os.path.exists(os.path.join(self.root_dir, f))
            for f in ["vite.config.js", "vite.config.ts", "vite.config.mjs"]
        )

        is_react = has_react_dep or (has_vite_react and src_exists)
        return is_react, {
            "has_react_dep": has_react_dep,
            "has_vite_config": vite_config,
            "has_src_dir": src_exists,
        }

    def _check_java(self) -> tuple[bool, dict]:
        manifests = []
        for cand in ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "mvnw", "gradlew"]:
            if os.path.exists(os.path.join(self.root_dir, cand)):
                manifests.append(cand)

        java_files = []
        for root, dirs, files in os.walk(self.root_dir):
            depth = root[len(self.root_dir):].count(os.sep)
            if depth > 4:
                continue
            for f in files:
                if f.endswith((".java", ".kt", ".scala")):
                    java_files.append(f)
                    if len(java_files) >= 5:
                        break
            if len(java_files) >= 5:
                break

        is_java = bool(manifests or java_files)
        return is_java, {"manifests": manifests, "has_java_files": bool(java_files)}

    def _check_php(self) -> tuple[bool, dict]:
        manifests = []
        for cand in ["composer.json", "composer.lock"]:
            if os.path.exists(os.path.join(self.root_dir, cand)):
                manifests.append(cand)

        php_files = []
        for root, dirs, files in os.walk(self.root_dir):
            depth = root[len(self.root_dir):].count(os.sep)
            if depth > 3:
                continue
            for f in files:
                if f.endswith(".php"):
                    php_files.append(f)
                    if len(php_files) >= 5:
                        break
            if len(php_files) >= 5:
                break

        is_php = bool(manifests or php_files)
        return is_php, {"manifests": manifests, "has_php_files": bool(php_files)}

    def _check_go(self) -> tuple[bool, dict]:
        manifests = []
        for cand in ["go.mod", "go.sum", "Gopkg.lock"]:
            if os.path.exists(os.path.join(self.root_dir, cand)):
                manifests.append(cand)

        go_files = []
        for root, dirs, files in os.walk(self.root_dir):
            depth = root[len(self.root_dir):].count(os.sep)
            if depth > 3:
                continue
            for f in files:
                if f.endswith(".go"):
                    go_files.append(f)
                    if len(go_files) >= 5:
                        break
            if len(go_files) >= 5:
                break

        is_go = bool(manifests or go_files)
        return is_go, {"manifests": manifests, "has_go_files": bool(go_files)}

    def _check_docker(self) -> bool:
        docker_indicators = [
            "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
            "compose.yml", "compose.yaml", ".dockerignore"
        ]
        return any(os.path.exists(os.path.join(self.root_dir, item)) for item in docker_indicators)

    def _check_github_actions(self) -> bool:
        workflows_dir = os.path.join(self.root_dir, ".github", "workflows")
        if os.path.isdir(workflows_dir):
            for f in os.listdir(workflows_dir):
                if f.endswith((".yml", ".yaml")):
                    return True
        return False
