import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from scanner.hash_utils import compute_sha256
from scanner.threat_checker import ThreatChecker
from quarantine.quarantine_manager import QuarantineManager
from notifications.notifier import NotificationManager
from threat_log.threat_log import ThreatLog
class RealTimeHandler(FileSystemEventHandler):

    def __init__(self):
        super().__init__()
        self.notifier = NotificationManager()
        self.threat_log = ThreatLog()

        self.checker = ThreatChecker()
        print("VT API Loaded:", bool(self.checker.vt_api_key))

        self.quarantine = QuarantineManager()

        
        self.last_scan = {}

    

    def scan_file(self, path):
        path_lower = os.path.abspath(path).lower()
        PROJECT_ROOT = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        ).lower()

        if path_lower.startswith(PROJECT_ROOT):
            return

        if "\\quarantine\\" in path_lower:
            return

        if "\\database\\" in path_lower:
            return

        if "\\logs\\" in path_lower:
            return

        if path_lower.endswith(".quarantined"):
            return

        if path_lower.endswith(".db"):
            return

        if path_lower.endswith(".db-journal"):
            return

        now = time.time()

        # Ignore duplicate events within 2 seconds
        if path in self.last_scan:
            if now - self.last_scan[path] < 2:
                return

        self.last_scan[path] = now

        print(f"\nScanning {path}")

        # Give Windows time to finish writing the file
        time.sleep(1)

        sha256 = None
        error = None

        for _ in range(10):

            sha256, error = compute_sha256(path)

            if not error:
                break

            time.sleep(0.5)

        if error:
            print("Hash Error:", error)
            return

        threat = self.checker.check(sha256)

        print("Verdict:", threat.verdict)

        if threat.is_threat:

            print("Threat:", threat.malware_name)

            try:

                record = self.quarantine.quarantine_file(
                    path=path,
                    malware_name=threat.malware_name,
                    sha256=sha256,
                )
                self.threat_log.add_log(
                    threat_name=threat.malware_name,
                    file_path=path,
                    sha256=sha256,
                    source=threat.source,
                )

                print("✓ File moved to quarantine")
                print("Location:", record.quarantine_path)
                self.notifier.threat_detected(
                    threat.malware_name,
                    path,
                )

            except Exception as e:

                print("Quarantine Error:", e)

        else:

            print("Clean")

   

    def on_created(self, event):

        if not event.is_directory:
            self.scan_file(event.src_path)

    

    def on_modified(self, event):

        if not event.is_directory:
            self.scan_file(event.src_path)


    def on_deleted(self, event):
        pass


class RealTimeMonitor:

    def __init__(self, folders):

        self.folders = folders
        self.observer = Observer()

    def start(self):

        handler = RealTimeHandler()

        for folder in self.folders:

            self.observer.schedule(
                handler,
                folder,
                recursive=True,
            )

        self.observer.start()

        print("✓ Real-Time Protection Started")

    def stop(self):

        self.observer.stop()
        self.observer.join()