import json
from typing import Dict, Any

def generate_sarif_report(scan_data: Dict[str, Any]) -> str:
    """
    Converts a StackDoctor scan dictionary and its findings into standard SARIF v2.1.0 JSON format.
    Compatible with GitHub Code Scanning, SonarQube, and CI security dashboards.
    """
    findings = scan_data.get("findings", [])
    rules_map = {}
    sarif_results = []

    sev_to_sarif = {
        "Critical": "error",
        "High": "error",
        "Medium": "warning",
        "Low": "note",
        "Informational": "note",
    }

    for f in findings:
        rule_id = f.get("rule_id", "SD-000")
        if rule_id not in rules_map:
            rules_map[rule_id] = {
                "id": rule_id,
                "name": f.get("title", rule_id),
                "shortDescription": {"text": f.get("title", rule_id)},
                "fullDescription": {"text": f.get("description", "")},
                "help": {"text": f.get("recommendation") or "Review and remediate according to guidelines."},
                "defaultConfiguration": {
                    "level": sev_to_sarif.get(f.get("severity", "Medium"), "warning")
                },
                "properties": {
                    "category": f.get("category") or f.get("module", "General"),
                    "tags": ["security", "deployment", f.get("category", "quality").lower()],
                },
            }

        line_num = f.get("line_number") or 1
        file_path = f.get("file_path") or "project"

        result = {
            "ruleId": rule_id,
            "level": sev_to_sarif.get(f.get("severity", "Medium"), "warning"),
            "message": {
                "text": f"{f.get('title')}: {f.get('description')}"
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_path.replace("\\", "/"),
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {
                            "startLine": max(1, line_num),
                            "startColumn": 1,
                        },
                    }
                }
            ],
            "properties": {
                "severity": f.get("severity", "Medium"),
                "scanner": f.get("scanner", "stackdoctor"),
                "recommendation": f.get("recommendation", ""),
            },
        }
        sarif_results.append(result)

    sarif_document = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "StackDoctor",
                        "fullName": "StackDoctor Intelligent Software Project Health Assessment Platform",
                        "semanticVersion": "2.0.0",
                        "version": "2.0.0",
                        "informationUri": "https://github.com/stackdoctor",
                        "rules": list(rules_map.values()),
                    }
                },
                "artifacts": [
                    {"location": {"uri": f.get("file_path", "project").replace("\\", "/")}}
                    for f in findings if f.get("file_path")
                ],
                "results": sarif_results,
            }
        ],
    }

    return json.dumps(sarif_document, indent=2)
