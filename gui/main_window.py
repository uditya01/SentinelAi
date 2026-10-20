import sys
import math
import os
from unittest import result
from database import db
from gui.quarantine_page_enhanced import QuarantinePage
from gui.protection_history_page import ProtectionHistoryPage
from reports.report_generator import ReportGenerator
from datetime import datetime
from gui.reports_page import ReportsPage
from gui.damage_assessment_page import DamageAssessmentPage
from threat_log.threat_log import ThreatLog

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QProgressBar, QScrollArea,
    QStackedWidget, QLineEdit, QSlider, QCheckBox, QComboBox,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPointF, pyqtSignal,QSettings
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush,
    QLinearGradient, QRadialGradient, QPainterPath
)

from scanner import ScanWorker

try:
    from database.db import HashDatabase
    _db = HashDatabase()
    _db.setup()
except Exception:
    _db = None

APP_VERSION = "4.1.0"

BG_BASE        = "#0A0E1A"
BG_CARD        = "#0D1827"
BG_SIDEBAR     = "#080C17"
ACCENT_CYAN    = "#00D4FF"
ACCENT_GREEN   = "#00FF88"
ACCENT_RED     = "#FF4466"
ACCENT_AMBER   = "#FFB020"
TEXT_PRIMARY   = "#E8EEF8"
TEXT_SECONDARY = "#8892A4"
BORDER_COLOR   = "#1A2540"

class ShieldWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self._pulse = 0.0
        self._rotation = 0.0
        self._ring2 = 0.0
        self.protected = True
        self._animation_timer = QTimer(self)
        self._animation_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._animation_timer.timeout.connect(self._tick)
        self._animation_timer.start(33) 
    def _tick(self):
        self._pulse = (self._pulse + 0.03) % (2 * math.pi)
        self._rotation = (self._rotation + 0.4) % 360
        self._ring2 = (self._ring2 - 0.6) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        pv = (math.sin(self._pulse) + 1) / 2

        for i in range(5, 0, -1):
            alpha = int(12 * pv * i)
            color = QColor(0, 212, 255, alpha) if self.protected else QColor(255, 68, 102, alpha)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(QPointF(cx, cy), 95 + i * 4, 95 + i * 4)

        p.save()
        p.translate(cx, cy)
        p.rotate(self._rotation)
        pen = QPen(QColor(0, 212, 255, 80), 1.5, Qt.PenStyle.DashLine)
        pen.setDashPattern([4, 6])
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), 90, 90)
        p.restore()

        p.save()
        p.translate(cx, cy)
        p.rotate(self._ring2)
        pen2 = QPen(QColor(0, 255, 136, 50), 1, Qt.PenStyle.DotLine)
        pen2.setDashPattern([2, 8])
        p.setPen(pen2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), 78, 78)
        p.restore()

        grad = QRadialGradient(cx, cy - 20, 65)
        if self.protected:
            grad.setColorAt(0, QColor("#0D2540"))
            grad.setColorAt(1, QColor("#060C18"))
        else:
            grad.setColorAt(0, QColor("#250D18"))
            grad.setColorAt(1, QColor("#180608"))
        cc = QColor(ACCENT_CYAN if self.protected else ACCENT_RED)
        cc.setAlpha(120)
        p.setPen(QPen(cc, 1.5))
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), 65, 65)

        sc = QColor(ACCENT_CYAN if self.protected else ACCENT_RED)
        sc.setAlpha(int(200 + 55 * pv))
        path = QPainterPath()
        s = 36
        path.moveTo(cx, cy - s)
        path.cubicTo(cx+s*1.1, cy-s*0.9, cx+s*1.2, cy+s*0.2, cx, cy+s*1.15)
        path.cubicTo(cx-s*1.2, cy+s*0.2, cx-s*1.1, cy-s*0.9, cx, cy-s)
        sg = QLinearGradient(cx, cy - s, cx, cy + s)
        sg.setColorAt(0, QColor(ACCENT_CYAN if self.protected else ACCENT_RED))
        sg.setColorAt(1, QColor(0, 180, 220, 180) if self.protected else QColor(220, 40, 80, 180))
        p.setPen(QPen(sc, 2))
        p.setBrush(QBrush(sg))
        p.drawPath(path)

        p.setPen(QPen(QColor("#FFFFFF"), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if self.protected:
            p.drawLine(int(cx-12), int(cy+2),  int(cx-2),  int(cy+12))
            p.drawLine(int(cx-2),  int(cy+12), int(cx+14), int(cy-8))
        else:
            p.drawLine(int(cx-10), int(cy-10), int(cx+10), int(cy+10))
            p.drawLine(int(cx+10), int(cy-10), int(cx-10), int(cy+10))
        p.end()


class StatCard(QFrame):
    def __init__(self, icon, value, label, accent=ACCENT_CYAN, parent=None):
        super().__init__(parent)
        self.accent = QColor(accent)
        self.setFixedHeight(100)
        self.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred
        )
        self.setStyleSheet(f"""
            StatCard {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)
        top = QHBoxLayout()
        il = QLabel(icon)
        il.setFont(QFont("Segoe UI Emoji", 18))
        self.val_lbl = QLabel(value)
        self.val_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self.val_lbl.setStyleSheet(f"color:{accent};")
        top.addWidget(il)
        top.addStretch()
        top.addWidget(self.val_lbl)
        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet(f"color:{TEXT_SECONDARY};")
        layout.addLayout(top)
        layout.addWidget(lbl)

    def set_value(self, v):
        self.val_lbl.setText(v)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QPen(self.accent, 2))
        p.drawLine(0, self.height()-1, int(self.width()*0.4), self.height()-1)
        p.end()


class SidebarButton(QPushButton):
    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self._icon = icon
        self._label = text
        self._active = False
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self._update_style()

    def set_active(self, val):
        self._active = val
        self.setChecked(val)
        self._update_style()

    def _update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba(0,212,255,25),stop:1 rgba(0,212,255,5));
                    border:none; border-left:3px solid {ACCENT_CYAN};
                    border-radius:0px; color:{ACCENT_CYAN};
                    font-size:13px; font-weight:600;
                    text-align:left; padding-left:20px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:transparent; border:none;
                    border-left:3px solid transparent;
                    border-radius:0px; color:{TEXT_SECONDARY};
                    font-size:13px; text-align:left; padding-left:20px;
                }}
                QPushButton:hover {{
                    background:rgba(0,212,255,8); color:{TEXT_PRIMARY};
                    border-left:3px solid rgba(0,212,255,80);
                }}
            """)
        self.setText(f"  {self._icon}   {self._label}")

class ScanButton(QPushButton):
    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0099BB,stop:1 #00D4FF);
                    color:#fff; border:none; border-radius:10px;
                    font-size:13px; font-weight:700; letter-spacing:1px;
                }}
                QPushButton:hover {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00BBDD,stop:1 #33DDFF); }}
                QPushButton:pressed {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #007799,stop:1 #00AABB); }}
                QPushButton:disabled {{ background:rgba(0,212,255,30); color:rgba(255,255,255,60); }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background:transparent; color:{ACCENT_CYAN};
                    border:1px solid rgba(0,212,255,60); border-radius:10px;
                    font-size:13px; font-weight:600;
                }}
                QPushButton:hover {{ background:rgba(0,212,255,12); border:1px solid rgba(0,212,255,120); }}
                QPushButton:pressed {{ background:rgba(0,212,255,20); }}
                QPushButton:disabled {{ color:rgba(0,212,255,40); border-color:rgba(0,212,255,20); }}
            """)

class ThreatItem(QFrame):
    def __init__(self, name, threat_type, severity, time_ago, parent=None):
        super().__init__(parent)
        sev_colors = {"HIGH": ACCENT_RED, "MED": ACCENT_AMBER, "LOW": ACCENT_CYAN,
                      "THREAT": ACCENT_RED, "SUSPICIOUS": ACCENT_AMBER}
        color = sev_colors.get(severity, ACCENT_CYAN)
        self.setFixedHeight(64)
        self.setStyleSheet(f"""
            ThreatItem {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:8px; }}
            ThreatItem:hover {{ border:1px solid rgba(0,212,255,40); }}
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        dot = QLabel("●")
        dot.setStyleSheet(f"color:{color}; font-size:10px;")
        dot.setFixedWidth(16)
        info = QVBoxLayout()
        info.setSpacing(2)
        nl = QLabel(name)
        nl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        nl.setStyleSheet(f"color:{TEXT_PRIMARY};")
        tl = QLabel(threat_type)
        tl.setFont(QFont("Segoe UI", 9))
        tl.setStyleSheet(f"color:{TEXT_SECONDARY};")
        info.addWidget(nl)
        info.addWidget(tl)
        sl = QLabel(severity)
        sl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        sl.setFixedSize(80, 20)
        sl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl.setStyleSheet(f"color:{color}; background:rgba(0,0,0,40); border:1px solid {color}; border-radius:4px;")
        tl2 = QLabel(time_ago)
        tl2.setFont(QFont("Segoe UI", 8))
        tl2.setStyleSheet(f"color:{TEXT_SECONDARY};")
        tl2.setFixedWidth(70)
        tl2.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(dot)
        layout.addLayout(info, 1)
        layout.addWidget(sl)
        layout.addSpacing(10)
        layout.addWidget(tl2)


