import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QProgressBar, QScrollArea,
    QGraphicsDropShadowEffect, QSizePolicy, QStackedWidget
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QThread, pyqtSignal, QPointF, QRectF, pyqtProperty, QObject
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath, QConicalGradient, QFontDatabase
)
import math
import random


# ─── Colour tokens ────────────────────────────────────────────────────────────
BG_BASE       = "#0A0E1A"
BG_CARD       = "#0D1827"
BG_SIDEBAR    = "#080C17"
ACCENT_CYAN   = "#00D4FF"
ACCENT_GREEN  = "#00FF88"
ACCENT_RED    = "#FF4466"
ACCENT_AMBER  = "#FFB020"
TEXT_PRIMARY  = "#E8EEF8"
TEXT_SECONDARY= "#8892A4"
BORDER_COLOR  = "#1A2540"
GLOW_CYAN     = QColor(0, 212, 255, 60)
GLOW_GREEN    = QColor(0, 255, 136, 60)


# ─── Animated Shield Widget ────────────────────────────────────────────────────
class ShieldWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 220)
        self._pulse = 0.0
        self._rotation = 0.0
        self._ring2_rotation = 0.0
        self.protected = True

        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._tick)
        self.pulse_timer.start(16)

    def _tick(self):
        self._pulse = (self._pulse + 0.03) % (2 * math.pi)
        self._rotation = (self._rotation + 0.4) % 360
        self._ring2_rotation = (self._ring2_rotation - 0.6) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy = self.width() / 2, self.height() / 2
        pulse_val = (math.sin(self._pulse) + 1) / 2  # 0→1

        # ── Outer glow halo ──
        for i in range(5, 0, -1):
            alpha = int(12 * pulse_val * i)
            r = 95 + i * 4
            color = QColor(0, 212, 255, alpha) if self.protected else QColor(255, 68, 102, alpha)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawEllipse(QPointF(cx, cy), r, r)

        # ── Rotating dashed ring ──
        p.save()
        p.translate(cx, cy)
        p.rotate(self._rotation)
        pen = QPen(QColor(0, 212, 255, 80), 1.5, Qt.PenStyle.DashLine)
        pen.setDashPattern([4, 6])
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), 90, 90)
        p.restore()

        # ── Counter-rotating dotted ring ──
        p.save()
        p.translate(cx, cy)
        p.rotate(self._ring2_rotation)
        pen2 = QPen(QColor(0, 255, 136, 50), 1, Qt.PenStyle.DotLine)
        pen2.setDashPattern([2, 8])
        p.setPen(pen2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(0, 0), 78, 78)
        p.restore()

        # ── Solid circle base ──
        grad = QRadialGradient(cx, cy - 20, 65)
        if self.protected:
            grad.setColorAt(0, QColor("#0D2540"))
            grad.setColorAt(1, QColor("#060C18"))
        else:
            grad.setColorAt(0, QColor("#250D18"))
            grad.setColorAt(1, QColor("#180608"))
        _circle_color = QColor(ACCENT_CYAN if self.protected else ACCENT_RED)
        _circle_color.setAlpha(120)
        p.setPen(QPen(_circle_color, 1.5))
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), 65, 65)

        # ── Shield path ──
        shield_color = QColor(ACCENT_CYAN) if self.protected else QColor(ACCENT_RED)
        shield_color.setAlpha(int(200 + 55 * pulse_val))

        path = QPainterPath()
        s = 36
        path.moveTo(cx, cy - s)
        path.cubicTo(cx + s * 1.1, cy - s * 0.9,
                     cx + s * 1.2, cy + s * 0.2,
                     cx, cy + s * 1.15)
        path.cubicTo(cx - s * 1.2, cy + s * 0.2,
                     cx - s * 1.1, cy - s * 0.9,
                     cx, cy - s)

        shield_grad = QLinearGradient(cx, cy - s, cx, cy + s)
        shield_grad.setColorAt(0, QColor(ACCENT_CYAN if self.protected else ACCENT_RED))
        shield_grad.setColorAt(1, QColor(0, 180, 220, 180) if self.protected else QColor(220, 40, 80, 180))
        p.setPen(QPen(shield_color, 2))
        p.setBrush(QBrush(shield_grad))
        p.drawPath(path)

        # ── Check or X mark ──
        p.setPen(QPen(QColor("#FFFFFF"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        if self.protected:
            p.drawLine(int(cx - 12), int(cy + 2), int(cx - 2), int(cy + 12))
            p.drawLine(int(cx - 2), int(cy + 12), int(cx + 14), int(cy - 8))
        else:
            p.drawLine(int(cx - 10), int(cy - 10), int(cx + 10), int(cy + 10))
            p.drawLine(int(cx + 10), int(cy - 10), int(cx - 10), int(cy + 10))

        p.end()


# ─── Stat Card ────────────────────────────────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, icon, value, label, accent="#00D4FF", parent=None):
        super().__init__(parent)
        self.accent = QColor(accent)
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            StatCard {{
                background: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 18))
        val_lbl = QLabel(value)
        val_lbl.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        val_lbl.setStyleSheet(f"color: {accent};")
        top.addWidget(icon_lbl)
        top.addStretch()
        top.addWidget(val_lbl)

        lbl = QLabel(label)
        lbl.setFont(QFont("Segoe UI", 9))
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")

        layout.addLayout(top)
        layout.addWidget(lbl)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.accent, 2)
        p.setPen(pen)
        p.drawLine(0, self.height() - 1, int(self.width() * 0.4), self.height() - 1)
        p.end()


# ─── Sidebar Button ───────────────────────────────────────────────────────────
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
        self.toggled.connect(lambda checked: self._set_active(checked))

    def _set_active(self, val):
        self._active = val
        self._update_style()

    def _update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(0,212,255,25), stop:1 rgba(0,212,255,5));
                    border: none;
                    border-left: 3px solid {ACCENT_CYAN};
                    border-radius: 0px;
                    color: {ACCENT_CYAN};
                    font-size: 13px;
                    font-weight: 600;
                    text-align: left;
                    padding-left: 20px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0px;
                    color: {TEXT_SECONDARY};
                    font-size: 13px;
                    text-align: left;
                    padding-left: 20px;
                }}
                QPushButton:hover {{
                    background: rgba(0,212,255,8);
                    color: {TEXT_PRIMARY};
                    border-left: 3px solid rgba(0,212,255,80);
                }}
            """)
        self.setText(f"  {self._icon}   {self._label}")


# ─── Scan Button ──────────────────────────────────────────────────────────────
class ScanButton(QPushButton):
    def __init__(self, text, primary=True, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #0099BB, stop:1 #00D4FF);
                    color: #ffffff;
                    border: none;
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 1px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #00BBDD, stop:1 #33DDFF);
                }}
                QPushButton:pressed {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #007799, stop:1 #00AABB);
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {ACCENT_CYAN};
                    border: 1px solid rgba(0,212,255,60);
                    border-radius: 10px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: rgba(0,212,255,12);
                    border: 1px solid rgba(0,212,255,120);
                }}
                QPushButton:pressed {{
                    background: rgba(0,212,255,20);
                }}
            """)


