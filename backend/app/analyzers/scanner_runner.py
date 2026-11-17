import os
import shutil
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("stackdoctor.scanner_runner")

def is_tool_available(tool_name: str) -> bool:
    """Checks if an external CLI tool binary is installed and executable on the PATH."""
    return shutil.which(tool_name) is not None

def run_command_safely(
    cmd: List[str],
    cwd: Optional[str] = None,
    timeout: int = 20,
) -> Dict[str, Any]:
    """
    Safely executes a CLI analysis command without shell=True to avoid injection.
    Enforces a strict timeout and captures stdout/stderr.
    Returns status, exit code, output, and whether the tool was found.
    """
    if not cmd:
        return {"available": False, "success": False, "output": "", "error": "Empty command"}

    binary = cmd[0]
    binary_path = shutil.which(binary)
    if not binary_path:
        return {
            "available": False,
            "success": False,
            "output": "",
            "error": f"Tool binary '{binary}' is not installed or not in PATH.",
        }

    try:
        # Use full binary path and pass arguments safely as a list
        exec_cmd = [binary_path] + cmd[1:]
        result = subprocess.run(
            exec_cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return {
            "available": True,
            "success": result.returncode in (0, 1),  # Some scanners return 1 when findings are discovered
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": None,
        }
    except subprocess.TimeoutExpired:
        logger.warning(f"Scanner '{binary}' timed out after {timeout} seconds.")
        return {
            "available": True,
            "success": False,
            "output": "",
            "error": f"Scanner '{binary}' execution timed out after {timeout}s.",
        }
    except Exception as e:
        logger.error(f"Error running scanner '{binary}': {str(e)}")
        return {
            "available": True,
            "success": False,
            "output": "",
            "error": str(e),
        }
