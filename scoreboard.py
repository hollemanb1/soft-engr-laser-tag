import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class ScoreboardApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # --- Window Setup ---
        self.setWindowTitle("Game Launcher")
        self.setFixedSize(720, 480)  # fixed size window

        # Central container & layout
        self.container = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)
        self.container.setStyleSheet("background-color: #222222;")
        self.container.setLayout(self.layout)
        self.setCentralWidget(self.container)

        # --- Start Screen Widgets ---
        self.prompt = QLabel("Start Game?")
        self.prompt.setAlignment(Qt.AlignCenter)
        self.prompt.setFont(QFont("Courier New", 28, QFont.Bold))

        self.start_button = QPushButton("Start")
        self.start_button.setFixedWidth(200)
        self.start_button.setFixedHeight(40)
        self.start_button.setStyleSheet("font-size: 18px;")
        self.start_button.clicked.connect(self.show_scoreboard)

        self.layout.addWidget(self.prompt)
        self.layout.addWidget(self.start_button)

    # --- Function: Replace prompt with scoreboard ---
    def show_scoreboard(self):
        # Clear old widgets
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Build and display scoreboard
        self.build_scoreboard()


    def build_scoreboard(self):
        # Load player data from JSON
        with open("test-database.json", "r") as f:
            players = json.load(f)

        # Example split: first half = Red Team, second half = Green Team
        # (Later you can actually split by team in your JSON)
        red_team = players[:len(players)//2]
        green_team = players[len(players)//2:]

        # --- Main Horizontal Layout (scoreboards left + messages right) ---
        h_layout = QHBoxLayout()

        # --- Left Side: Two stacked scoreboards ---
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)

        # Build red and green team tables
        red_table = self.build_team_table("Red Team", red_team, "#cc0000")
        green_table = self.build_team_table("Green Team", green_team, "#00cc00")

        left_layout.addWidget(red_table)
        left_layout.addWidget(green_table)

        # Add left layout to main layout
        h_layout.addLayout(left_layout)

        # --- Messages Panel (Right Side) ---
        self.message_box = QTextEdit()
        self.message_box.setReadOnly(True)
        self.message_box.setPlaceholderText("Game messages will appear here...")
        self.message_box.setStyleSheet("font-size: 14px; background-color: #333333; color: white;")
        h_layout.addWidget(self.message_box)

        # Apply horizontal layout to main container
        self.layout.addLayout(h_layout)


    def build_team_table(self, team_name, players, team_color):
        """Helper function: creates a visually styled table for a single team."""

        # --- Table Setup ---
        table = QTableWidget(len(players), 2)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setVisible(False)
        table.setShowGrid(False)

        # Style: slightly darker than background, no visible borders
        table.setStyleSheet(
            "background-color: #1a1a1a; color: white; font-size: 16px; "
            "gridline-color: #1a1a1a; border-radius: 6px;"
        )

        # Fill player rows
        for row, p in enumerate(players):
            name_item = QTableWidgetItem(p["name"])
            score_item = QTableWidgetItem(str(p["score"]))
            name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, score_item)

        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, 200)

        # --- Header Row (Team Name + Total Score Side by Side) ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        header_label = QLabel(team_name)
        header_label.setStyleSheet(
            f"background-color: {team_color}; color: white; "
            "font-weight: bold; font-size: 18px; padding: 4px; border-top-left-radius: 2px; border-bottom-left-radius: 2px;"
        )

        header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        total_score = sum(p['score'] for p in players)
        total_label = QLabel(f"{total_score}")
        total_label.setStyleSheet(
            f"background-color: {team_color}; color: white; "
            "font-size: 16px; padding: 4px; border-top-right-radius: 2px; border-bottom-right-radius: 2px;"
        )

        total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        header_layout.addWidget(header_label)
        header_layout.addWidget(total_label)

        # --- Wrapper Layout (Header + Table) ---
        wrapper = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.addLayout(header_layout)
        layout.addWidget(table)
        wrapper.setLayout(layout)

        return wrapper



    def add_message(self, text):
        """Append a new message to the message box."""
        self.message_box.append(text)
        self.message_box.ensureCursorVisible()


# --- Main Program Entry ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScoreboardApp()
    window.show()
    sys.exit(app.exec_())
