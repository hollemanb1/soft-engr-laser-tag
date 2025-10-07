# main.py
"""
Main entry point for the Photon Game.

- Creates QApplication (Qt event loop).
- Builds the ScoreboardWindow (UI).
- Starts splash screen.
- Starts UDPTransport + GameCore (backend).
- Uses a QTimer to:
    * Pull new events from UDPTransport.event_queue
    * Process them with GameCore (updates state + DB)
    * Refresh the scoreboard UI
"""

import sys, time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from qt_ui import ScoreboardWindow, Start_App   # <-- your old qt_header.py (rename to qt_ui.py)
from engine_mk2 import GameEngine                   # <-- new consolidated game logic -- CHANGE 'engine' to 'engine_mk2' to test new engine

def main():
    # --- Start Qt app ---
    app = QApplication(sys.argv)

    # --- Create engine (but don’t start yet) ---
    engine = GameEngine()

    # --- Create main window and pass engine reference ---
    window = ScoreboardWindow(engine)
    Start_App(app, window)


    # --- Run app event loop ---
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

