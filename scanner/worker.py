"""
scanner/worker.py

QThread worker — runs scanner.py off the UI thread and emits Qt signals.
Now passes a ThreatChecker into the scan and emits threat_found signal.
"""

import hashlib
import os
import threading
import time

from PyQt6.QtCore import QThread, pyqtSignal
from .models import FileResult, ScanResult, ThreatInfo, UNKNOWN
from .scanner import run_scan
from .scan_targets import quick_scan_dirs, full_scan_dirs, custom_scan_dirs
from .threat_checker import ThreatChecker
from threading import Event


class ScanWorker(QThread):
    """
    Signals
    -------
    progress(current, total, path)      — after every file
    threat_found(FileResult)            — immediately when a threat is detected
    file_scanned(FileResult)            — after every file (for logging)
    finished(ScanResult)                — once at the end
    error(str)                          — if scan cannot start
    """

    progress = pyqtSignal(int, int, str)
    threat_found = pyqtSignal(object)  # FileResult with threat info
    file_scanned = pyqtSignal(object)  # every FileResult
    finished = pyqtSignal(object)  # ScanResult
    error = pyqtSignal(str)

    def __init__(
        self,
        mode: str = "quick",
        custom_paths: list[str] = None,
        vt_api_key: str = "",
        use_virustotal: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.mode = mode
        self.custom_paths = custom_paths or []
        self.vt_api_key = vt_api_key
        self.use_virustotal = use_virustotal
        self._abort = Event()

    def abort(self):
        """Request cancellation from the UI thread."""
        self._abort.set()

    def _should_abort(self) -> bool:
        return self._abort.is_set()


    def run(self):
        directories = self._get_directories()

        if not directories:
            self.error.emit(f"No valid directories found for mode '{self.mode}'.")
            return

        checker = ThreatChecker(
            vt_api_key=self.vt_api_key,
            use_virustotal=self.use_virustotal and bool(self.vt_api_key),
            abort_flag=self._should_abort,
        )

        stop_event = threading.Event()
        monitor_ready = threading.Event()

        monitor_thread = threading.Thread(
            target=self._monitor_new_files,
            args=(directories, stop_event, monitor_ready),
            daemon=True,
        )

        monitor_thread.start()

        try:
            # Wait until the monitor has recorded the existing files.
            while not monitor_ready.wait(0.1):
                if self._should_abort():
                    stop_event.set()
                    monitor_thread.join(timeout=2)
                    return

            if self._should_abort():
                stop_event.set()
                monitor_thread.join(timeout=2)
                return

            result = run_scan(
                directories=directories,
                on_progress=self._on_progress,
                on_threat=self._on_threat,
                abort_flag=self._should_abort,
                checker=checker,
            )

            self.finished.emit(result)

        except Exception as exc:
            self.error.emit(f"Scan failed: {exc}")

        finally:
            stop_event.set()
            monitor_thread.join(timeout=2)

    def _get_directories(self) -> list[str]:
        if self.mode == "quick":
            return quick_scan_dirs()
        elif self.mode == "full":
            return full_scan_dirs()
        elif self.mode == "custom":
            return custom_scan_dirs(self.custom_paths)
        return []

    def _on_progress(self, current: int, total: int, path: str):
        self.progress.emit(current, total, path)

    def _on_threat(self, file_result: FileResult):
        self.threat_found.emit(file_result)

    def _monitor_new_files(self, directories, stop_event, ready_event):
        # Record files that already exist when monitoring begins.
        known_files = set()

        for directory in directories:
            if not os.path.isdir(directory):
                continue

            for root, _, filenames in os.walk(directory):
                if stop_event.is_set():
                    ready_event.set()
                    return

                for name in filenames:
                    known_files.add(
                        os.path.normcase(os.path.abspath(os.path.join(root, name)))
                    )
                for directory in directories:
                    if not os.path.isdir(directory):
                        continue

                    for root, _, filenames in os.walk(directory):
                        if stop_event.is_set():
                            ready_event.set()
                            return

                        for name in filenames:
                            known_files.add(
                                os.path.normcase(
                                    os.path.abspath(os.path.join(root, name))
                                )
                            )

        # Add this line here, outside both loops.
        ready_event.set()

        checker = ThreatChecker(use_virustotal=False)
        alerted = set()

        while not stop_event.wait(1.0):
            for directory in directories:
                if not os.path.isdir(directory):
                    continue

                for root, _, filenames in os.walk(directory):
                    if stop_event.is_set():
                        return

                    for name in filenames:
                        path = os.path.normcase(
                            os.path.abspath(os.path.join(root, name))
                        )

                        if path in known_files:
                            continue

                        known_files.add(path)

                        # Ignore files that are still being written.
                        try:
                            size_before = os.path.getsize(path)
                            time.sleep(0.15)
                            if os.path.getsize(path) != size_before:
                                continue

                            with open(path, "rb") as f:
                                digest = hashlib.sha256(f.read()).hexdigest()

                            size = os.path.getsize(path)
                        except (OSError, PermissionError):
                            continue

                        if digest in alerted:
                            continue

                        try:
                            threat = checker.check(digest, file_path=path)
                        except Exception as exc:
                            print(f"[Live monitor] Check failed for {path}: {exc}")
                            continue

                        if not threat or threat.verdict not in ("THREAT", "SUSPICIOUS"):
                            continue

                        alerted.add(digest)

                        result = FileResult(
                            path=path,
                            sha256=digest,
                            size_bytes=size,
                            error=None,
                            threat=threat,
                        )

                        print(f"[Live monitor] Threat detected: {path}")
                        self.threat_found.emit(result)
