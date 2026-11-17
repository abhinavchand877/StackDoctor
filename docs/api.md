# StackDoctor — REST API Reference

All requests require JWT authentication unless marked otherwise. Send tokens via header:
`Authorization: Bearer <access_token>`

---

## Authentication Endpoints

### `POST /api/auth/register`
Creates a new developer account.
```json
{
  "username": "developer1",
  "email": "dev1@example.com",
  "password": "SecurePassword123!"
}
```

### `POST /api/auth/login`
Authenticates a user and returns a JWT access token.
```json
{
  "identifier": "developer1",
  "password": "SecurePassword123!"
}
```

### `GET /api/auth/me`
Returns details of the currently authenticated user.

---

## Scan & Upload Endpoints

### `POST /api/upload` / `POST /api/scans`
Uploads and executes a static health inspection on a project ZIP archive.
- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `file`: ZIP archive file (`.zip`)
  - `project_name` (optional): Project display label

**Response (201 Created):**
```json
{
  "message": "Scan completed successfully.",
  "scan": {
    "id": 1,
    "uuid": "SCAN-A1B2C3D4E5F6",
    "project_name": "DemoApp",
    "health_score": 92,
    "risk_level": "Healthy",
    "readiness_status": "READY",
    "readiness_reasons": ["All security policies and validations passed."],
    "detected_technologies": ["Python", "Docker", "GitHub Actions"],
    "total_findings": 2,
    "scan_duration": 1.42,
    "category_scores": {
      "Project Structure": { "score": 100, "weight": 15, "status": "Passed" },
      "Dependencies": { "score": 92, "weight": 20, "status": "Warning" },
      "Docker": { "score": 100, "weight": 20, "status": "Passed" },
      "CI/CD": { "score": 100, "weight": 15, "status": "Passed" },
      "Security": { "score": 100, "weight": 30, "status": "Passed" }
    }
  }
}
```

### `GET /api/scans`
Returns a list of all historical scans and aggregate metrics for the authenticated user.

### `GET /api/scans/<id>`
Returns complete details and findings for a specific scan. Accepts integer ID or UUID string.

### `GET /api/scans/<id>/findings`
Returns detailed findings with optional query parameters:
- `?category=Security`
- `?severity=Critical`

### `GET /api/scans/<id>/score`
Returns category scores, domain weights, and overall weighted health score.

### `GET /api/scans/<id>/readiness`
Returns deployment readiness status (`READY`, `READY WITH WARNINGS`, `BLOCKED`, `INSUFFICIENT DATA`) and blocking explanations.

### `DELETE /api/scans/<id>`
Deletes a scan record and all associated findings from the database.

---

## Comparison Endpoint

### `GET /api/scans/compare?base_id=<id1>&target_id=<id2>`
Compares two scans, calculating health score delta, newly introduced findings, and resolved findings.

---

## Report Export Endpoints

### `GET /api/scans/<id>/report/pdf`
Downloads an executive PDF health report.
- Supports `Authorization: Bearer <token>` or `?token=<jwt_token>`.

### `GET /api/scans/<id>/report/json`
Downloads standard structured JSON health report.

### `GET /api/scans/<id>/report/sarif`
Downloads standard SARIF v2.1.0 report for CI/CD and GitHub Code Scanning integration.

### `GET /api/scans/<id>/report/sbom`
Downloads CycloneDX v1.5 Software Bill of Materials (SBOM) JSON.

---

## System Endpoints

### `GET /api/health`
Unauthenticated system health check. Verifies backend and database connectivity.
