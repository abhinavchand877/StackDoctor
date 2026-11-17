# StackDoctor Security Policy & Boundaries

## 1. Security Overview

StackDoctor is designed as a **Static Project Analysis Tool**. Its core objective is to analyze project layouts, manifests, configuration files, and potential configuration mistakes **without executing untrusted code**.

### Foundational Security Guarantee:
> **StackDoctor NEVER runs uploaded code.**
> It never executes `python`, `node`, `bash`, `pip install`, `npm install`, or `docker build` on any uploaded file. All inspection is strictly static string, regex, AST, or YAML/JSON parsing.

---

## 2. ZIP Archive Processing Defense

Uploading archives introduces potential file-system risks. StackDoctor implements multi-layered defenses:

1. **Path Traversal Prevention (`ZipSlip`):**
   - Every file entry in the ZIP is inspected for traversal sequences (`..`, `/..`, `../`, `C:`).
   - Extraction paths are resolved and strictly validated to ensure they reside within an isolated temporary sandbox (`tempfile.mkdtemp()`).

2. **ZIP Bomb & Resource Exhaustion Defense:**
   - **Upload Limit:** Capped at 50 MB compressed.
   - **Extracted Size Limit:** Cumulative extracted file size is clamped at 150 MB.
   - **Entry Count Limit:** Maximum 3,000 entries.
   - **Compression Ratio Check:** Entries exceeding a 100:1 compression ratio with size over 10 MB are rejected immediately.

3. **Symbolic Link Rejection:**
   - UNIX symlinks embedded inside ZIP archives (`0o120000` mode) are rejected to prevent directory escape attacks.

4. **Encrypted Archives:**
   - Encrypted/password-protected archives are rejected upfront to prevent inspection evasion.

5. **Automatic Cleanup:**
   - All extracted projects are placed inside temporary directories and cleaned up immediately after analysis via Python context managers, even if an exception occurs.

---

## 3. Secret Detection & Exposure Prevention

1. **Secret Masking:**
   - Detected secret values (e.g. `sk-...`, `AKIA...`, `ghp_...`, passwords) are **masked** (e.g., `sk-****************`) before being saved to the database, returned via API, or written to PDF reports.
   - Raw secrets are never written to logs or persisted in plaintext.

2. **Heuristic Scope & False Positives:**
   - Static regex patterns identify potential credential patterns. Because regex pattern matching cannot determine whether a key is active, matches are labeled as **potential exposures**.

---

## 4. User Tenancy & API Security

1. **Strict Tenancy Isolation:**
   - Every scan record is associated with the authenticated `user_id`.
   - Access to scan details, findings, deletion, and PDF generation requires valid JWT authorization matching the owning user. Users cannot view or delete another user's scans.

2. **Password Security:**
   - User passwords are never stored in plaintext. They are hashed using `werkzeug.security` (PBKDF2 with SHA-256).

3. **Database Parameterization:**
   - All database queries are executed through SQLAlchemy ORM, protecting against SQL injection vulnerabilities.

---

## 5. Known Limitations

- **Compiled Binaries:** StackDoctor does not decompile `.class`, `.dll`, or ELF binaries.
- **Deep Code Vulnerability Analysis:** This tool focuses on project structure, configuration, containerization, dependencies, and CI/CD pipelines. It is not an AST-based taint analysis tool or dynamic runtime sandbox.