class ScanProgress(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(90)
        self.setStyleSheet(f"ScanProgress {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(8)
        top = QHBoxLayout()
        self.status_lbl = QLabel("System Idle  —  Ready to scan")
        self.status_lbl.setFont(QFont("Segoe UI", 10))
        self.status_lbl.setStyleSheet(f"color:{TEXT_SECONDARY};")
        self.pct_lbl = QLabel("")
        self.pct_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.pct_lbl.setStyleSheet(f"color:{ACCENT_CYAN};")
        top.addWidget(self.status_lbl)
        top.addStretch()
        top.addWidget(self.pct_lbl)
        self.bar = QProgressBar()
        self.bar.setFixedHeight(6)
        self.bar.setTextVisible(False)
        self.bar.setValue(0)
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background:rgba(255,255,255,8); border-radius:3px; border:none; }}
            QProgressBar::chunk {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0099BB,stop:1 #00D4FF); border-radius:3px; }}
        """)
        layout.addLayout(top)
        layout.addWidget(self.bar)

    def set_status(self, text, color=TEXT_SECONDARY):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color:{color};")

    def set_percent(self, value):
        self.bar.setValue(value)
        self.pct_lbl.setText(f"{value}%")
    def reset(self):
        self.bar.setValue(0)
        self.pct_lbl.setText("")
        self.set_status("System Idle  —  Ready to scan", TEXT_SECONDARY)



def _page_header(title, subtitle):
    """Reusable page header."""
    w = QWidget()
    l = QVBoxLayout(w)
    l.setContentsMargins(0, 0, 0, 0)
    l.setSpacing(3)
    t = QLabel(title)
    t.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
    t.setStyleSheet(f"color:{TEXT_PRIMARY};")
    s = QLabel(subtitle)
    s.setFont(QFont("Segoe UI", 10))
    s.setStyleSheet(f"color:{TEXT_SECONDARY};")
    l.addWidget(t)
    l.addWidget(s)
    return w


def _section_title(text):
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
    lbl.setStyleSheet(f"color:{TEXT_PRIMARY}; padding-top:8px;")
    return lbl


def _divider():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"background:{BORDER_COLOR}; max-height:1px;")
    return line


def _card(content_widget, padding=(20, 16, 20, 16)):
    outer = QFrame()
    outer.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}")
    l = QVBoxLayout(outer)
    l.setContentsMargins(*padding)
    l.addWidget(content_widget)
    return outer


# ─── Page: Dashboard ──────────────────────────────────────────────────────────
class DashboardPage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        cw = QWidget()
        self.setWidget(cw)
        self._layout = QVBoxLayout(cw)
        self._layout.setContentsMargins(32, 28, 32, 28)
        self._layout.setSpacing(24)
        self._build()

    def _build(self):
        cl = self._layout

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(_page_header(
            "Security Overview",
            f"{datetime.now().strftime('%A, %d %b %Y')}  ·  Real-time protection enabled"
        ))
        hdr.addStretch()
        nb = QPushButton("🔔")
        nb.setFixedSize(40, 40)
        nb.setStyleSheet(f"""
            QPushButton {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR};
                border-radius:10px; font-size:16px; color:{TEXT_SECONDARY}; }}
            QPushButton:hover {{ border-color:{ACCENT_CYAN}; color:{ACCENT_CYAN}; }}
        """)
        hdr.addWidget(nb)
        cl.addLayout(hdr)

        # Hero row
        hero = QHBoxLayout()
        hero.setSpacing(24)

        # Shield panel
        sp = QFrame()
        sp.setMinimumWidth(200)
        sp.setMaximumWidth(280)
        sp.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred
        )
        sp.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:16px; }}")
        spl = QVBoxLayout(sp)
        spl.setContentsMargins(20, 20, 20, 20)
        spl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shield_widget = ShieldWidget()
        spl.addWidget(self.shield_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        self.shield_status_lbl = QLabel("PROTECTED")
        self.shield_status_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.shield_status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shield_status_lbl.setStyleSheet(f"color:{ACCENT_GREEN}; letter-spacing:3px;")
        self.threat_count_lbl = QLabel("0 threats detected")
        self.threat_count_lbl.setFont(QFont("Segoe UI", 9))
        self.threat_count_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.threat_count_lbl.setStyleSheet(f"color:{TEXT_SECONDARY};")
        spl.addWidget(self.shield_status_lbl)
        spl.addSpacing(2)
        spl.addWidget(self.threat_count_lbl)

        # Right column
        rc = QVBoxLayout()
        rc.setSpacing(16)

        # Stat cards
        sr = QHBoxLayout()
        sr.setSpacing(14)
        self.card_files    = StatCard("🗂", "0",  "Files Scanned",  ACCENT_CYAN)
        self.card_threats  = StatCard("🛡", "0",  "Threats Found",  ACCENT_RED)
        self.card_lastscan = StatCard("⚡", "—",  "Last Scan",      ACCENT_AMBER)
        self.card_web      = StatCard("🌐", "ON", "Web Protection", ACCENT_GREEN)
        for card in [
            self.card_files,
            self.card_threats,
            self.card_lastscan,
            self.card_web,
        ]:
            card.setMinimumWidth(0)
            card.setSizePolicy(
                QSizePolicy.Policy.Ignored,
                QSizePolicy.Policy.Preferred
            )
            sr.addWidget(card, 1)
        
        rc.addLayout(sr)

        self.scan_progress = ScanProgress()
        rc.addWidget(self.scan_progress)

        # Scan buttons
        br = QHBoxLayout()
        br.setSpacing(12)
        self.quick_btn  = ScanButton("⚡  QUICK SCAN", primary=True)
        self.full_btn   = ScanButton("◉  FULL SCAN",  primary=False)
        self.cancel_btn = ScanButton("✕  CANCEL",     primary=False)
        self.cancel_btn.setEnabled(False)
        br.addWidget(self.quick_btn, 2)
        br.addWidget(self.full_btn,  2)
        br.addWidget(self.cancel_btn, 1)
        rc.addLayout(br)

        hero.addWidget(sp)
        hero.addLayout(rc, 1)
        cl.addLayout(hero)

        # Threat activity section
        th_hdr = QHBoxLayout()
        self.threats_title = QLabel("Threat Activity  —  0 found")
        self.threats_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.threats_title.setStyleSheet(f"color:{TEXT_PRIMARY};")
        th_hdr.addWidget(self.threats_title)
        th_hdr.addStretch()
        cl.addLayout(th_hdr)

        self.threat_list_layout = QVBoxLayout()
        self.threat_list_layout.setSpacing(8)
        self.threat_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.no_threats_lbl = QLabel("✓  No threats detected yet.  Run a scan to check your system.")
        self.no_threats_lbl.setFont(QFont("Segoe UI", 10))
        self.no_threats_lbl.setStyleSheet(f"color:{TEXT_SECONDARY}; padding:20px 0;")
        self.no_threats_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.threat_list_layout.addWidget(self.no_threats_lbl)

        tc = QWidget()
        tc.setLayout(self.threat_list_layout)
        cl.addWidget(tc)
        cl.addStretch()


# ─── Page: Quick Scan ─────────────────────────────────────────────────────────
class QuickScanPage(QScrollArea):
    scan_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        cw = QWidget()
        self.setWidget(cw)
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(24)

        cl.addWidget(_page_header("Quick Scan",
            "Scans Desktop, Downloads, Documents, and Temp folders"))

        # Target folders card
        targets_card = QFrame()
        targets_card.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}")
        tcl = QVBoxLayout(targets_card)
        tcl.setContentsMargins(20, 16, 20, 16)
        tcl.setSpacing(12)
        tcl.addWidget(_section_title("Scan Targets"))

        home = os.path.expanduser("~")
        targets = [
            ("🖥️", "Desktop",   os.path.join(home, "Desktop")),
            ("📥", "Downloads", os.path.join(home, "Downloads")),
            ("📄", "Documents", os.path.join(home, "Documents")),
            ("🗑️", "Temp",      os.environ.get("TEMP", "/tmp")),
        ]
        for icon, name, path in targets:
            row = QHBoxLayout()
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont("Segoe UI Emoji", 14))
            icon_lbl.setFixedWidth(28)
            name_lbl = QLabel(name)
            name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            name_lbl.setStyleSheet(f"color:{TEXT_PRIMARY};")
            path_lbl = QLabel(path)
            path_lbl.setFont(QFont("Segoe UI", 9))
            path_lbl.setStyleSheet(f"color:{TEXT_SECONDARY};")
            exists = os.path.exists(path)
            status = QLabel("✓ Found" if exists else "✗ Not found")
            status.setStyleSheet(f"color:{'#00FF88' if exists else '#FF4466'}; font-size:10px;")
            status.setFixedWidth(80)
            status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            col = QVBoxLayout()
            col.setSpacing(1)
            col.addWidget(name_lbl)
            col.addWidget(path_lbl)
            row.addWidget(icon_lbl)
            row.addLayout(col, 1)
            row.addWidget(status)
            tcl.addLayout(row)
            tcl.addWidget(_divider())

        cl.addWidget(targets_card)

        # Start button
        start_btn = ScanButton("⚡  START QUICK SCAN", primary=True)
        start_btn.setFixedHeight(54)
        start_btn.clicked.connect(lambda: self.scan_requested.emit("quick"))
        cl.addWidget(start_btn)
        cl.addStretch()

# ─── Page: Updates ────────────────────────────────────────────────────────────
class UpdatesPage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        cw = QWidget()
        self.setWidget(cw)
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(24)

        cl.addWidget(_page_header("Updates", "Virus definitions and application updates"))

        # Current version card
        vc = QFrame()
        vc.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}")
        vcl = QVBoxLayout(vc)
        vcl.setContentsMargins(20, 16, 20, 16)
        vcl.setSpacing(14)
        vcl.addWidget(_section_title("Current Status"))

        # Real DB hash count
        db_count = "0 hashes"
        db_status = "Empty — run seeder"
        db_color  = ACCENT_RED
        if _db:
            try:
                count = _db.total_hashes()
                db_count  = f"{count:,} hashes"
                db_status = "Ready" if count > 0 else "Empty — run seeder"
                db_color  = ACCENT_GREEN if count > 0 else ACCENT_RED
            except Exception:
                pass

        # Real VT status (check env var)
        
        settings = QSettings("SentinelAI", "SentinelAI")
        vt_key_set = bool(
            os.environ.get("VT_API_KEY", "").strip()
            or settings.value("virustotal/api_key", "", type=str).strip()
        )
        vt_status = "Connected" if vt_key_set else "API key required"
        vt_color = ACCENT_GREEN if vt_key_set else ACCENT_AMBER


        # Definition date = today (refreshed when seeder runs)
        def_date  = datetime.now().strftime("v%Y.%m.%d")

        items = [
            ("🛡", "Virus Definitions",   def_date,          "Up to date",  ACCENT_GREEN),
            ("⚙", "Application Version", f"v{APP_VERSION}", "Up to date",  ACCENT_GREEN),
            ("🗄", "Hash Database",       db_count,          db_status,     db_color),
            ("🌐", "Cloud Lookup",        "VirusTotal",      vt_status,     vt_color),
        ]
        # Keep references to live labels so we can update them after seeding
        self._db_version_lbl = None
        self._db_status_lbl  = None
        self._vt_status_lbl  = None

        for i, (icon, name, version, status, color) in enumerate(items):
            row = QHBoxLayout()
            il = QLabel(icon)
            il.setFont(QFont("Segoe UI Emoji", 16))
            il.setFixedWidth(30)
            col = QVBoxLayout()
            col.setSpacing(2)
            nl = QLabel(name)
            nl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            nl.setStyleSheet(f"color:{TEXT_PRIMARY};")
            vl = QLabel(version)
            vl.setFont(QFont("Segoe UI", 9))
            vl.setStyleSheet(f"color:{TEXT_SECONDARY};")
            col.addWidget(nl)
            col.addWidget(vl)
            sl = QLabel(status)
            sl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            sl.setStyleSheet(f"color:{color};")
            sl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(il)
            row.addLayout(col, 1)
            row.addWidget(sl)
            vcl.addLayout(row)
            vcl.addWidget(_divider())
            if i == 2:   # Hash Database row
                self._db_version_lbl = vl
                self._db_status_lbl  = sl
            if i == 3:   # Cloud Lookup row
                self._vt_status_lbl  = sl

        cl.addWidget(vc)

        # Update button
        upd_btn = ScanButton("↑  UPDATE DEFINITIONS NOW", primary=True)
        upd_btn.setFixedHeight(54)
        upd_btn.clicked.connect(self._on_update)
        self.update_status = QLabel("")
        self.update_status.setFont(QFont("Segoe UI", 10))
        self.update_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upd_btn.setObjectName("upd_btn")
        cl.addWidget(upd_btn)
        cl.addWidget(self.update_status)
        cl.addStretch()
        self._upd_btn = upd_btn

    def _on_update(self):
        self._upd_btn.setEnabled(False)
        self._upd_btn.setText("Updating...")
        self.update_status.setStyleSheet(f"color:{ACCENT_CYAN};")
        self.update_status.setText("Downloading latest definitions from MalwareBazaar...")

        # Run seeder on a background thread so UI doesn't freeze
        #self._seed_thread = SeederThread()
        self._seed_thread.finished.connect(self._update_done)
        self._seed_thread.error.connect(self._update_error)
        self._seed_thread.start()

    def _update_done(self, inserted: int, total: int):
        self._upd_btn.setEnabled(True)
        self._upd_btn.setText("↑  UPDATE DEFINITIONS NOW")
        self.update_status.setStyleSheet(f"color:{ACCENT_GREEN};")
        self.update_status.setText(
            f"✓  Updated — {inserted:,} new hashes added  ·  {total:,} total in database"
        )
        # Refresh the live DB count label
        if self._db_version_lbl:
            self._db_version_lbl.setText(f"{total:,} hashes")
        if self._db_status_lbl:
            self._db_status_lbl.setText("Ready")
            self._db_status_lbl.setStyleSheet(f"color:{ACCENT_GREEN};")

    def _update_error(self, message: str):
        self._upd_btn.setEnabled(True)
        self._upd_btn.setText("↑  UPDATE DEFINITIONS NOW")
        self.update_status.setStyleSheet(f"color:{ACCENT_RED};")
        self.update_status.setText(f"✕  Update failed: {message}")


# ─── Page: Settings ───────────────────────────────────────────────────────────
class SettingsPage(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        cw = QWidget()
        self.setWidget(cw)
        cl = QVBoxLayout(cw)
        cl.setContentsMargins(32, 28, 32, 28)
        cl.setSpacing(24)

        cl.addWidget(_page_header("Settings", "Configure Sentinel AI behaviour and integrations"))

        # Protection settings
        p_card = QFrame()
        p_card.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}")
        pcl = QVBoxLayout(p_card)
        pcl.setContentsMargins(20, 16, 20, 16)
        pcl.setSpacing(14)
        pcl.addWidget(_section_title("Protection"))

        toggles = [
            ("Real-time Protection",         "Monitor files as they are created or modified", True),
            ("Web Protection",               "Block malicious URLs and downloads",             True),
            ("Quarantine Threats Automatically","Move detected threats to quarantine",         False),
            ("Send Anonymous Usage Data",    "Help improve Sentinel AI",                       False),
        ]
        self._toggles = {}
        for name, desc, default in toggles:
            row = QHBoxLayout()
            col = QVBoxLayout()
            col.setSpacing(2)
            nl = QLabel(name)
            nl.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            nl.setStyleSheet(f"color:{TEXT_PRIMARY};")
            dl = QLabel(desc)
            dl.setFont(QFont("Segoe UI", 9))
            dl.setStyleSheet(f"color:{TEXT_SECONDARY};")
            col.addWidget(nl)
            col.addWidget(dl)
            cb = QCheckBox()
            cb.setChecked(default)
            cb.setStyleSheet(f"""
                QCheckBox::indicator {{ width:42px; height:22px; border-radius:11px; }}
                QCheckBox::indicator:checked {{ background:{ACCENT_CYAN}; border:none; }}
                QCheckBox::indicator:unchecked {{ background:{BORDER_COLOR}; border:none; }}
            """)
            row.addLayout(col, 1)
            row.addWidget(cb)
            pcl.addLayout(row)
            pcl.addWidget(_divider())
            self._toggles[name] = cb

        cl.addWidget(p_card)

        # VirusTotal API key
        vt_card = QFrame()
        vt_card.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}")
        vtcl = QVBoxLayout(vt_card)
        vtcl.setContentsMargins(20, 16, 20, 16)
        vtcl.setSpacing(12)
        vtcl.addWidget(_section_title("VirusTotal Integration"))
        desc = QLabel("Enter your free VirusTotal API key to enable cloud-based threat lookup.\nGet one free at virustotal.com → Sign up → API Key.")
        desc.setFont(QFont("Segoe UI", 9))
        desc.setStyleSheet(f"color:{TEXT_SECONDARY};")
        desc.setWordWrap(True)
        vtcl.addWidget(desc)
        key_row = QHBoxLayout()
        self.vt_key_input = QLineEdit()
        self.vt_key_input.setPlaceholderText("Paste your VirusTotal API key here...")
        self.vt_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.vt_key_input.setFixedHeight(40)
        self.vt_key_input.setStyleSheet(f"""
            QLineEdit {{
                background:rgba(255,255,255,5); border:1px solid {BORDER_COLOR};
                border-radius:8px; color:{TEXT_PRIMARY}; padding:0 12px;
                font-size:12px;
            }}
            QLineEdit:focus {{ border-color:{ACCENT_CYAN}; }}
        """)
        save_btn = QPushButton("Save")
        save_btn.setFixedSize(80, 40)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background:{ACCENT_CYAN}; color:#000; border:none;
                border-radius:8px; font-weight:700; font-size:12px;
            }}
            QPushButton:hover {{ background:#33DDFF; }}
        """)
        save_btn.clicked.connect(self._save_vt_key)
        self.vt_save_status = QLabel("")
        self.vt_save_status.setFont(QFont("Segoe UI", 9))
        key_row.addWidget(self.vt_key_input, 1)
        key_row.addWidget(save_btn)
        vtcl.addLayout(key_row)
        vtcl.addWidget(self.vt_save_status)
        cl.addWidget(vt_card)

        # Scan schedule card
        sc_card = QFrame()
        sc_card.setStyleSheet(f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}")
        sccl = QVBoxLayout(sc_card)
        sccl.setContentsMargins(20, 16, 20, 16)
        sccl.setSpacing(12)
        sccl.addWidget(_section_title("Scheduled Scans"))
        srow = QHBoxLayout()
        sl = QLabel("Auto Quick Scan Frequency")
        sl.setFont(QFont("Segoe UI", 11))
        sl.setStyleSheet(f"color:{TEXT_PRIMARY};")
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["Disabled", "Daily", "Weekly", "Monthly"])
        self.freq_combo.setCurrentIndex(2)
        self.freq_combo.setFixedWidth(140)
        self.freq_combo.setStyleSheet(f"""
            QComboBox {{
                background:rgba(255,255,255,5); border:1px solid {BORDER_COLOR};
                border-radius:8px; color:{TEXT_PRIMARY}; padding:6px 12px;
                font-size:12px;
            }}
            QComboBox:focus {{ border-color:{ACCENT_CYAN}; }}
            QComboBox QAbstractItemView {{
                background:{BG_CARD}; color:{TEXT_PRIMARY};
                selection-background-color:{ACCENT_CYAN};
            }}
        """)
        srow.addWidget(sl, 1)
        srow.addWidget(self.freq_combo)
        sccl.addLayout(srow)
        cl.addWidget(sc_card)
        cl.addStretch()

    
    def _save_vt_key(self):
        key = self.vt_key_input.text().strip()

        if key:
            settings = QSettings("SentinelAI", "SentinelAI")
            settings.setValue("virustotal/api_key", key)
            settings.sync()

            if settings.status() == QSettings.Status.NoError:
                self.vt_save_status.setStyleSheet(
                    f"color:{ACCENT_GREEN};"
                )
                self.vt_save_status.setText("✓ API key saved.")
            else:
                self.vt_save_status.setStyleSheet(
                    f"color:{ACCENT_RED};"
                )
                self.vt_save_status.setText(
                    "✗ Could not save the API key."
                )
        else:
            self.vt_save_status.setStyleSheet(
                f"color:{ACCENT_RED};"
            )
            self.vt_save_status.setText(
                "✗ Please enter a valid key."
            )


    
    def get_vt_key(self) -> str:
        key = self.vt_key_input.text().strip()
        if key:
            return key

        settings = QSettings("SentinelAI", "SentinelAI")
        return settings.value("virustotal/api_key", "", type=str).strip()



