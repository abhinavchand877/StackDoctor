# StackDoctor — Security Architecture and Sandbox Model

## 1. Zero Code Execution Guarantee

StackDoctor enforces strict static analysis. Untrusted user projects are **never executed**:
- No scripts (`setup.py`, `install.sh`, `npm postinstall`) are executed.
- No packages or containers are built or run from user source code.
- Analysis occurs solely through file tree traversal, static text parsing, AST validation, and read-only tool invocation.

---

## 2. Secure ZIP Upload Sandbox Processor

Untrusted ZIP archives are processed with layered defenses:

1. **ZIP Slip / Path Traversal Prevention:**
   All entry paths are canonicalized. Absolute paths (`/etc/...`), drive letters (`C:...`), and directory traversal components (`../`) trigger immediate rejection. Target paths are verified to remain strictly within the isolated temporary extraction directory.

2. **ZIP Bomb Defense:**
   - Maximum compressed upload: 50 MB (configurable).
   - Maximum uncompressed extraction size: 150 MB.
   - Maximum entries: 3,000 files.
   - Compression ratio threshold: Rejects entries with decompression ratio > 100:1 when uncompressed size exceeds 10 MB.

3. **Symlink Attack Mitigation:**
   UNIX symbolic links (`0o120000`) within ZIP entries are rejected to prevent escaping the sandboxed extraction root.

4. **Guaranteed Ephemeral Cleanup:**
   Extraction directories are created with `tempfile.mkdtemp` and managed using Python context managers. Extracted contents are wiped upon request completion.

---

## 3. Secret Detection and Masking Guarantee

1. **Regex Pattern Engine + External Scanners:**
   Scans for OpenAI keys, AWS keys, GitHub tokens, Slack webhooks, private keys, and hardcoded credentials.
   Integrates Gitleaks and Trivy secret scanning when available.

2. **Strict Redaction:**
   Raw secret values are **never stored** in database records, **never logged** to disk, and **never sent** across API responses. Only masked strings (e.g., `sk-proj-DEMO****************`) are retained.

---

## 4. External Scanner Sandboxing

All CLI tool executions (Trivy, OSV-Scanner, Hadolint, Checkov, zizmor, Gitleaks, Syft):
- Run with `shell=False` passing arguments as an immutable list.
- Execute under strict subprocess timeouts (15–25 seconds).
- Silently fall back to deterministic Python static analysis engines if binaries are absent.
