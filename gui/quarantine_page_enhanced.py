"""Responsive Quarantine page for Sentinel AI."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox, QLineEdit, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics

from quarantine.quarantine_manager import QuarantineManager, QuarantineRecord

BG_BASE = "#0A0E1A"
BG_CARD = "#0D1827"
ACCENT_CYAN = "#00D4FF"
ACCENT_GREEN = "#00FF88"
ACCENT_RED = "#FF4466"
ACCENT_AMBER = "#FFB020"
TEXT_PRIMARY = "#E8EEF8"
TEXT_SECONDARY = "#8892A4"
BORDER_COLOR = "#1A2540"


def _elide(label: QLabel, full_text: str, width: int | None = None):
    """Keep long paths and names from forcing the whole page wider."""
    available = width if width is not None else max(40, label.width())
    label.setToolTip(full_text)
    label.setText(QFontMetrics(label.font()).elidedText(
        full_text, Qt.TextElideMode.ElideMiddle, available
    ))


class QuarantineRow(QFrame):
    restore_clicked = pyqtSignal(int)
    delete_clicked = pyqtSignal(int)

    def __init__(self, record: QuarantineRecord, parent=None):
        super().__init__(parent)
        self.record_id = record.id
        self._name_text = record.filename
        self._details_text = (
            f"{record.malware_name or 'Unknown Malware'}  ·  "
            f"{record.size_kb:.1f} KB  ·  Quarantined {record.quarantined_at}"
        )
        self._path_text = record.original_path
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(0)
        self.setMinimumHeight(86)
        self.setStyleSheet(f"""
            QFrame#QuarantineRow {{ background: {BG_CARD}; border: 1px solid {BORDER_COLOR}; border-radius: 10px; }}
            QFrame#QuarantineRow:hover {{ border: 1px solid {ACCENT_CYAN}; }}
        """)
        self.setObjectName("QuarantineRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 9, 14, 9)
        layout.setSpacing(10)

        icon = QLabel("⚠️")
        icon.setFont(QFont("Segoe UI Emoji", 18))
        icon.setFixedWidth(30)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info = QVBoxLayout()
        info.setSpacing(3)
        info_widget = QWidget()
        info_widget.setLayout(info)
        info_widget.setMinimumWidth(0)
        info_widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self.name_lbl = QLabel(self._name_text)
        self.name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; border: none; background: transparent;")
        self.name_lbl.setMinimumWidth(0)
        self.name_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.name_lbl.setToolTip(self._name_text)

        self.details_lbl = QLabel(self._details_text)
        self.details_lbl.setFont(QFont("Segoe UI", 9))
        self.details_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none; background: transparent;")
        self.details_lbl.setMinimumWidth(0)
        self.details_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.details_lbl.setToolTip(self._details_text)

        self.path_lbl = QLabel(self._path_text)
        self.path_lbl.setFont(QFont("Segoe UI", 8))
        self.path_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none; background: transparent;")
        self.path_lbl.setMinimumWidth(0)
        self.path_lbl.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.path_lbl.setToolTip(self._path_text)

        info.addWidget(self.name_lbl)
        info.addWidget(self.details_lbl)
        info.addWidget(self.path_lbl)

        self.restore_btn = QPushButton("↩ Restore")
        self.restore_btn.setFixedSize(94, 32)
        self.restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.restore_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {ACCENT_AMBER}; border: 1px solid rgba(255,176,32,100); border-radius: 7px; font-size: 11px; font-weight: 600; }}
            QPushButton:hover {{ background: rgba(255,176,32,18); }}
        """)
        self.restore_btn.clicked.connect(lambda: self.restore_clicked.emit(self.record_id))

        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.setFixedSize(94, 32)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {ACCENT_RED}; border: 1px solid rgba(255,68,102,100); border-radius: 7px; font-size: 11px; font-weight: 600; }}
            QPushButton:hover {{ background: rgba(255,68,102,18); }}
        """)
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.record_id))

        layout.addWidget(icon)
        layout.addWidget(info_widget, 1)
        layout.addWidget(self.restore_btn)
        layout.addWidget(self.delete_btn)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Elide long text instead of allowing it to expand the scroll area.
        for label, text in (
            (self.name_lbl, self._name_text),
            (self.details_lbl, self._details_text),
            (self.path_lbl, self._path_text),
        ):
            _elide(label, text)


class QuarantinePage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setStyleSheet(f"QScrollArea {{ background: {BG_BASE}; border: none; }}")

        self.manager = QuarantineManager()
        self._restored_count = 0
        self._all_records = []

        self.content = QWidget()
        self.content.setObjectName("QuarantineContent")
        self.content.setMinimumWidth(0)
        self.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.content.setStyleSheet(f"QWidget#QuarantineContent {{ background: {BG_BASE}; }}")
        self.setWidget(self.content)

        self._root = QVBoxLayout(self.content)
        self._root.setContentsMargins(24, 22, 24, 22)
        self._root.setSpacing(18)

        self._build_header()
        self._build_stats()
        self._build_list()
        self.refresh()

    def _build_header(self):
        header = QHBoxLayout()
        header.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Quarantine")
        title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent;")
        subtitle = QLabel("Files isolated because they were identified as threats")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        subtitle.setWordWrap(True)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search quarantined files...")
        self.search_box.setMinimumWidth(120)
        self.search_box.setMaximumWidth(300)
        self.search_box.setFixedHeight(38)
        self.search_box.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{ background: {BG_CARD}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 7px 10px; font-size: 11px; }}
            QLineEdit:focus {{ border: 1px solid {ACCENT_CYAN}; }}
        """)
        self.search_box.textChanged.connect(self.refresh)

        clear_btn = QPushButton("🗑 Clear All")
        clear_btn.setFixedSize(112, 38)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {ACCENT_RED}; border: 1px solid rgba(255,68,102,100); border-radius: 8px; font-size: 11px; font-weight: 600; }}
            QPushButton:hover {{ background: rgba(255,68,102,18); }}
        """)
        clear_btn.clicked.connect(self._on_clear_all)

        header.addLayout(title_col, 1)
        header.addWidget(self.search_box, 0)
        header.addWidget(clear_btn, 0)
        self._root.addLayout(header)

    def _build_stats(self):
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        self._stat_cards = []

        def stat_card(icon, value, label, accent):
            card = QFrame()
            card.setMinimumWidth(0)
            card.setMinimumHeight(88)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            card.setStyleSheet(f"QFrame {{ background: {BG_CARD}; border: 1px solid {BORDER_COLOR}; border-radius: 12px; }}")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(15, 10, 15, 10)
            cl.setSpacing(4)
            top = QHBoxLayout()
            top.setSpacing(8)
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("Segoe UI Emoji", 16))
            icon_lbl.setStyleSheet("border: none; background: transparent;")
            value_lbl = QLabel(value)
            value_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            value_lbl.setStyleSheet(f"color: {accent}; border: none; background: transparent;")
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            value_lbl.setMinimumWidth(0)
            top.addWidget(icon_lbl)
            top.addStretch(1)
            top.addWidget(value_lbl)
            text_lbl = QLabel(label)
            text_lbl.setFont(QFont("Segoe UI", 9))
            text_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; border: none; background: transparent;")
            cl.addLayout(top)
            cl.addWidget(text_lbl)
            return card, value_lbl

        cards = [
            stat_card("🔒", "0", "Files Quarantined", ACCENT_RED),
            stat_card("💾", "0 KB", "Total Size", ACCENT_AMBER),
            stat_card("⚠️", "0", "Threats Blocked", ACCENT_CYAN),
            stat_card("✅", "0", "Restored Safely", ACCENT_GREEN),
        ]
        self.stat_total, self.stat_size, self.stat_threats, self.stat_safe = [item[1] for item in cards]
        for index, (card, _) in enumerate(cards):
            grid.addWidget(card, index // 2, index % 2)
            grid.setColumnStretch(index % 2, 1)
        self._root.addLayout(grid)

    def _build_list(self):
        self._section_lbl = QLabel("Quarantined Files")
        self._section_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._section_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; background: transparent; padding-top: 4px;")
        self._root.addWidget(self._section_lbl)

        self._list_container = QVBoxLayout()
        self._list_container.setSpacing(9)
        self._list_container.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._list_widget = QWidget()
        self._list_widget.setMinimumWidth(0)
        self._list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._list_widget.setLayout(self._list_container)
        self._root.addWidget(self._list_widget)
        self._root.addStretch(1)

    def refresh(self, *_):
        """Reload records and filter the visible list; stats reflect all quarantined files."""
        all_records = self.manager.list_files()
        self._all_records = all_records
        query = self.search_box.text().lower().strip()
        records = all_records
        if query:
            records = [r for r in all_records if (
                query in r.filename.lower()
                or query in (r.malware_name or "").lower()
                or query in r.original_path.lower()
            )]

        while self._list_container.count():
            item = self._list_container.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not records:
            message = "No matching quarantined files." if query else "✓  Quarantine is empty — no threats have been isolated."
            self._empty_lbl = QLabel(message)
            self._empty_lbl.setFont(QFont("Segoe UI", 10))
            self._empty_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; padding: 26px 8px; background: transparent;")
            self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._empty_lbl.setWordWrap(True)
            self._list_container.addWidget(self._empty_lbl)
        else:
            for record in records:
                row = QuarantineRow(record)
                row.restore_clicked.connect(self._on_restore)
                row.delete_clicked.connect(self._on_delete)
                self._list_container.addWidget(row)

        total = len(all_records)
        size_bytes = self.manager.total_size_bytes()
        if size_bytes >= 1024 * 1024:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            size_str = f"{size_bytes / 1024:.1f} KB"
        self.stat_total.setText(str(total))
        self.stat_size.setText(size_str)
        self.stat_threats.setText(str(total))
        self.stat_safe.setText(str(self._restored_count))
        self._section_lbl.setText(f"Quarantined Files  —  {len(records)} shown / {total} isolated" if query else f"Quarantined Files  —  {total} isolated")

    def add_from_file_result(self, file_result):
        """Quarantine a detected file and log the action only after success."""
        threat = file_result.threat
        if not threat or threat.verdict not in ("THREAT", "SUSPICIOUS"):
            return
        try:
            record = self.manager.quarantine_file(
                path=file_result.path,
                malware_name=threat.malware_name or "Suspicious file",
                sha256=file_result.sha256 or "",
            )
            from threat_log.threat_log import ThreatLog
            ThreatLog().add_log(
                threat_name=threat.malware_name or "Suspicious file",
                file_path=file_result.path,
                sha256=file_result.sha256 or "",
                source=threat.source or "unknown",
                action="Quarantined",
            )
            self.refresh()
            print(f"[quarantine] File quarantined: {record.quarantine_path}")
        except Exception as exc:
            print(f"[quarantine] Failed to quarantine {file_result.path}: {exc}")

    def _on_restore(self, record_id: int):
        reply = QMessageBox.question(
            self, "Restore File",
            "Are you sure you want to restore this file to its original location?\n\n"
            "Only do this if you are certain it is a false positive.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            restored_path = self.manager.restore_file(record_id)
            self._restored_count += 1
            self.refresh()
            QMessageBox.information(self, "File Restored", f"File restored to:\n{restored_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Restore Failed", str(exc))

    def _on_delete(self, record_id: int):
        reply = QMessageBox.question(
            self, "Delete Permanently",
            "This will permanently delete the quarantined file. This cannot be undone.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            self.manager.delete_file(record_id)
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Delete Failed", str(exc))

    def _on_clear_all(self):
        count = self.manager.count()
        if count == 0:
            return
        reply = QMessageBox.question(
            self, "Clear All Quarantine",
            f"This will permanently delete all {count} quarantined file(s).\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            deleted = self.manager.clear_all()
            self.refresh()
            QMessageBox.information(self, "Cleared", f"{deleted} file(s) permanently deleted.")
        except Exception as exc:
            QMessageBox.critical(self, "Clear Failed", str(exc))
