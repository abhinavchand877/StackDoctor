import os
from typing import List, Dict, Any

class StructureAnalyzer:
    """
    Module 1: Evaluates project layout, essential configuration files, documentation, and testing layout.
    """

    def __init__(self, root_dir: str, detected_info: Dict[str, Any]):
        self.root_dir = root_dir
        self.detected_info = detected_info
        self.technologies = detected_info.get("technologies", [])

    def analyze(self) -> List[Dict[str, Any]]:
        findings = []

        # 1. README documentation check (Universal)
        readme_candidates = ["README.md", "README.rst", "README.txt", "readme.md"]
        has_readme = any(os.path.exists(os.path.join(self.root_dir, r)) for r in readme_candidates)
        if not has_readme:
            findings.append({
                "rule_id": "STR-001",
                "module": "Project Structure",
                "title": "Missing Project Documentation (README)",
                "description": "No README.md or equivalent documentation file was discovered in the project root.",
                "severity": "Medium",
                "file_path": "README.md",
                "explanation": "A README file is essential for onboarders, developers, and deployment automation to understand the project purpose, setup, and usage.",
                "recommendation": "Create a comprehensive README.md detailing project overview, installation, testing commands, and environment setup.",
                "penalty": 8,
            })

        # 2. .gitignore configuration (Universal)
        gitignore_path = os.path.join(self.root_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            findings.append({
                "rule_id": "STR-002",
                "module": "Project Structure",
                "title": "Missing .gitignore Configuration",
                "description": "No .gitignore file exists in the repository root directory.",
                "severity": "Medium",
                "file_path": ".gitignore",
                "explanation": "Without a .gitignore file, build artifacts, temporary cache files, local virtual environments, and sensitive keys risk being accidentally committed to version control.",
                "recommendation": "Add a standard .gitignore file appropriate for your tech stack (ignoring venv, node_modules, .env, build output).",
                "penalty": 8,
            })

        # 3. Test directory or automated test suite check (Universal)
        has_test_dir = False
        test_dir_candidates = ["tests", "test", "__tests__", "spec"]
        for td in test_dir_candidates:
            if os.path.isdir(os.path.join(self.root_dir, td)):
                has_test_dir = True
                break

        # Check for inline test files if no dedicated dir
        has_test_files = False
        if not has_test_dir:
            for root, _, files in os.walk(self.root_dir):
                for f in files:
                    lower = f.lower()
                    if lower.startswith("test_") or lower.endswith("_test.py") or lower.endswith(".test.js") or lower.endswith(".test.jsx") or lower.endswith(".spec.js") or lower.endswith(".spec.ts"):
                        has_test_files = True
                        break
                if has_test_files:
                    break

        if not has_test_dir and not has_test_files:
            findings.append({
                "rule_id": "STR-003",
                "module": "Project Structure",
                "title": "Missing Automated Test Suite or Directory",
                "description": "No test directory (such as 'tests/', '__tests__/') or recognized test files were found.",
                "severity": "Medium",
                "file_path": "tests/",
                "explanation": "Automated tests ensure software reliability and prevent regressions during continuous deployment.",
                "recommendation": "Create a 'tests/' directory with automated unit tests using Pytest, Vitest, or Jest.",
                "penalty": 8,
            })

        # 4. Python-specific structure
        if "Python" in self.technologies:
            py_manifests = ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"]
            has_manifest = any(os.path.exists(os.path.join(self.root_dir, m)) for m in py_manifests)
            if not has_manifest:
                findings.append({
                    "rule_id": "STR-004",
                    "module": "Project Structure",
                    "title": "Missing Python Dependency Manifest",
                    "description": "Python source files were detected, but no dependency manifest (requirements.txt, pyproject.toml, Pipfile) exists.",
                    "severity": "High",
                    "file_path": "requirements.txt",
                    "explanation": "Python projects need a clear specification of dependencies for reproducible builds in Docker and CI/CD pipelines.",
                    "recommendation": "Add a requirements.txt or pyproject.toml declaring all required runtime and development dependencies.",
                    "penalty": 15,
                })

        # 5. Node.js-specific structure
        if "Node.js" in self.technologies:
            pkg_path = os.path.join(self.root_dir, "package.json")
            if not os.path.exists(pkg_path):
                findings.append({
                    "rule_id": "STR-005",
                    "module": "Project Structure",
                    "title": "Missing package.json in Node.js Project",
                    "description": "Node.js project artifacts detected but package.json is missing in root.",
                    "severity": "High",
                    "file_path": "package.json",
                    "explanation": "package.json defines project metadata, scripts, and runtime dependencies required for npm/yarn/pnpm.",
                    "recommendation": "Run 'npm init' or add a valid package.json file.",
                    "penalty": 15,
                })

        # 6. React-specific structure
        if "React" in self.technologies:
            src_dir = os.path.join(self.root_dir, "src")
            if not os.path.isdir(src_dir):
                findings.append({
                    "rule_id": "STR-006",
                    "module": "Project Structure",
                    "title": "Missing 'src/' Directory in React Application",
                    "description": "A React project was identified, but standard 'src/' source folder is missing.",
                    "severity": "High",
                    "file_path": "src/",
                    "explanation": "Modern frontend bundlers (Vite, Webpack) expect components and entry points in a dedicated 'src' directory.",
                    "recommendation": "Organize your React components, assets, and entry points inside a 'src/' folder.",
                    "penalty": 15,
                })
            else:
                # Check for entry points
                entry_candidates = ["main.jsx", "main.tsx", "main.js", "index.jsx", "index.tsx", "index.js", "App.jsx", "App.tsx", "App.js"]
                has_entry = any(os.path.exists(os.path.join(src_dir, e)) for e in entry_candidates)
                if not has_entry:
                    findings.append({
                        "rule_id": "STR-007",
                        "module": "Project Structure",
                        "title": "Missing React Application Entry Point",
                        "description": "Could not locate standard React entry point (App.jsx, main.jsx, index.js) inside src/.",
                        "severity": "Medium",
                        "file_path": "src/App.jsx",
                        "explanation": "The build bundler needs a root application entry file to render the React component hierarchy.",
                        "recommendation": "Provide an App.jsx and main.jsx (or index.js) in src/ to mount the application.",
                        "penalty": 8,
                    })

        # 7. Environment example configuration (Universal Best Practice)
        env_example_candidates = [".env.example", ".env.sample", ".env.template", "env.example"]
        has_env_example = any(os.path.exists(os.path.join(self.root_dir, e)) for e in env_example_candidates)
        if not has_env_example:
            findings.append({
                "rule_id": "STR-008",
                "module": "Project Structure",
                "category": "Project Structure",
                "title": "Missing Environment Configuration Example (.env.example)",
                "description": "No .env.example or template file exists to document required runtime environment variables.",
                "severity": "Low",
                "file_path": ".env.example",
                "explanation": "A .env.example file provides developers and deployment systems with the schema of required configuration variables without leaking actual secret values.",
                "recommendation": "Add a .env.example file with placeholder values for all necessary environment variables.",
                "penalty": 3,
            })

        # 8. Java-specific structure
        if "Java" in self.technologies:
            java_manifests = ["pom.xml", "build.gradle", "build.gradle.kts"]
            has_java_manifest = any(os.path.exists(os.path.join(self.root_dir, m)) for m in java_manifests)
            if not has_java_manifest:
                findings.append({
                    "rule_id": "STR-009",
                    "module": "Project Structure",
                    "category": "Project Structure",
                    "title": "Missing Java Build Manifest (pom.xml or build.gradle)",
                    "description": "Java source files were detected, but no build manifest (pom.xml or build.gradle) exists in the project root.",
                    "severity": "High",
                    "file_path": "pom.xml",
                    "explanation": "Java builds require Maven or Gradle build manifests to resolve dependencies, compile classes, and assemble artifacts.",
                    "recommendation": "Add a standard pom.xml for Maven or build.gradle for Gradle.",
                    "penalty": 15,
                })

        # 9. PHP-specific structure
        if "PHP" in self.technologies:
            composer_path = os.path.join(self.root_dir, "composer.json")
            if not os.path.exists(composer_path):
                findings.append({
                    "rule_id": "STR-010",
                    "module": "Project Structure",
                    "category": "Project Structure",
                    "title": "Missing PHP composer.json",
                    "description": "PHP source files were detected, but composer.json is missing.",
                    "severity": "High",
                    "file_path": "composer.json",
                    "explanation": "Composer is the standard dependency manager for PHP. Without composer.json, package dependencies and PSR autoloading cannot be resolved.",
                    "recommendation": "Run 'composer init' or add a valid composer.json file.",
                    "penalty": 15,
                })

        # 10. Go-specific structure
        if "Go" in self.technologies:
            gomod_path = os.path.join(self.root_dir, "go.mod")
            if not os.path.exists(gomod_path):
                findings.append({
                    "rule_id": "STR-011",
                    "module": "Project Structure",
                    "category": "Project Structure",
                    "title": "Missing Go Module Definition (go.mod)",
                    "description": "Go source files were detected, but go.mod is missing in root.",
                    "severity": "High",
                    "file_path": "go.mod",
                    "explanation": "Go modules are the standard dependency management system for Go since Go 1.11. Without go.mod, dependencies cannot be reproducibly vendored or downloaded.",
                    "recommendation": "Run 'go mod init <module-path>' to initialize the module.",
                    "penalty": 15,
                })

        # Normalize common finding fields
        for f in findings:
            if "category" not in f:
                f["category"] = "Project Structure"
            if "scanner" not in f:
                f["scanner"] = "static_rule_engine"
            if "confidence" not in f:
                f["confidence"] = "HIGH"

        return findings
