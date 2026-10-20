import os
import sys
import string
from pathlib import Path


def quick_scan_dirs() -> list[str]:
    """
    Directories targeted by a Quick Scan:
    Desktop, Downloads, Documents, Temp.
    Only returns paths that actually exist on this machine.
    """
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "Downloads",
        home / "Documents",
        Path(os.environ.get("TEMP", "/tmp")),
    ]
    return [str(p) for p in candidates if p.exists()]


def full_scan_dirs() -> list[str]:
    """
    Directories targeted by a Full Scan.
    Windows → all mounted drives (C:\\, D:\\, …)
    Linux / macOS → filesystem root /
    """
    if sys.platform.startswith("win"):
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drives.append(drive)
        return drives
    return ["/"]


def custom_scan_dirs(paths: list[str]) -> list[str]:
    """
    Validate and return a user-supplied list of paths.
    Skips anything that doesn't exist.
    """
    valid = []
    for p in paths:
        if os.path.exists(p):
            valid.append(p)
        else:
            print(f"[scan_targets] Skipping invalid path: {p!r}")
    return valid