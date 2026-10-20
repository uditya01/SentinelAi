"""Damage Assessment page for Sentinel AI.

This first version reports existing detection evidence without pretending that
EMBER's malware score predicts system damage. Sandbox status remains explicitly
"not run" until a real isolated sandbox integration is implemented.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QComboBox,
    QScrollArea,
    QSizePolicy,
)

BG_CARD = "#0D1827"
BORDER = "#1A2540"
PRIMARY = "#E8EEF8"
SECONDARY = "#8892A4"
CYAN = "#00D4FF"
AMBER = "#FFB020"
RED = "#FF4466"
GREEN = "#00FF88"


class DamageAssessmentPage(QScrollArea):
    """Displays scan evidence while keeping predicted risk separate from impact."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._results = []

        root = QWidget()
        self.setWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        title = QLabel("Damage Assessment")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{PRIMARY};")
        subtitle = QLabel(
            "Review detection evidence, potential impact estimates, and sandbox observations separately."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"color:{SECONDARY};")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.file_selector = QComboBox()
        self.file_selector.setMinimumHeight(40)
        self.file_selector.setStyleSheet(
            f"QComboBox {{ background:{BG_CARD}; color:{PRIMARY}; border:1px solid {BORDER}; "
            "border-radius:8px; padding:8px; }"
            f"QComboBox QAbstractItemView {{ background:{BG_CARD}; color:{PRIMARY}; }}"
        )
        self.file_selector.currentIndexChanged.connect(self._show_selected)
        layout.addWidget(self.file_selector)

        self.file_path = self._value_label("Run a scan to populate detected files.")
        layout.addWidget(self._card("Selected file", self.file_path))

        self.malware_value = self._value_label("Not available")
        self.malware_note = self._note_label(
            "EMBER output is a malware-classification score, not a probability of damage."
        )
        layout.addWidget(
            self._card(
                "1 · Malware detection evidence", self.malware_value, self.malware_note
            )
        )

        self.damage_value = self._value_label("Not estimated")
        self.damage_note = self._note_label(
            "No validated damage model is connected yet. A damage percentage would be misleading at this stage."
        )
        layout.addWidget(
            self._card(
                "2 · Potential damage", self.damage_value, self.damage_note, AMBER
            )
        )

        self.sandbox_value = self._value_label("NOT RUN")
        self.sandbox_note = self._note_label(
            "No sandbox behavior has been observed. This is not evidence that the file is safe."
        )
        layout.addWidget(
            self._card(
                "3 · Observed sandbox impact",
                self.sandbox_value,
                self.sandbox_note,
                CYAN,
            )
        )

        self.summary = self._note_label(
            "Only THREAT and SUSPICIOUS scan results are listed here."
        )
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        layout.addStretch(1)

    @staticmethod
    def _value_label(text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Segoe UI", 12, QFont.Weight.DemiBold))
        label.setStyleSheet(f"color:{PRIMARY};")
        return label

    @staticmethod
    def _note_label(text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Segoe UI", 9))
        label.setStyleSheet(f"color:{SECONDARY};")
        return label

    def _card(self, heading, value, note=None, accent=CYAN):
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        frame.setStyleSheet(
            f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER}; border-radius:12px; }}"
        )
        box = QVBoxLayout(frame)
        box.setContentsMargins(18, 15, 18, 15)
        h = QLabel(heading)
        h.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        h.setStyleSheet(f"color:{accent};")
        box.addWidget(h)
        box.addWidget(value)
        if note is not None:
            box.addWidget(note)
        return frame

    def update_scan_result(self, scan_result):
        """Update from the existing ScanResult without changing scanner verdicts."""
        self._results = list(scan_result.threat_files)
        self.file_selector.blockSignals(True)
        self.file_selector.clear()
        for item in self._results:
            verdict = item.threat.verdict if item.threat else "UNKNOWN"
            self.file_selector.addItem(f"[{verdict}] {os.path.basename(item.path)}")
        self.file_selector.blockSignals(False)

        if not self._results:
            self.file_path.setText(
                "No THREAT or SUSPICIOUS files were returned by this scan."
            )
            self.malware_value.setText("No flagged files in this scan")
            self.damage_value.setText("Not estimated")
            self.sandbox_value.setText("NOT RUN")
            self.summary.setText(
                f"Scan completed: {scan_result.scanned_files:,} files scanned. "
                "A clean scan does not guarantee that every file is safe."
            )
            return

        self.summary.setText(
            f"{len(self._results)} flagged file(s) from the latest scan. "
            "Select a file above to review its evidence."
        )
        self.file_selector.setCurrentIndex(0)
        self._show_selected(0)

    def _show_selected(self, index):
        if index < 0 or index >= len(self._results):
            return
        item = self._results[index]
        threat = item.threat
        self.file_path.setText(item.path)
        if threat is None:
            self.malware_value.setText("No threat metadata available")
        else:
            pieces = [
                f"Verdict: {threat.verdict}",
                f"Source: {threat.source or 'unknown'}",
            ]
            if threat.malware_name:
                pieces.append(f"Detection: {threat.malware_name}")
            if threat.ml_score is not None:
                pieces.append(
                    f"EMBER classification score: {threat.ml_score:.4f} ({threat.ml_score:.2%})"
                )
            if threat.detection_count or threat.total_engines:
                pieces.append(
                    f"VirusTotal detections: {threat.detection_count}/{threat.total_engines}"
                )
            self.malware_value.setText("\n".join(pieces))
        self.damage_value.setText("Not estimated — no validated damage model")
        self.sandbox_value.setText("NOT RUN — no sandbox observations recorded")
