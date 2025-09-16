import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QTextEdit
)
from PyQt5.QtCore import QTimer, Qt

# --- Placeholder Data ---
players = [
    {"name": "Player 1", "score": 100},
    {"name": "Player 2", "score": 90},
    {"name": "Player 3", "score": 80},
]

class ScoreboardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laser Tag Scoreboard")
        self.resize(600, 400)

        # --- Main Container ---
        container = QWidget()
        self.setCentralWidget(container)

        main_layout = QVBoxLayout(container)

        # --- Timer Label ---
        self.time_left = 10
        self.timer_label = QLabel(f"Time Left: {self.time_left}")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.timer_label)

        # --- Horizontal Layout for Table + Notifications ---
        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # --- Scoreboard Table ---
        self.table = QTableWidget(len(players), 2)
        self.table.setHorizontalHeaderLabels(["Score", "Name"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        for i, p in enumerate(players):
            self.table.setItem(i, 0, QTableWidgetItem(str(p["score"])))
            self.table.setItem(i, 1, QTableWidgetItem(p["name"]))

        self.table.resizeColumnsToContents()
        content_layout.addWidget(self.table)

        # --- Notifications Panel ---
        self.notif_box = QTextEdit()
        self.notif_box.setReadOnly(True)
        self.notif_box.setStyleSheet("background-color: #222; color: white;")
        content_layout.addWidget(self.notif_box)

        # --- Timers ---
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        self.notif_timer = QTimer()
        self.notif_timer.timeout.connect(self.add_fake_notification)
        self.notif_timer.start(3000)

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.setText(f"Time Left: {self.time_left}")
        else:
            self.timer_label.setText("GAME OVER")
            self.notif_box.append("Game Over!")
            self.timer.stop()

    def add_fake_notification(self):
        p1, p2 = random.sample(players, 2)
        self.notif_box.append(f"{p1['name']} shot {p2['name']}")
        self.notif_box.ensureCursorVisible()

# --- Main Entry Point ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScoreboardApp()
    window.show()
    sys.exit(app.exec_())
