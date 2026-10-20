import os
import sys
import subprocess
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
    QPushButton,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
)

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

REPORT_DIR = "reports/generated"


class ReportCard(QFrame):

    def __init__(self, pdf_path):
        super().__init__()

        self.pdf_path = pdf_path

        self.setStyleSheet("""
        QFrame{
            background:#101827;
            border:1px solid #1A2540;
            border-radius:14px;
        }

        QFrame:hover{
            border:1px solid #00D4FF;
        }

        QPushButton{
            background:#0D6EFD;
            color:white;
            border:none;
            border-radius:8px;
            padding:6px 18px;
        }

        QPushButton:hover{
            background:#1F82FF;
        }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20,15,20,15)

        icon = QLabel("📄")
        icon.setFont(QFont("Segoe UI Emoji",24))
        layout.addWidget(icon)

        info = QVBoxLayout()

        filename = QLabel(os.path.basename(pdf_path))
        filename.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        filename.setStyleSheet("color:white")

        dt = datetime.fromtimestamp(os.path.getmtime(pdf_path))
        date = dt.strftime("%d %b %Y   %H:%M")

        size = os.path.getsize(pdf_path)/1024

        details = QLabel(f"{date}   •   {size:.1f} KB")
        details.setStyleSheet("color:#8B92A4")

        info.addWidget(filename)
        info.addWidget(details)

        layout.addLayout(info)

        layout.addStretch()


        open_btn = QPushButton("Open")
        delete_btn = QPushButton("Delete")

        delete_btn.setStyleSheet("""
        QPushButton{
            background:#D32F2F;
            color:white;
            border:none;
            border-radius:8px;
            padding:6px 18px;
        }

        QPushButton:hover{
            background:#F44336;
        }
        """)

        open_btn.clicked.connect(self.open_report)
        delete_btn.clicked.connect(self.delete_report)

        layout.addWidget(open_btn)
        layout.addWidget(delete_btn)

    def open_report(self):

        if sys.platform.startswith("win"):
            os.startfile(self.pdf_path)
        elif sys.platform.startswith("darwin"):
            subprocess.call(["open", self.pdf_path])
        else:
            subprocess.call(["xdg-open", self.pdf_path])

    def delete_report(self):

        reply = QMessageBox.question(
            self,
            "Delete Report",
            "Delete this report?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            os.remove(self.pdf_path)
            self.setParent(None)
            self.deleteLater()


class ReportsPage(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Security Reports")
        title.setFont(QFont("Segoe UI",20,QFont.Weight.Bold))
        title.setStyleSheet("color:white")
        layout.addWidget(title)

        toolbar = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search reports...")
        self.search.textChanged.connect(self.refresh)

        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)

        delete_all = QPushButton("Delete All")
        delete_all.clicked.connect(self.delete_all)

        toolbar.addWidget(self.search)
        toolbar.addWidget(refresh)
        toolbar.addWidget(delete_all)

        layout.addLayout(toolbar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.container = QWidget()
        self.report_layout = QVBoxLayout(self.container)

        self.scroll.setWidget(self.container)

        layout.addWidget(self.scroll)

        self.load_reports()

    def clear_layout(self):

        while self.report_layout.count():

            item = self.report_layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

    def refresh(self):

        self.clear_layout()
        self.load_reports()

    def delete_all(self):

        reply = QMessageBox.question(
            self,
            "Delete All",
            "Delete all reports?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if os.path.exists(REPORT_DIR):

            for f in os.listdir(REPORT_DIR):

                if f.endswith(".pdf"):
                    os.remove(os.path.join(REPORT_DIR,f))

        self.refresh()

    def load_reports(self):

        if not os.path.exists(REPORT_DIR):
            return

        keyword = self.search.text().lower()

        reports = sorted(
            [
                os.path.join(REPORT_DIR,f)
                for f in os.listdir(REPORT_DIR)
                if f.endswith(".pdf")
                and keyword in f.lower()
            ],
            reverse=True
        )

        if not reports:

            lbl = QLabel("No reports found.")
            lbl.setStyleSheet("color:#8B92A4")
            self.report_layout.addWidget(lbl)

        else:

            for pdf in reports:
                self.report_layout.addWidget(ReportCard(pdf))

        self.report_layout.addStretch()