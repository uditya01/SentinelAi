"""
gui/threat_log_page.py

Scan History page — shows every past scan as a collapsible session card.
Each card shows: mode, date, file count, threats, duration, status.
Expanding a card shows the threat files found in that session.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from threat_log.threat_log import ThreatLog

# ─── Colour tokens ────────────────────────────────────────────────────────────
BG_BASE        = "#0A0E1A"
BG_CARD        = "#0D1827"
BG_EXPANDED    = "#0A1520"
ACCENT_CYAN    = "#00D4FF"
ACCENT_GREEN   = "#00FF88"
ACCENT_RED     = "#FF4466"
ACCENT_AMBER   = "#FFB020"
TEXT_PRIMARY   = "#E8EEF8"
TEXT_SECONDARY = "#8892A4"
BORDER_COLOR   = "#1A2540"


# ─── Threat file row (inside expanded session) ────────────────────────────────
class ThreatFileRow(QFrame):
    def __init__(self, filename, malware_name, verdict, path, parent=None):
        super().__init__(parent)
        color = ACCENT_RED if verdict == "THREAT" else ACCENT_AMBER
        self.setFixedHeight(52)
        self.setStyleSheet(f"""
            ThreatFileRow {{
                background: rgba(255,68,102,6);
                border: 1px solid rgba(255,68,102,25);
                border-radius: 8px;
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet(f"color:{color}; font-size:9px;")
        dot.setFixedWidth(14)

        info = QVBoxLayout()
        info.setSpacing(2)
        nl = QLabel(filename)
        nl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        nl.setStyleSheet(f"color:{TEXT_PRIMARY};")
        pl = QLabel(path)
        pl.setFont(QFont("Segoe UI", 8))
        pl.setStyleSheet(f"color:{TEXT_SECONDARY};")
        info.addWidget(nl)
        info.addWidget(pl)

        badge = QLabel(verdict)
        badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        badge.setFixedSize(90, 20)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(f"""
            color:{color};
            background: rgba(0,0,0,40);
            border: 1px solid {color};
            border-radius: 4px;
        """)

        ml = QLabel(malware_name or "Unknown Malware")
        ml.setFont(QFont("Segoe UI", 9))
        ml.setStyleSheet(f"color:{color};")
        ml.setFixedWidth(180)
        ml.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(dot)
        layout.addLayout(info, 1)
        layout.addWidget(badge)
        layout.addWidget(ml)


# ─── Session Card ─────────────────────────────────────────────────────────────
class SessionCard(QFrame):
    delete_clicked = pyqtSignal(int)

    def __init__(self, session: ScanSession, db: ScanHistoryDB, parent=None):
        super().__init__(parent)
        self.session = session
        self.db = db
        self._expanded = False
        self._detail_widget = None

        self.setStyleSheet(f"""
            SessionCard {{
                background: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            }}
        """)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        self._build_header()

    def _build_header(self):
        s = self.session

        # Status colours
        status_colors = {
            "CLEAN":         ACCENT_GREEN,
            "THREATS FOUND": ACCENT_RED,
            "ABORTED":       ACCENT_AMBER,
        }
        status_color = status_colors.get(s.status_label, ACCENT_CYAN)

        mode_icons = {"quick": "⚡", "full": "◉", "custom": "☰"}
        mode_icon  = mode_icons.get(s.mode, "⟳")

        header = QFrame()
        header.setStyleSheet("QFrame { background: transparent; border: none; }")
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 16, 20, 16)
        hl.setSpacing(16)

        # Mode icon + scan type
        icon_lbl = QLabel(mode_icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 20))
        icon_lbl.setFixedWidth(32)

        # Main info column
        info = QVBoxLayout()
        info.setSpacing(4)

        title_row = QHBoxLayout()
        mode_lbl = QLabel(f"{s.mode.capitalize()} Scan")
        mode_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        mode_lbl.setStyleSheet(f"color:{TEXT_PRIMARY};")
        date_lbl = QLabel(s.started_at)
        date_lbl.setFont(QFont("Segoe UI", 9))
        date_lbl.setStyleSheet(f"color:{TEXT_SECONDARY};")
        title_row.addWidget(mode_lbl)
        title_row.addSpacing(12)
        title_row.addWidget(date_lbl)
        title_row.addStretch()

        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)
        for label, value in [
            ("Files",    f"{s.scanned_files:,}"),
            ("Threats",  str(s.threats_found)),
            ("Size",     f"{s.total_mb:.1f} MB"),
            ("Duration", s.duration),
        ]:
            col = QVBoxLayout()
            col.setSpacing(1)
            vl = QLabel(value)
            vl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            vl.setStyleSheet(f"color:{'#FF4466' if label == 'Threats' and s.threats_found > 0 else ACCENT_CYAN};")
            ll = QLabel(label)
            ll.setFont(QFont("Segoe UI", 8))
            ll.setStyleSheet(f"color:{TEXT_SECONDARY};")
            col.addWidget(vl)
            col.addWidget(ll)
            stats_row.addLayout(col)

        info.addLayout(title_row)
        info.addLayout(stats_row)

        # Right: status badge + expand + delete
        right = QVBoxLayout()
        right.setSpacing(8)
        right.setAlignment(Qt.AlignmentFlag.AlignTop)

        status_badge = QLabel(s.status_label)
        status_badge.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        status_badge.setFixedHeight(22)
        status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_badge.setStyleSheet(f"""
            color: {status_color};
            background: rgba(0,0,0,40);
            border: 1px solid {status_color};
            border-radius: 5px;
            padding: 0 10px;
        """)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._expand_btn = QPushButton("▼  Details")
        self._expand_btn.setFixedSize(100, 28)
        self._expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._expand_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color:{ACCENT_CYAN};
                border: 1px solid rgba(0,212,255,50); border-radius:6px;
                font-size:10px; font-weight:600;
            }}
            QPushButton:hover {{ background:rgba(0,212,255,10); }}
        """)
        self._expand_btn.clicked.connect(self._toggle_expand)

        del_btn = QPushButton("🗑")
        del_btn.setFixedSize(32, 28)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color:{ACCENT_RED};
                border: 1px solid rgba(255,68,102,40); border-radius:6px;
                font-size:12px;
            }}
            QPushButton:hover {{ background:rgba(255,68,102,12); }}
        """)
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(self.session.id))

        btn_row.addWidget(self._expand_btn)
        btn_row.addWidget(del_btn)

        right.addWidget(status_badge)
        right.addLayout(btn_row)

        hl.addWidget(icon_lbl)
        hl.addLayout(info, 1)
        hl.addLayout(right)

        self._outer.addWidget(header)

    def _toggle_expand(self):
        self._expanded = not self._expanded

        if self._expanded:
            self._expand_btn.setText("▲  Hide")
            self._show_details()
        else:
            self._expand_btn.setText("▼  Details")
            if self._detail_widget:
                self._detail_widget.setVisible(False)

    def _show_details(self):
        if self._detail_widget:
            self._detail_widget.setVisible(True)
            return

        # Load files from DB
        threats = self.db.get_threats(self.session.id)

        detail = QFrame()
        detail.setStyleSheet(f"""
            QFrame {{
                background: {BG_EXPANDED};
                border: none;
                border-top: 1px solid {BORDER_COLOR};
                border-radius: 0px;
            }}
        """)
        dl = QVBoxLayout(detail)
        dl.setContentsMargins(20, 14, 20, 14)
        dl.setSpacing(8)

        if not threats:
            no_threat = QLabel("✓  No threats found in this scan session.")
            no_threat.setFont(QFont("Segoe UI", 10))
            no_threat.setStyleSheet(f"color:{ACCENT_GREEN}; padding: 8px 0;")
            dl.addWidget(no_threat)
        else:
            lbl = QLabel(f"Threats detected ({len(threats)})")
            lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color:{ACCENT_RED};")
            dl.addWidget(lbl)
            for f in threats:
                row = ThreatFileRow(f.filename, f.malware_name, f.verdict, f.path)
                dl.addWidget(row)

        self._detail_widget = detail
        self._outer.addWidget(detail)


