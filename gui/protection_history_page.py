from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from threat_log.threat_log import ThreatLog

# ---------------- Colors ----------------
BG = "#0A0E1A"
CARD = "#101B2D"
BORDER = "#1E2A3F"
TEXT = "#E8EEF8"
SUBTEXT = "#8892A4"
RED = "#FF4466"
CYAN = "#00D4FF"
GREEN = "#00FF88"
AMBER = "#FFB020"


class StatCard(QFrame):
    """Compact, responsive statistic card."""

    def __init__(self, title: str, value: str, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("ProtectionHistoryStatCard")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(96)
        self.setStyleSheet(f"""
            QFrame#ProtectionHistoryStatCard {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(5)

        self.value_lbl = QLabel(str(value))
        self.value_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.value_lbl.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )
        self.value_lbl.setMinimumWidth(0)

        self.title_lbl = QLabel(title)
        self.title_lbl.setFont(QFont("Segoe UI", 9))
        self.title_lbl.setStyleSheet(
            f"color: {SUBTEXT}; background: transparent; border: none;"
        )
        self.title_lbl.setWordWrap(True)

        layout.addWidget(self.value_lbl)
        layout.addWidget(self.title_lbl)


class ThreatCard(QFrame):
    """One history entry; all columns can shrink to fit the viewport."""

    def __init__(self, time, threat, file, source, action, parent=None):
        super().__init__(parent)
        self.setObjectName("ProtectionHistoryThreatCard")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(f"""
            QFrame#ProtectionHistoryThreatCard {{
                background: {CARD};
                border: 1px solid {BORDER};
                border-radius: 12px;
            }}
            """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        icon = QLabel("🛡")
        icon.setFont(QFont("Segoe UI Emoji", 22))
        icon.setFixedWidth(34)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(4)

        threat_lbl = QLabel(str(threat or "Unknown threat"))
        threat_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        threat_lbl.setStyleSheet(
            f"color: {RED}; background: transparent; border: none;"
        )
        threat_lbl.setWordWrap(True)

        file_lbl = QLabel(str(file or "Unknown file"))
        file_lbl.setFont(QFont("Segoe UI", 9))
        file_lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        file_lbl.setWordWrap(True)
        file_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        time_lbl = QLabel(str(time or ""))
        time_lbl.setFont(QFont("Segoe UI", 9))
        time_lbl.setStyleSheet(
            f"color: {SUBTEXT}; background: transparent; border: none;"
        )
        time_lbl.setWordWrap(True)

        info.addWidget(threat_lbl)
        info.addWidget(file_lbl)
        info.addWidget(time_lbl)
        info_widget = QWidget()
        info_widget.setMinimumWidth(0)
        info_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        info_widget.setLayout(info)
        layout.addWidget(info_widget, 1)

        right_widget = QWidget()
        right_widget.setMinimumWidth(0)
        right_widget.setMaximumWidth(140)
        right_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        right = QVBoxLayout(right_widget)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(6)
        right.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        src = QLabel(str(source or "Unknown source"))
        src.setFont(QFont("Segoe UI", 8))
        src.setStyleSheet(f"color: {CYAN}; background: transparent; border: none;")
        src.setWordWrap(True)
        src.setAlignment(Qt.AlignmentFlag.AlignRight)
        src.setMinimumWidth(0)

        act = QLabel(str(action or "Detected"))
        act.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        action_color = (
            GREEN if str(action).lower() in ("quarantined", "restored") else AMBER
        )
        act.setStyleSheet(
            f"color: {action_color}; background: transparent; border: none;"
        )
        act.setWordWrap(True)
        act.setAlignment(Qt.AlignmentFlag.AlignRight)
        act.setMinimumWidth(0)

        right.addWidget(src)
        right.addWidget(act)
        layout.addWidget(right_widget, 0, Qt.AlignmentFlag.AlignTop)


class ProtectionHistoryPage(QScrollArea):
    """Protection History view backed by the existing ThreatLog database."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = ThreatLog()

        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setStyleSheet(f"""
            QScrollArea {{
                background: {BG};
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: {BG};
            }}
            """)

        root = QWidget()
        root.setObjectName("ProtectionHistoryContent")
        root.setMinimumWidth(0)
        root.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred
        )
        self.setWidget(root)

        self.root_layout = QVBoxLayout(root)
        self.root_layout.setContentsMargins(12, 16, 12, 18)
        self.root_layout.setSpacing(10)
        self.root_layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)

        self._build_header()
        self._build_stats()
        self._build_history_list()
        self.load_logs()

    def _build_header(self):
        header = QVBoxLayout()
        header.setSpacing(3)

        title = QLabel("🛡  Protection History")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        title.setWordWrap(True)

        subtitle = QLabel("Every detected threat is shown here.")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet(
            f"color: {SUBTEXT}; background: transparent; border: none;"
        )
        subtitle.setWordWrap(True)

        header.addWidget(title)
        header.addWidget(subtitle)
        self.root_layout.addLayout(header)

    def _build_stats(self):
        stats = QHBoxLayout()
        stats.setContentsMargins(0, 0, 0, 0)
        stats.setSpacing(12)

        self.total = StatCard("Total Threats", "0", RED)
        self.today = StatCard("Today", "0", CYAN)
        self.quarantine = StatCard("Quarantined", "0", GREEN)

        for card in (self.total, self.today, self.quarantine):
            stats.addWidget(card, 1)

        self.root_layout.addLayout(stats)

    def _build_history_list(self):
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.empty_label = QLabel("No protection events have been recorded yet.")
        self.empty_label.setFont(QFont("Segoe UI", 10))
        self.empty_label.setStyleSheet(f"color: {SUBTEXT}; padding: 28px 8px;")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setWordWrap(True)

        self.cards_layout.addWidget(self.empty_label)
        self.root_layout.addLayout(self.cards_layout)
        self.root_layout.addStretch(1)

    def load_logs(self):
        """Reload history from ThreatLog without changing its database schema."""
        logs = self.db.get_logs() or []

        # Remove prior cards, including the previous empty-state label.
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        total = len(logs)
        today_date = datetime.now().strftime("%Y-%m-%d")
        today_count = 0
        quarantined_count = 0

        for log in logs:
            log_time = str(log["time"] or "")
            action = str(log["action"] or "Detected")

            if log_time.startswith(today_date):
                today_count += 1
            if action.lower() == "quarantined":
                quarantined_count += 1

            card = ThreatCard(
                time=log_time,
                threat=log["threat_name"],
                file=log["file_name"],
                source=log["source"],
                action=action,
            )
            self.cards_layout.addWidget(card)

        if not logs:
            self.empty_label = QLabel("No protection events have been recorded yet.")
            self.empty_label.setFont(QFont("Segoe UI", 10))
            self.empty_label.setStyleSheet(f"color: {SUBTEXT}; padding: 28px 8px;")
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.empty_label.setWordWrap(True)
            self.cards_layout.addWidget(self.empty_label)

        self.total.value_lbl.setText(str(total))
        self.today.value_lbl.setText(str(today_count))
        self.quarantine.value_lbl.setText(str(quarantined_count))

    def add_threat(self, file_result):
        """Record a detection when automatic quarantine is not handling the event."""
        threat = getattr(file_result, "threat", None)
        if not threat or threat.verdict not in ("THREAT", "SUSPICIOUS"):
            return

        self.db.add_log(
            threat_name=threat.malware_name or "Suspicious file",
            file_path=file_result.path,
            sha256=file_result.sha256 or "",
            source=threat.source or "unknown",
            action="Detected",
        )
        self.load_logs()

    def refresh(self):
        """Compatibility alias for callers that use refresh()."""
        self.load_logs()
