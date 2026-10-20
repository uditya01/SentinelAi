
import os
from typing import Callable, Optional

from .hash_utils import compute_sha256
from .models import FileResult, ScanResult, ThreatInfo, UNKNOWN
from .threat_checker import ThreatChecker


def _is_excluded_path(file_path: str) -> bool:
    """Return True for files inside Sentinel AI's quarantine directory."""
    path = os.path.normcase(os.path.abspath(file_path))

    # Resolve the project's quarantine directory.
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    quarantine_dir = os.path.normcase(
        os.path.abspath(os.path.join(project_root, "quarantine"))
    )

    try:
        return os.path.commonpath([path, quarantine_dir]) == quarantine_dir
    except ValueError:
        # Different drives or incompatible paths.
        return False



def run_scan(
    directories: list[str],
    on_progress: Optional[Callable[[int, int, str], None]] = None,
    on_threat: Optional[Callable[[FileResult], None]] = None,
    abort_flag: Optional[Callable[[], bool]] = None,
    checker: Optional[ThreatChecker] = None,
) -> ScanResult:
    """Count eligible files first, then scan with accurate progress."""

    result = ScanResult(target_dirs=directories, total_files=0)

    def should_abort() -> bool:
        return bool(abort_flag and abort_flag())

    def walk_error(_error):
        # Continue through folders that remain accessible.
        return

    def iter_files():
        """Yield eligible file paths without entering quarantine."""
        for directory in directories:
            if should_abort():
                return
            if not os.path.isdir(directory):
                continue

            for root, dirs, filenames in os.walk(
                directory, onerror=walk_error
            ):
                if should_abort():
                    return

                dirs[:] = [
                    name for name in dirs
                    if not _is_excluded_path(os.path.join(root, name))
                ]

                for filename in filenames:
                    if should_abort():
                        return

                    file_path = os.path.join(root, filename)
                    if not _is_excluded_path(file_path):
                        yield file_path

    # Phase 1: count eligible files.
    total = sum(1 for _ in iter_files())
    result.total_files = total

    if should_abort():
        result.aborted = True
        return result

    # Phase 2: scan files and report actual percentage progress.
    processed = 0

    for file_path in iter_files():
        if should_abort():
            result.aborted = True
            break

        processed += 1

        try:
            size = os.path.getsize(file_path)
        except OSError:
            size = 0

        
        sha256, error = compute_sha256(file_path)

        # Stop if cancellation was requested while hashing.
        if should_abort():
            result.aborted = True
            break

        threat: Optional[ThreatInfo] = None

        if sha256 and checker:
            # Avoid entering the detection pipeline if cancellation arrived
            # during hashing.
            if should_abort():
                result.aborted = True
                break

            threat = checker.check(sha256, file_path=file_path)

            # Discard a result from a check interrupted by cancellation and do
            # not start processing another file.
            if should_abort():
                result.aborted = True
                break

        elif sha256:
            threat = ThreatInfo(verdict=UNKNOWN)


        file_result = FileResult(
            path=file_path,
            sha256=sha256,
            size_bytes=size,
            error=error,
            threat=threat,
        )
        result.files.append(file_result)

        if file_result.ok:
            result.scanned_files += 1
            result.total_bytes += size
        else:
            result.skipped_files += 1

        if file_result.is_threat:
            result.threats_found += 1
            if on_threat:
                on_threat(file_result)

        if on_progress:
            on_progress(processed, total, file_path)

    if should_abort():
        result.aborted = True

    return result