# ─── Threat Log / Scan History Page ──────────────────────────────────────────
class ThreatLogPage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.db = ThreatLog()

        cw = QWidget()
        self.setWidget(cw)
        self._root = QVBoxLayout(cw)
        self._root.setContentsMargins(32, 28, 32, 28)
        self._root.setSpacing(20)

        self._build()
        self.refresh()

    def _build(self):
        # Header
        hdr = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(3)
        t = QLabel("Scan History")
        t.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        t.setStyleSheet(f"color:{TEXT_PRIMARY};")
        s = QLabel("Complete record of all past scan sessions and threats detected")
        s.setFont(QFont("Segoe UI", 10))
        s.setStyleSheet(f"color:{TEXT_SECONDARY};")
        title_col.addWidget(t)
        title_col.addWidget(s)

        clear_btn = QPushButton("🗑  Clear History")
        clear_btn.setFixedHeight(38)
        clear_btn.setFixedWidth(130)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background:transparent; color:{ACCENT_RED};
                border:1px solid rgba(255,68,102,60); border-radius:9px;
                font-size:12px; font-weight:600;
            }}
            QPushButton:hover {{ background:rgba(255,68,102,12); }}
        """)
        clear_btn.clicked.connect(self._on_clear)

        hdr.addLayout(title_col)
        hdr.addStretch()
        hdr.addWidget(clear_btn)
        self._root.addLayout(hdr)

        # Summary stat cards
        sr = QHBoxLayout()
        sr.setSpacing(14)

        def stat_card(icon, value, label, accent):
            card = QFrame()
            card.setFixedHeight(90)
            card.setStyleSheet(f"""
                QFrame {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(18, 12, 18, 12)
            cl.setSpacing(4)
            top = QHBoxLayout()
            il = QLabel(icon)
            il.setFont(QFont("Segoe UI Emoji", 16))
            vl = QLabel(value)
            vl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
            vl.setStyleSheet(f"color:{accent};")
            top.addWidget(il)
            top.addStretch()
            top.addWidget(vl)
            ll = QLabel(label)
            ll.setFont(QFont("Segoe UI", 9))
            ll.setStyleSheet(f"color:{TEXT_SECONDARY};")
            cl.addLayout(top)
            cl.addWidget(ll)
            return card, vl

        c1, self.stat_sessions = stat_card("📋", "0", "Total Scans",      ACCENT_CYAN)
        c2, self.stat_threats  = stat_card("⚠️", "0", "Total Threats",    ACCENT_RED)
        c3, self.stat_files    = stat_card("🗂", "0", "Files Scanned",    ACCENT_AMBER)
        c4, self.stat_clean    = stat_card("✅", "0", "Clean Scans",      ACCENT_GREEN)
        for c in [c1, c2, c3, c4]:
            sr.addWidget(c)
        self._root.addLayout(sr)

        # Section label
        self._section_lbl = QLabel("Recent Sessions")
        self._section_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._section_lbl.setStyleSheet(f"color:{TEXT_PRIMARY}; padding-top:8px;")
        self._root.addWidget(self._section_lbl)

        # Session list
        self._list_layout = QVBoxLayout()
        self._list_layout.setSpacing(10)
        self._list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._empty_lbl = QLabel("📋  No scan sessions yet.  Run a Quick Scan to get started.")
        self._empty_lbl.setFont(QFont("Segoe UI", 10))
        self._empty_lbl.setStyleSheet(f"color:{TEXT_SECONDARY}; padding:40px 0;")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._list_layout.addWidget(self._empty_lbl)

        wrapper = QWidget()
        wrapper.setLayout(self._list_layout)
        self._root.addWidget(wrapper)
        self._root.addStretch()

    def refresh(self):
        """Reload all sessions from DB and redraw."""
        logs = self.db.get_logs()

        # Clear list
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not sessions:
            self._empty_lbl = QLabel("📋  No scan sessions yet.  Run a Quick Scan to get started.")
            self._empty_lbl.setFont(QFont("Segoe UI", 10))
            self._empty_lbl.setStyleSheet(f"color:{TEXT_SECONDARY}; padding:40px 0;")
            self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._list_layout.addWidget(self._empty_lbl)
        else:
            for session in sessions:
                card = SessionCard(session, self.db)
                card.delete_clicked.connect(self._on_delete_session)
                self._list_layout.addWidget(card)

        # Update stat cards
        total_sessions = self.db.total_sessions()
        total_threats  = self.db.total_threats_ever()
        total_files    = sum(s.scanned_files for s in sessions)
        clean_scans    = sum(1 for s in sessions if s.threats_found == 0 and not s.aborted)

        self.stat_sessions.setText(str(total_sessions))
        self.stat_threats.setText(str(total_threats))
        self.stat_files.setText(f"{total_files:,}")
        self.stat_clean.setText(str(clean_scans))
        self._section_lbl.setText(f"Recent Sessions  —  {total_sessions} total")

    def add_session(self, scan_result, mode: str, started_at: str):
        """Called from main_window after a scan finishes."""
        self.db.save_session(scan_result, mode, started_at)
        self.refresh()

    def _on_delete_session(self, session_id: int):
        reply = QMessageBox.question(
            self, "Delete Session",
            "Remove this scan session from history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_session(session_id)
            self.refresh()

    def _on_clear(self):
        count = self.db.total_sessions()
        if count == 0:
            return
        reply = QMessageBox.question(
            self, "Clear History",
            f"Permanently delete all {count} scan session(s) from history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.clear_all()
            self.refresh()