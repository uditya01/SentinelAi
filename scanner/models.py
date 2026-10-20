from dataclasses import dataclass, field
from typing import Optional

# ─── Threat verdict constants ─────────────────────────────────────────────────
CLEAN = "CLEAN"
THREAT = "THREAT"
SUSPICIOUS = "SUSPICIOUS"
UNKNOWN = "UNKNOWN"


@dataclass
class ThreatInfo:
    """Details about a detected threat."""

    verdict: str  # CLEAN | THREAT | SUSPICIOUS | UNKNOWN
    source: str = ""  # "local_db" | "virustotal" | ""
    malware_name: str = ""  # e.g. "Trojan.GenericKD.71234"
    detection_count: int = 0  # how many VT engines flagged it
    total_engines: int = 0  # total VT engines checked
    ml_score: Optional[float] = None

    @property
    def is_threat(self) -> bool:
        return self.verdict in (THREAT, SUSPICIOUS)

    def label(self) -> str:
        if self.verdict == THREAT:
            return (
                f"{self.malware_name or 'Malware'} [{self.source or 'unknown source'}]"
            )

        if self.verdict == SUSPICIOUS:
            if self.source == "ember_lightgbm" and self.ml_score is not None:
                return f"Suspicious (EMBER score: {self.ml_score:.1%})"

            if self.source == "virustotal":
                return (
                    f"Suspicious "
                    f"({self.detection_count}/{self.total_engines} engines)"
                )

            return f"Suspicious [{self.source or 'unknown source'}]"

        return self.verdict


@dataclass
class FileResult:
    """Holds the scan outcome for a single file."""

    path: str
    sha256: Optional[str]
    size_bytes: int
    error: Optional[str] = None
    threat: Optional[ThreatInfo] = None  # None until checked

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def is_threat(self) -> bool:
        return self.threat is not None and self.threat.is_threat

    def __repr__(self):
        status = self.sha256[:12] + "..." if self.sha256 else f"ERR({self.error})"
        verdict = self.threat.verdict if self.threat else "unchecked"
        return f"<FileResult {self.path!r} → {status} [{verdict}]>"


@dataclass
class ScanResult:
    """Aggregated results for an entire scan run."""

    target_dirs: list[str]
    files: list[FileResult] = field(default_factory=list)
    total_files: int = 0
    scanned_files: int = 0
    skipped_files: int = 0
    total_bytes: int = 0
    threats_found: int = 0
    aborted: bool = False

    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return self.scanned_files / self.total_files * 100

    @property
    def total_mb(self) -> float:
        return self.total_bytes / (1024 * 1024)

    @property
    def threat_files(self) -> list[FileResult]:
        return [f for f in self.files if f.is_threat]

    def summary(self) -> str:
        status = "ABORTED" if self.aborted else "COMPLETE"
        return (
            f"[{status}] Scanned {self.scanned_files}/{self.total_files} files "
            f"({self.total_mb:.1f} MB) — {self.threats_found} threats — "
            f"{self.skipped_files} skipped"
        )
