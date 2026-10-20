import sys
import os

from dotenv import load_dotenv
from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow
from scanner.realtime import RealTimeMonitor


def main():

    # Load environment variables from .env
    load_dotenv()

    app = QApplication(sys.argv)

    # -----------------------------
    # Start Real-Time Protection
    # -----------------------------

    home = os.path.expanduser("~")

    folders = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "Downloads"),
        os.path.join(home, "Documents"),
    ]

    monitor = RealTimeMonitor(folders)
    monitor.start()

    # -----------------------------
    # Launch GUI
    # -----------------------------

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()