# ─── Page: Placeholder (for unbuilt pages) ────────────────────────────────────
class PlaceholderPage(QWidget):
    def __init__(self, icon, title, subtitle, parent=None):
        super().__init__(parent)
        l = QVBoxLayout(self)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        il = QLabel(icon)
        il.setFont(QFont("Segoe UI Emoji", 48))
        il.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tl = QLabel(title)
        tl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        tl.setStyleSheet(f"color:{TEXT_PRIMARY};")
        tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl = QLabel(subtitle)
        sl.setFont(QFont("Segoe UI", 11))
        sl.setStyleSheet(f"color:{TEXT_SECONDARY};")
        sl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(il)
        l.addSpacing(12)
        l.addWidget(tl)
        l.addSpacing(6)
        l.addWidget(sl)


class FullScanPage(QScrollArea):
    """Full scan page: scans all detected local drive roots via the existing worker."""
    scan_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QWidget()
        self.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        layout.addWidget(_page_header(
            "Full Scan",
            "Scans all detected local drive roots. Large drives may take a long time."
        ))

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:{BG_CARD}; border:1px solid {BORDER_COLOR}; border-radius:12px; }}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        card_layout.addWidget(_section_title("Included locations"))

        try:
            from scanner.scan_targets import full_scan_dirs
            targets = full_scan_dirs()
        except Exception:
            targets = []

        if targets:
            for path in targets:
                row = QHBoxLayout()
                icon_lbl = QLabel("💽")
                icon_lbl.setFont(QFont("Segoe UI Emoji", 14))
                icon_lbl.setFixedWidth(30)
                path_lbl = QLabel(path)
                path_lbl.setFont(QFont("Segoe UI", 10))
                path_lbl.setStyleSheet(f"color:{TEXT_PRIMARY};")
                status_lbl = QLabel("Available")
                status_lbl.setStyleSheet(f"color:{ACCENT_GREEN}; font-size:10px;")
                row.addWidget(icon_lbl)
                row.addWidget(path_lbl, 1)
                row.addWidget(status_lbl)
                card_layout.addLayout(row)
        else:
            note = QLabel("No scan locations were detected. Check drive access and try again.")
            note.setWordWrap(True)
            note.setStyleSheet(f"color:{ACCENT_AMBER};")
            card_layout.addWidget(note)

        layout.addWidget(card)

        info = QLabel(
            "Full Scan uses the existing Sentinel AI scanning engine and detection pipeline. "
            "Inaccessible or locked files may be skipped. Suspicious files are inspected, not executed."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color:{TEXT_SECONDARY}; padding:4px 2px;")
        layout.addWidget(info)

        self.start_btn = ScanButton("◉  START FULL SCAN", primary=True)
        self.start_btn.setFixedHeight(54)
        self.start_btn.setEnabled(bool(targets))
        self.start_btn.clicked.connect(lambda: self.scan_requested.emit("full"))
        layout.addWidget(self.start_btn)
        layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sentinel AI")
        self.setMinimumSize(1100, 680)
        self.resize(1200, 740)
        self.worker = None
        self._threats_this_scan = 0
        self._cancel_requested = False
        self._build_ui()
        self.page_quarantine = QuarantinePage()
        self.stack.addWidget(self.page_quarantine)   
        self.page_reports = ReportsPage()
        self.stack.addWidget(self.page_reports)      
        self.page_damage_assessment = DamageAssessmentPage()
        self.stack.addWidget(self.page_damage_assessment)
        self._apply_global_styles()

    def _apply_global_styles(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background:{BG_BASE}; color:{TEXT_PRIMARY};
                font-family:"Segoe UI","SF Pro Display",Arial,sans-serif;
            }}
            QScrollBar:vertical {{ background:transparent; width:6px; }}
            QScrollBar::handle:vertical {{ background:rgba(255,255,255,15); border-radius:3px; min-height:30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:none; }}
        """)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        rl = QHBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)
        rl.addWidget(self._build_sidebar())

        # ── Stacked pages ─────────────────────────────────────────────────────
        self.stack = QStackedWidget()

        self.page_dashboard  = DashboardPage()
        self.page_quickscan  = QuickScanPage()
        self.page_threats = ProtectionHistoryPage()
        self.page_updates    = UpdatesPage()
        self.page_settings   = SettingsPage()
        self.page_reports    = ReportsPage()
        self.page_fullscan   = FullScanPage()

        self.stack.addWidget(self.page_dashboard)   # index 0
        self.stack.addWidget(self.page_quickscan)   # index 1
        self.stack.addWidget(self.page_fullscan)    # index 2
        self.stack.addWidget(self.page_threats)     # index 3
        self.stack.addWidget(self.page_updates)     # index 4
        self.stack.addWidget(self.page_reports)     # index 5
        self.stack.addWidget(self.page_settings)    # index 6

        rl.addWidget(self.stack, 1)

        # Wire dashboard scan buttons
        self.page_dashboard.quick_btn.clicked.connect(lambda: self._start_scan("quick"))
        self.page_dashboard.full_btn.clicked.connect(lambda: self._start_scan("full"))
        self.page_dashboard.cancel_btn.clicked.connect(self._cancel_scan)

        # Wire quick scan page
        self.page_quickscan.scan_requested.connect(self._start_scan)
        self.page_fullscan.scan_requested.connect(self._start_scan)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"QFrame {{ background:{BG_SIDEBAR}; border-right:1px solid {BORDER_COLOR}; }}")
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)

        # Logo
        lf = QFrame()
        lf.setFixedHeight(72)
        lf.setStyleSheet(f"background:{BG_SIDEBAR}; border-bottom:1px solid {BORDER_COLOR};")
        ll = QHBoxLayout(lf)
        ll.setContentsMargins(20, 0, 20, 0)
        si = QLabel("🛡")
        si.setFont(QFont("Segoe UI Emoji", 20))
        brand = QVBoxLayout()
        brand.setSpacing(0)
        n = QLabel("SENTINEL")
        n.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        n.setStyleSheet(f"color:{TEXT_PRIMARY}; letter-spacing:3px;")
        a = QLabel("AI  ·  v4.1")
        a.setFont(QFont("Segoe UI", 8))
        a.setStyleSheet(f"color:{ACCENT_CYAN}; letter-spacing:2px;")
        brand.addWidget(n)
        brand.addWidget(a)
        ll.addWidget(si)
        ll.addSpacing(8)
        ll.addLayout(brand)
        ll.addStretch()
        sb.addWidget(lf)
        sb.addSpacing(16)

        nav_lbl = QLabel("NAVIGATION")
        nav_lbl.setFont(QFont("Segoe UI", 8))
        nav_lbl.setStyleSheet(f"color:{TEXT_SECONDARY}; letter-spacing:2px; padding-left:20px;")
        sb.addWidget(nav_lbl)
        sb.addSpacing(6)

        # Nav items: (icon, label, stack_index)
        self.nav_buttons = []
        nav_items = [
            ("⬡", "Dashboard",  0),
            ("⟳", "Quick Scan", 1),
            ("◉", "Full Scan",  2),
            ("☰", "Threat Log", 3),
            ("↑", "Updates",    4),
            ("📄", "Reports",    5),
            ("⚙", "Settings",   6),
            ("🔒", "Quarantine", 7),
            ("⚠", "Damage Assessment", 9),
        ]
        for icon, label, idx in nav_items:
            btn = SidebarButton(icon, label)
            sb.addWidget(btn)
            self.nav_buttons.append(btn)
            btn.clicked.connect(lambda _, i=idx, b=btn: self._nav_select(b, i))

        self.nav_buttons[0].set_active(True)
        sb.addStretch()

        # User badge
        uf = QFrame()
        uf.setFixedHeight(64)
        uf.setStyleSheet(f"border-top:1px solid {BORDER_COLOR};")
        ufl = QHBoxLayout(uf)
        ufl.setContentsMargins(16, 0, 16, 0)
        av = QLabel("👤")
        av.setFont(QFont("Segoe UI Emoji", 16))
        ui_v = QVBoxLayout()
        ui_v.setSpacing(1)
        un = QLabel("Admin User")
        un.setFont(QFont("Segoe UI", 15, QFont.Weight.Medium))
        un.setStyleSheet(f"color:{TEXT_PRIMARY};")
        ui_v.addWidget(un)
        ufl.addWidget(av)
        ufl.addSpacing(8)
        ufl.addLayout(ui_v)
        ufl.addStretch()
        sb.addWidget(uf)
        return sidebar

    # ── Navigation ────────────────────────────────────────────────────────────
    def _nav_select(self, active_btn, index: int):
        for btn in self.nav_buttons:
            btn.set_active(btn is active_btn)
        self.stack.setCurrentIndex(index)

    # ── Scan wiring ───────────────────────────────────────────────────────────
    def _start_scan(self, mode: str):
        if self.worker and self.worker.isRunning():
            return

        # Switch to dashboard to show progress
        self._nav_select(self.nav_buttons[0], 0)

        self._threats_this_scan = 0
        self._cancel_requested = False
        self._clear_threat_list()

        db = self.page_dashboard
        db.scan_progress.reset()
        db.scan_progress.set_status(f"Preparing {mode} scan...", ACCENT_CYAN)
        db.quick_btn.setEnabled(False)
        db.full_btn.setEnabled(False)
        db.cancel_btn.setEnabled(True)
        db.shield_status_lbl.setText("SCANNING")
        db.shield_status_lbl.setStyleSheet(f"color:{ACCENT_CYAN}; letter-spacing:3px;")
        db.threat_count_lbl.setText("Scanning in progress...")

        vt_key = self.page_settings.get_vt_key()
        self.worker = ScanWorker(mode=mode, vt_api_key=vt_key, use_virustotal=bool(vt_key))
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.error.connect(self._on_scan_error)
        # Connect threat_found only if worker has that signal
        if hasattr(self.worker, 'threat_found'):
            self.worker.threat_found.connect(self._on_threat_found)
        self.worker.start()
        self._scan_started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._scan_mode = mode

    def _cancel_scan(self):
        if self.worker and self.worker.isRunning():
            self._cancel_requested = True
            self.worker.abort()

            db = self.page_dashboard
            db.scan_progress.set_status(
                "Cancelling scan — waiting for the current operation...",
                ACCENT_AMBER,
            )
            db.cancel_btn.setEnabled(False)
            db.quick_btn.setEnabled(False)
            db.full_btn.setEnabled(False)

            # Do not report PROTECTED until the scan has actually stopped.
            db.shield_status_lbl.setText("CANCELLING")
            db.shield_status_lbl.setStyleSheet(
                f"color:{ACCENT_AMBER}; letter-spacing:3px;"
            )
            db.threat_count_lbl.setText("Stopping scan...")

    
    def _on_progress(self, current: int, total: int, path: str):
        # Ignore queued progress signals after the user presses Cancel.
        if self._cancel_requested:
            return

        db = self.page_dashboard

        if total > 0:
            percent = min(100, int(current * 100 / total))
            db.scan_progress.set_percent(percent)
            progress_text = f"{current:,} / {total:,} files ({percent}%)"
        else:
            # Total is unknown during streaming traversal.
            db.scan_progress.pct_lbl.setText(f"{current:,} files")
            progress_text = f"{current:,} files processed"

        filename = path.replace("\\", "/").split("/")[-1]
        db.scan_progress.set_status(
            f"Scanning: {filename}  •  {progress_text}",
            ACCENT_CYAN,
        )
        db.card_files.set_value(f"{current:,}")


    
    def _on_threat_found(self, file_result):
        # Do not add late queued threat signals after cancellation.
        if self._cancel_requested:
            return

        threat = file_result.threat

        if not threat or threat.verdict not in ("THREAT", "SUSPICIOUS"):
            return

        self._threats_this_scan += 1
        db = self.page_dashboard

        if self._threats_this_scan == 1:
            db.no_threats_lbl.setVisible(False)

        filename = os.path.basename(file_result.path)
        severity = (
            "THREAT"
            if threat.verdict == "THREAT"
            else "SUSPICIOUS"
        )

        item = ThreatItem(
            filename,
            threat.malware_name or "Unknown Malware",
            severity,
            datetime.now().strftime("%H:%M"),
        )

        db.threat_list_layout.insertWidget(0, item)
        db.card_threats.set_value(str(self._threats_this_scan))
        db.threats_title.setText(
            f"Threat Activity  —  {self._threats_this_scan} found"
        )
        db.threat_count_lbl.setText(
            f"{self._threats_this_scan} threat(s) detected!"
        )
        db.threat_count_lbl.setStyleSheet(f"color:{ACCENT_RED};")
        db.shield_widget.protected = False
        db.shield_status_lbl.setText("AT RISK")
        db.shield_status_lbl.setStyleSheet(
            f"color:{ACCENT_RED}; letter-spacing:3px;"
        )

        auto_quarantine = self.page_settings._toggles[
            "Quarantine Threats Automatically"
        ].isChecked()

        if auto_quarantine:
            self.page_quarantine.add_from_file_result(file_result)

        # Note: History logging is handled separately below



    
    def _on_finished(self, result):
        db = self.page_dashboard
        self.page_damage_assessment.update_scan_result(result)

        finished_time = datetime.now().strftime("%H:%M")
        was_cancelled = bool(
            getattr(result, "aborted", False)
            or self._cancel_requested
        )

        db.card_files.set_value(f"{result.scanned_files:,}")
        db.card_threats.set_value(str(result.threats_found))
        db.card_lastscan.set_value(finished_time)
        db.threats_title.setText(
            f"Threat Activity  —  {result.threats_found} found"
        )

        # Keep the scan status accurate.
        if was_cancelled:
            db.scan_progress.set_status(
                f"Scan cancelled — {result.scanned_files:,} files processed; "
                f"{result.threats_found} threats found",
                ACCENT_AMBER,
            )

            if result.threats_found > 0:
                db.shield_widget.protected = False
                db.shield_status_lbl.setText("AT RISK")
                db.shield_status_lbl.setStyleSheet(
                    f"color:{ACCENT_RED}; letter-spacing:3px;"
                )
                db.threat_count_lbl.setText(
                    f"{result.threats_found} threat(s) detected!"
                )
                db.threat_count_lbl.setStyleSheet(
                    f"color:{ACCENT_RED};"
                )
            else:
                db.shield_widget.protected = True
                db.shield_status_lbl.setText("SCAN CANCELLED")
                db.shield_status_lbl.setStyleSheet(
                    f"color:{ACCENT_AMBER}; letter-spacing:2px;"
                )
                db.threat_count_lbl.setText("Scan stopped by user")
                db.threat_count_lbl.setStyleSheet(
                    f"color:{TEXT_SECONDARY};"
                )
        else:
            color = (
                ACCENT_GREEN
                if result.threats_found == 0
                else ACCENT_RED
            )
            db.scan_progress.set_percent(100)
            db.scan_progress.set_status(
                f"✓  Complete  —  {result.scanned_files:,} files  "
                f"|  {result.threats_found} threats  "
                f"|  {result.skipped_files} skipped  "
                f"|  {result.total_mb:.1f} MB",
                color,
            )

        # Generate a report for both completed and cancelled scans.
        try:
            report_path = ReportGenerator.generate(result)
            print(f"✓ Report saved: {report_path}")

            if was_cancelled:
                db.scan_progress.set_status(
                    f"Scan Cancelled • Partial Report Generated\n"
                    f"{report_path}",
                    ACCENT_AMBER,
                )
            else:
                db.scan_progress.set_status(
                    f"✓ Scan Complete • Report Generated\n{report_path}",
                    ACCENT_GREEN
                    if result.threats_found == 0
                    else ACCENT_RED,
                )

        except Exception as e:
            print("Failed to generate report:", e)

        # Update the dashboard's threat status.
        if not was_cancelled:
            if result.threats_found == 0:
                db.shield_widget.protected = True
                db.shield_status_lbl.setText("PROTECTED")
                db.shield_status_lbl.setStyleSheet(
                    f"color:{ACCENT_GREEN}; letter-spacing:3px;"
                )
                db.threat_count_lbl.setText(
                    f"{result.scanned_files:,} files scanned  ·  "
                    "0 threats found"
                )
                db.threat_count_lbl.setStyleSheet(
                    f"color:{TEXT_SECONDARY};"
                )
            else:
                db.shield_widget.protected = False
                db.shield_status_lbl.setText("AT RISK")
                db.shield_status_lbl.setStyleSheet(
                    f"color:{ACCENT_RED}; letter-spacing:3px;"
                )
                db.threat_count_lbl.setText(
                    f"{result.scanned_files:,} files scanned  ·  "
                    f"{result.threats_found} threat(s) found!"
                )
                db.threat_count_lbl.setStyleSheet(
                    f"color:{ACCENT_RED};"
                )

        self._restore_buttons()


    def _on_scan_error(self, message: str):
        db = self.page_dashboard
        db.scan_progress.set_status(f"✕  Error: {message}", ACCENT_RED)
        db.shield_widget.protected = True
        db.shield_status_lbl.setText("PROTECTED")
        db.shield_status_lbl.setStyleSheet(f"color:{ACCENT_GREEN}; letter-spacing:3px;")
        self._restore_buttons()

    def _restore_buttons(self):
        db = self.page_dashboard
        db.quick_btn.setEnabled(True)
        db.full_btn.setEnabled(True)
        db.cancel_btn.setEnabled(False)

    def _clear_threat_list(self):
        db = self.page_dashboard
        while db.threat_list_layout.count():
            item = db.threat_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        db.no_threats_lbl = QLabel("✓  No threats detected yet.  Run a scan to check your system.")
        db.no_threats_lbl.setFont(QFont("Segoe UI", 10))
        db.no_threats_lbl.setStyleSheet(f"color:{TEXT_SECONDARY}; padding:20px 0;")
        db.no_threats_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        db.threat_list_layout.addWidget(db.no_threats_lbl)
        db.threats_title.setText("Threat Activity  —  0 found")
        db.card_threats.set_value("0")
        db.shield_widget.protected = True

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.abort()
            self.worker.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
