# StackDoctor — Scoring and Deployment Readiness Specification

## 1. Executive Summary

StackDoctor evaluates software repositories across five static quality and security domains. It separates **Health Score** (a 0–100 quality compliance metric) from **Deployment Readiness** (an actionable release gate indicating whether an application can be safely deployed to production).

---

## 2. Domain Weights and Scoring Formula

The overall Project Health Score is computed using a weighted composite formula:

$$\text{Health Score} = \sum_{i=1}^{5} \left( \text{Category Score}_i \times \text{Weight}_i \right)$$

| Domain | Weight | Canonical Key | Primary Focus |
| :--- | :---: | :--- | :--- |
| **Project Structure** | **15%** | `Project Structure` | Manifest presence, documentation (README), .gitignore, standard layout, .env.example |
| **Dependencies** | **20%** | `Dependencies` | Semantic version pinning, lockfile presence, vulnerable package detection |
| **Docker** | **20%** | `Docker` | Multi-stage build quality, unpinned/latest base tags, non-root USER execution, Compose syntax |
| **CI/CD** | **15%** | `CI/CD` | Automated test steps, build verification, least privilege permissions, trigger coverage |
| **Security** | **30%** | `Security` | API keys, secret detection, private key files, exposed `.env` files, credential masking |

### Deductions per Finding

Each category score starts at a baseline of **100 points**, with severity-based deductions:

$$\text{Category Score} = \max(0, \min(100, 100 - \sum \text{Finding Penalties}))$$

- **Critical:** -25 points
- **High:** -15 points
- **Medium:** -8 points
- **Low:** -3 points
- **Informational:** 0 points

---

## 3. Deployment Readiness Engine

Deployment readiness acts as an independent production gate that cannot be bypassed by high scores in other categories:

| Status | Trigger Condition | Operational Meaning |
| :--- | :--- | :--- |
| `READY` | Health Score $\ge$ 85, 0 Critical findings, 0 High findings | Approved for automated production deployment. |
| `READY WITH WARNINGS` | Health Score $\ge$ 60, 0 Critical findings, $\ge 1$ High findings or warnings | Manual sign-off recommended before deployment. |
| `BLOCKED` | $\ge 1$ Critical finding (e.g. exposed credentials, committed private keys, broken core manifests) or Security Score < 50 | Automated deployment blocked. Explicit remediation required. |
| `INSUFFICIENT DATA` | Unsupported stack or empty archive | Project architecture could not be verified. |

---

## 4. Rule-Based Fix Recommendations

Every identified finding is linked to an actionable recommendation:
- **`config_patch`**: Template `.env.example`, `.dockerignore`, or YAML adjustments.
- **`version_bump`**: Specific version pin or upgrade commands.
- **`security_remediation`**: Credential revocation steps and environment variable extraction.
- **`pipeline_step`**: CI test and build workflow jobs.