# ─── Threat List Item ─────────────────────────────────────────────────────────
class ThreatItem(QFrame):
    def __init__(self, name, threat_type, severity, time_ago, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            ThreatItem {{
                background: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
            ThreatItem:hover {{
                border: 1px solid rgba(0,212,255,40);
            }}
        """)
        self.setFixedHeight(64)

        sev_colors = {"HIGH": ACCENT_RED, "MED": ACCENT_AMBER, "LOW": ACCENT_CYAN}
        color = sev_colors.get(severity, ACCENT_CYAN)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color}; font-size: 10px;")
        dot.setFixedWidth(16)

        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(name)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY};")
        type_lbl = QLabel(threat_type)
        type_lbl.setFont(QFont("Segoe UI", 9))
        type_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        info.addWidget(name_lbl)
        info.addWidget(type_lbl)

        sev_lbl = QLabel(severity)
        sev_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        sev_lbl.setFixedSize(40, 20)
        sev_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sev_lbl.setStyleSheet(f"""
            color: {color};
            background: rgba(0,0,0,40);
            border: 1px solid {color};
            border-radius: 4px;
        """)

        time_lbl = QLabel(time_ago)
        time_lbl.setFont(QFont("Segoe UI", 8))
        time_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        time_lbl.setFixedWidth(55)
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(dot)
        layout.addLayout(info, 1)
        layout.addWidget(sev_lbl)
        layout.addSpacing(10)
        layout.addWidget(time_lbl)


# ─── Progress Scan Bar ────────────────────────────────────────────────────────
class ScanProgress(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            ScanProgress {{
                background: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
            }}
        """)
        self.setFixedHeight(90)
        self.scanning = False
        self._progress = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self.status_lbl = QLabel("System Idle  —  Last scan: 2 hours ago")
        self.status_lbl.setFont(QFont("Segoe UI", 10))
        self.status_lbl.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self.pct_lbl = QLabel("")
        self.pct_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.pct_lbl.setStyleSheet(f"color: {ACCENT_CYAN};")
        top.addWidget(self.status_lbl)
        top.addStretch()
        top.addWidget(self.pct_lbl)

        self.bar = QProgressBar()
        self.bar.setFixedHeight(6)
        self.bar.setTextVisible(False)
        self.bar.setValue(0)
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(255,255,255,8);
                border-radius: 3px;
                border: none;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0099BB, stop:1 #00D4FF);
                border-radius: 3px;
            }}
        """)

        layout.addLayout(top)
        layout.addWidget(self.bar)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._advance)

    def start_scan(self, label="Quick Scan"):
        self.scanning = True
        self._progress = 0
        self.bar.setValue(0)
        self.status_lbl.setText(f"Running {label}...")
        self.status_lbl.setStyleSheet(f"color: {ACCENT_CYAN};")
        self.timer.start(40)

    def _advance(self):
        self._progress += random.uniform(0.4, 1.2)
        if self._progress >= 100:
            self._progress = 100
            self.timer.stop()
            self.scanning = False
            self.status_lbl.setText("✓  Scan complete  —  No threats found")
            self.status_lbl.setStyleSheet(f"color: {ACCENT_GREEN};")
            self.pct_lbl.setText("")
        else:
            self.pct_lbl.setText(f"{int(self._progress)}%")
        self.bar.setValue(int(self._progress))


# ─── Main Window ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sentinel AI")
        self.setMinimumSize(1100, 680)
        self.resize(1200, 740)
        self._build_ui()
        self._apply_global_styles()

    def _apply_global_styles(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {BG_BASE};
                color: {TEXT_PRIMARY};
                font-family: "Segoe UI", "SF Pro Display", Arial, sans-serif;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255,255,255,15);
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ──
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {BG_SIDEBAR};
                border-right: 1px solid {BORDER_COLOR};
            }}
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo area
        logo_frame = QFrame()
        logo_frame.setFixedHeight(72)
        logo_frame.setStyleSheet(f"background: {BG_SIDEBAR}; border-bottom: 1px solid {BORDER_COLOR};")
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(20, 0, 20, 0)
        shield_icon = QLabel("🛡")
        shield_icon.setFont(QFont("Segoe UI Emoji", 20))
        brand = QVBoxLayout()
        brand.setSpacing(0)
        name_lbl = QLabel("SENTINEL")
        name_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {TEXT_PRIMARY}; letter-spacing: 3px;")
        ai_lbl = QLabel("AI  ·  v4.1")
        ai_lbl.setFont(QFont("Segoe UI", 8))
        ai_lbl.setStyleSheet(f"color: {ACCENT_CYAN}; letter-spacing: 2px;")
        brand.addWidget(name_lbl)
        brand.addWidget(ai_lbl)
        logo_layout.addWidget(shield_icon)
        logo_layout.addSpacing(8)
        logo_layout.addLayout(brand)
        logo_layout.addStretch()

        sb_layout.addWidget(logo_frame)
        sb_layout.addSpacing(16)

        nav_label = QLabel("NAVIGATION")
        nav_label.setFont(QFont("Segoe UI", 8))
        nav_label.setStyleSheet(f"color: {TEXT_SECONDARY}; letter-spacing: 2px; padding-left: 20px;")
        sb_layout.addWidget(nav_label)
        sb_layout.addSpacing(6)

        self.nav_buttons = []
        nav_items = [
            ("⬡", "Dashboard"),
            ("⟳", "Quick Scan"),
            ("◉", "Full Scan"),
            ("☰", "Threat Log"),
            ("↑", "Updates"),
            ("⚙", "Settings"),
        ]
        for icon, label in nav_items:
            btn = SidebarButton(icon, label)
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            btn.clicked.connect(lambda _, b=btn: self._nav_select(b))

        self.nav_buttons[0].setChecked(True)
        self.nav_buttons[0]._set_active(True)

        sb_layout.addStretch()

        # User badge
        user_frame = QFrame()
        user_frame.setFixedHeight(64)
        user_frame.setStyleSheet(f"border-top: 1px solid {BORDER_COLOR};")
        uf_layout = QHBoxLayout(user_frame)
        uf_layout.setContentsMargins(16, 0, 16, 0)
        avatar = QLabel("👤")
        avatar.setFont(QFont("Segoe UI Emoji", 16))
        user_info = QVBoxLayout()
        user_info.setSpacing(1)
        uname = QLabel("Admin User")
        uname.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        uname.setStyleSheet(f"color: {TEXT_PRIMARY};")
        uplan = QLabel("Enterprise Plan")
        uplan.setFont(QFont("Segoe UI", 8))
        uplan.setStyleSheet(f"color: {ACCENT_CYAN};")
        user_info.addWidget(uname)
        user_info.addWidget(uplan)
        uf_layout.addWidget(avatar)
        uf_layout.addSpacing(8)
        uf_layout.addLayout(user_info)
        uf_layout.addStretch()
        sb_layout.addWidget(user_frame)

        # ── Main Content ──
        content = QScrollArea()
        content.setWidgetResizable(True)
        content.setFrameShape(QFrame.Shape.NoFrame)
        content.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content.setWidget(content_widget)
        c_layout = QVBoxLayout(content_widget)
        c_layout.setContentsMargins(32, 28, 32, 28)
        c_layout.setSpacing(24)

        # Header
        header = QHBoxLayout()
        h_text = QVBoxLayout()
        h_text.setSpacing(3)
        page_title = QLabel("Security Overview")
        page_title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        page_title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        page_sub = QLabel("Wednesday, 25 Jun 2026  ·  Real-time protection enabled")
        page_sub.setFont(QFont("Segoe UI", 10))
        page_sub.setStyleSheet(f"color: {TEXT_SECONDARY};")
        h_text.addWidget(page_title)
        h_text.addWidget(page_sub)

        notif_btn = QPushButton("🔔")
        notif_btn.setFixedSize(40, 40)
        notif_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                font-size: 16px;
                color: {TEXT_SECONDARY};
            }}
            QPushButton:hover {{ border-color: {ACCENT_CYAN}; color: {ACCENT_CYAN}; }}
        """)

        header.addLayout(h_text)
        header.addStretch()
        header.addWidget(notif_btn)
        c_layout.addLayout(header)

        # ── Shield + Status Row ──
        hero_row = QHBoxLayout()
        hero_row.setSpacing(24)

        # Shield panel
        shield_panel = QFrame()
        shield_panel.setFixedWidth(260)
        shield_panel.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 16px;
            }}
        """)
        sp_layout = QVBoxLayout(shield_panel)
        sp_layout.setContentsMargins(20, 20, 20, 20)
        sp_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.shield_widget = ShieldWidget()
        sp_layout.addWidget(self.shield_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        status_lbl = QLabel("PROTECTED")
        status_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_lbl.setStyleSheet(f"color: {ACCENT_GREEN}; letter-spacing: 3px;")

        threat_count = QLabel("0 threats detected")
        threat_count.setFont(QFont("Segoe UI", 9))
        threat_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threat_count.setStyleSheet(f"color: {TEXT_SECONDARY};")

        sp_layout.addWidget(status_lbl)
        sp_layout.addSpacing(2)
        sp_layout.addWidget(threat_count)

        # Right side of hero: stat cards + scan controls
        right_col = QVBoxLayout()
        right_col.setSpacing(16)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        stats = [
            ("🗂", "14,302", "Files Scanned",  ACCENT_CYAN),
            ("🛡", "47",     "Threats Blocked", ACCENT_GREEN),
            ("⚡", "2 hrs",  "Last Full Scan",  ACCENT_AMBER),
            ("🌐", "ON",     "Web Protection",  ACCENT_GREEN),
        ]
        for icon, val, lbl, color in stats:
            card = StatCard(icon, val, lbl, color)
            stats_row.addWidget(card)

        right_col.addLayout(stats_row)

        # Scan progress
        self.scan_progress = ScanProgress()
        right_col.addWidget(self.scan_progress)

        # Scan buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        quick = ScanButton("⚡  QUICK SCAN", primary=True)
        full  = ScanButton("◉  FULL SCAN",  primary=False)
        custom = ScanButton("☰  CUSTOM",    primary=False)
        quick.clicked.connect(lambda: self.scan_progress.start_scan("Quick Scan"))
        full.clicked.connect(lambda: self.scan_progress.start_scan("Full Scan"))
        btn_row.addWidget(quick, 2)
        btn_row.addWidget(full,  2)
        btn_row.addWidget(custom, 1)
        right_col.addLayout(btn_row)

        hero_row.addWidget(shield_panel)
        hero_row.addLayout(right_col, 1)
        c_layout.addLayout(hero_row)

        # ── Recent Threats ──
        threats_header = QHBoxLayout()
        th_title = QLabel("Recent Threat Activity")
        th_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        th_title.setStyleSheet(f"color: {TEXT_PRIMARY};")
        see_all = QPushButton("View all →")
        see_all.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT_CYAN};
                border: none;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: white; }}
        """)
        threats_header.addWidget(th_title)
        threats_header.addStretch()
        threats_header.addWidget(see_all)
        c_layout.addLayout(threats_header)

        threats_data = [
            ("Trojan.GenericKD.71234",  "Trojan",         "HIGH", "3 min ago"),
            ("Adware.Bundleware.99X",   "Adware",         "MED",  "18 min ago"),
            ("PUP.Optional.Toolbar",    "Unwanted App",   "LOW",  "1 hr ago"),
            ("Spyware.Agent.ZP",        "Spyware",        "MED",  "2 hrs ago"),
            ("Ransom.WannaCrypt!ml",    "Ransomware",     "HIGH", "Yesterday"),
        ]
        for data in threats_data:
            item = ThreatItem(*data)
            c_layout.addWidget(item)

        c_layout.addStretch()

        # ── Assemble root ──
        root_layout.addWidget(sidebar)
        root_layout.addWidget(content, 1)

    def _nav_select(self, active_btn):
        for btn in self.nav_buttons:
            if btn is not active_btn:
                btn.setChecked(False)
                btn._set_active(False)
            else:
                btn._set_active(True)
