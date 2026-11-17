import os
import zipfile
import tempfile
import shutil
from typing import Generator
from contextlib import contextmanager

IGNORED_DIRECTORIES = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
    "target",
}

BINARY_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".mp4", ".mp3", ".wav", ".avi", ".mov",
    ".woff", ".woff2", ".ttf", ".eot",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".class", ".jar", ".war"
}

class ZipProcessingError(Exception):
    """Custom exception raised for security or validation errors during ZIP handling."""
    pass


class ZipProcessor:
    def __init__(
        self,
        max_upload_size: int = 50 * 1024 * 1024,      # 50 MB
        max_extracted_size: int = 150 * 1024 * 1024,  # 150 MB
        max_entries: int = 3000,
        max_single_file_size: int = 2 * 1024 * 1024,  # 2 MB
    ):
        self.max_upload_size = max_upload_size
        self.max_extracted_size = max_extracted_size
        self.max_entries = max_entries
        self.max_single_file_size = max_single_file_size

    def validate_zip(self, file_path: str) -> None:
        """Validates archive presence, size, structure, and integrity before extraction."""
        if not os.path.exists(file_path):
            raise ZipProcessingError("Archive file does not exist.")

        file_size = os.path.getsize(file_path)
        if file_size > self.max_upload_size:
            raise ZipProcessingError(
                f"ZIP archive size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed limit of {self.max_upload_size / (1024*1024):.0f} MB."
            )

        if not zipfile.is_zipfile(file_path):
            raise ZipProcessingError("The uploaded file is not a valid ZIP archive or is corrupted.")

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # Check for encryption
                for zinfo in zf.infolist():
                    if zinfo.flag_bits & 0x1:
                        raise ZipProcessingError("Encrypted or password-protected ZIP archives are not supported.")

                # Check entry count
                entry_count = len(zf.infolist())
                if entry_count > self.max_entries:
                    raise ZipProcessingError(
                        f"Archive contains {entry_count} entries, exceeding limit of {self.max_entries}."
                    )

                # Test archive integrity
                bad_file = zf.testzip()
                if bad_file:
                    raise ZipProcessingError(f"Corrupted file detected in ZIP archive: {bad_file}")

                # Check cumulative uncompressed size and suspicious compression ratios (ZIP bomb prevention)
                total_uncompressed = 0
                for zinfo in zf.infolist():
                    total_uncompressed += zinfo.file_size
                    if total_uncompressed > self.max_extracted_size:
                        raise ZipProcessingError(
                            f"Total uncompressed content ({total_uncompressed / (1024*1024):.2f} MB) exceeds maximum safe limit of {self.max_extracted_size / (1024*1024):.0f} MB."
                        )
                    # ZIP bomb ratio check
                    if zinfo.compress_size > 0:
                        ratio = zinfo.file_size / zinfo.compress_size
                        if ratio > 100 and zinfo.file_size > 10 * 1024 * 1024:
                            raise ZipProcessingError("Archive rejected: Suspicious compression ratio detected (potential ZIP bomb).")

        except zipfile.BadZipFile as e:
            raise ZipProcessingError(f"Malformed or corrupt ZIP archive: {str(e)}")

    @contextmanager
    def extract_safely(self, file_path: str) -> Generator[str, None, None]:
        """
        Safely extracts the ZIP archive into an isolated temporary directory.
        Yields the root directory path of the extracted project.
        Guarantees that the temporary directory is deleted when the context exits.
        """
        self.validate_zip(file_path)
        temp_dir = tempfile.mkdtemp(prefix="stackdoctor_scan_")
        
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                for member in zf.infolist():
                    # Check for path traversal attacks
                    filename = member.filename
                    
                    # Normalize path separators
                    normalized = filename.replace("\\", "/")
                    
                    # Disallow absolute paths and traversal components
                    if (
                        normalized.startswith("/")
                        or normalized.startswith("../")
                        or "/../" in normalized
                        or normalized.endswith("/..")
                        or ":" in normalized  # Windows drive letters e.g. C:
                    ):
                        raise ZipProcessingError(f"Potential Path Traversal attack detected in ZIP entry: {filename}")

                    # Check for symlinks
                    # In standard ZIP, symlink unix mode is 0o120000
                    if (member.external_attr >> 16) & 0o120000 == 0o120000:
                        # Reject symlinks to prevent escaping extraction directory
                        continue

                    # Filter out ignored directories
                    parts = normalized.strip("/").split("/")
                    if any(part in IGNORED_DIRECTORIES for part in parts):
                        continue

                    # Prevent single file decompression explosion
                    if member.file_size > self.max_single_file_size * 5:
                        # Skip oversized files beyond safe limit
                        continue

                    # Safe target extraction path
                    target_path = os.path.realpath(os.path.join(temp_dir, filename))
                    real_temp_dir = os.path.realpath(temp_dir)
                    
                    if not target_path.startswith(real_temp_dir + os.sep) and target_path != real_temp_dir:
                        raise ZipProcessingError(f"Path traversal detected: {filename} resolves outside temp dir.")

                    if member.is_dir():
                        os.makedirs(target_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with zf.open(member) as source, open(target_path, "wb") as target:
                            shutil.copyfileobj(source, target)

            # Determine project root: if the zip contains a single top-level folder, use that as root
            extracted_items = [
                item for item in os.listdir(temp_dir)
                if item not in IGNORED_DIRECTORIES and not item.startswith(".")
            ]
            
            project_root = temp_dir
            if len(extracted_items) == 1:
                single_sub = os.path.join(temp_dir, extracted_items[0])
                if os.path.isdir(single_sub):
                    project_root = single_sub

            yield project_root

        finally:
            # Guarantee cleanup of all extracted files
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
