# header.py
import sys, json, time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QSplashScreen,
    QListWidget, QStackedWidget, QLineEdit, QApplication,
    QMainWindow, QSizePolicy, QAbstractItemView
)
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtCore import Qt, QTimer


##### CONSTRUCTORS #####

def init_app():
    """Initialize the QApplication with global fonts and styles."""
    app = QApplication(sys.argv)

    # Global font
    app.setFont(QFont("Courier New", 12))

    # Global stylesheet
    app.setStyleSheet("""
        QWidget {
            color: white;
            font-family: "Courier New";
        }
        QLineEdit {
            background-color: #333;
            border: 1px solid #555;
            padding: 4px;
            border-radius: 4px;
        }
        QPushButton {
            background-color: #444;
            border: 1px solid #666;
            padding: 6px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #555;
        }
    """)

    return app


class ScoreboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Launcher")
        self.setFixedSize(720, 480)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.container.setStyleSheet("background-color: #272727;")
        self.setCentralWidget(self.container)




##### HELPER FUNCTIONS #####



##### SPLASH SCREEN #####
def Start_App(app, window):
    splash = QLabel()
    pixmap = QPixmap("logo.jpg").scaled(360, 229, Qt.KeepAspectRatioByExpanding)
    splash.setPixmap(pixmap)
    splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
    splash.setFixedSize(360, 229)
    splash.show()

    # after 5 seconds, close splash and show main window
    QTimer.singleShot(500, lambda: (splash.close(), window.show()))



##### Box Setup #####
# Allows me to make multiple fields in the settings menu,
#   and not have to continually remake them over and over
  #
  #   Args:
  #       box_title (str): Title at the top of the box.
  #       fields (list of dict): Each dict defines one row:
  #           {
  #               "field_placeholder": str,
  #               "button_text": str,
  #               "button_func": callable   # takes input_text as arg
  #           }
  #
  #   Returns:
  #       (QWidget, dict):
  #           - The QWidget containing the whole box
  #           - A dict of { "inputs": [QLineEdit...], "buttons": [QPushButton...] }

def build_form_box(box_title, fields):

    box = QWidget()
    box.setStyleSheet("""
        background-color: #333;
        color: white;
        font-size: 16px;
    """)
    box.setSizePolicy(
        QSizePolicy.Expanding,   # fill horizontally
        QSizePolicy.Maximum      # shrink vertically
    )
    box_layout = QVBoxLayout(box)

    # Title
    title = QLabel(box_title)
    title.setAlignment(Qt.AlignLeft)
    title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
    box_layout.addWidget(title)

    # Fields
    for field in fields:
        row = QHBoxLayout()
        line = QLineEdit()
        line.setPlaceholderText(field["field_placeholder"])
        button = QPushButton(field["button_text"])
        button.setFixedSize(120, 30)

        # Hook up the function if provided
        func = field["button_func"]
        button.clicked.connect(lambda _, l=line: func(l.text()))

        row.addWidget(line)
        row.addWidget(button)
        box_layout.addLayout(row)

    return box






##### ADD USER PAGE #####
def User_Page():
    def Search(name):
        result = False  # <-- replace with your function
        if result:
            print("found!")
        else:
            print("not found")
            # search_button.setEnabled(False)
            # search_button.setText("Not Found")
            # search_button.setStyleSheet("color: #f53333;")
            # id_input.show()
            # add_button.show()

    def Add_User(user, id):
        print(f"added {user} to database")

    page = QWidget()
    page.setStyleSheet("background-color: #444444;")
    layout = QVBoxLayout(page)

    # --- Group box ---
    add_user_box = build_form_box(
        "Add User:",
        [
            {
                "field_placeholder": "Enter Name Here...",
                "button_text": "Search",
                "button_func": Search
            },
            {
                "field_placeholder": "Enter ID Number Here...",
                "button_text": "Add User",
                "button_func": Add_User
            }
        ]
    )

    #id_input.hide()
    #add_button.hide()

    # Add group box to page
    layout.addWidget(add_user_box)
    layout.addStretch()

    return page



##### NETWORK PAGE #####
def Network_Page():
    def change_ip(new_ip):
        print(f"Changing IP to {new_ip}")   # replace with real logic

    page = QWidget()
    page.setStyleSheet("background-color: #444444;")
    layout = QVBoxLayout(page)

    change_ip_box = build_form_box(
        "Change IP:",
        [
            {
                "field_placeholder": "DEFAULT: LOCALHOST",
                "button_text": "Change",
                "button_func": change_ip
            }
        ]
    )

    layout.addWidget(change_ip_box)
    layout.addStretch()
    return page


##### SETUP SCREEN (Sidebar + Pages) #####
def Setup_Screen():
    container = QWidget()
    main_layout = QVBoxLayout(container)   # vertical: header on top, body below

    # --- Header row ---
    header_layout = QHBoxLayout()
    header_text = QLabel("Settings")
    header_text.setStyleSheet("font-size: 20px; font-weight: bold; padding: 1px;")
    start_button = QPushButton("Start Game")
    start_button.setStyleSheet("font-size: 13px; background-color: #2f2f2f")
    header_layout.addWidget(header_text)
    header_layout.addStretch()
    header_layout.addWidget(start_button)
    main_layout.addLayout(header_layout)

    # --- Body row ---
    body_layout = QHBoxLayout()

    menu = QListWidget()
    menu.addItems(["Add Users", "Network"])
    menu.setFixedWidth(140)
    menu.setStyleSheet("""
        QListWidget {
            color: white;
            font-size: 18px;
            background-color: #2f2f2f;
            padding: 10px;
        }
        QListWidget::item:selected {
            background-color: #007377;
            color: white;
        }
    """)
    body_layout.addWidget(menu)

    stack = QStackedWidget()
    stack.addWidget(User_Page())
    stack.addWidget(Network_Page())
    body_layout.addWidget(stack, stretch=1)

    menu.currentRowChanged.connect(stack.setCurrentIndex)
    menu.setCurrentRow(0)

    main_layout.addLayout(body_layout)

    return container



##### START BUTTON PAGE #####
def Start_Button_Page(start_callback):
    container = QWidget()
    layout = QVBoxLayout(container)

    button = QPushButton("Start Game")
    button.setFixedSize(200, 40)
    button.setStyleSheet("font-size: 18px;")
    button.clicked.connect(start_callback)

    layout.addWidget(button, alignment=Qt.AlignCenter)
    return container


##### SCOREBOARD PAGE #####
def Scoreboard_Page(players):
    container = QWidget()
    h_layout = QHBoxLayout(container)

    # Split players into two teams (for demo)
    red_team = players[:len(players)//2]
    green_team = players[len(players)//2:]

    # Left: stacked scoreboards
    left_layout = QVBoxLayout()
    left_layout.setSpacing(20)
    left_layout.addWidget(Build_Team_Table("Red Team", red_team, "#cc0000"))
    left_layout.addWidget(Build_Team_Table("Green Team", green_team, "#00cc00"))
    h_layout.addLayout(left_layout)

    # Right: message box
    message_box = QTextEdit()
    message_box.setReadOnly(True)
    message_box.setPlaceholderText("Game messages will appear here...")
    message_box.setStyleSheet("font-size: 14px; background-color: #333; color: white;")
    h_layout.addWidget(message_box)

    return container


##### TEAM TABLE BUILDER #####
def Build_Team_Table(team_name, players, team_color):
    table = QTableWidget(len(players), 2)
    #table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setVisible(False)
    table.setShowGrid(False)
    table.setStyleSheet(
        "background-color: #1a1a1a; color: white; font-size: 16px; "
        "gridline-color: #1a1a1a; border-radius: 6px;"
    )

    for row, p in enumerate(players):
        name_item = QTableWidgetItem(p["name"])
        score_item = QTableWidgetItem(str(p["score"]))
        name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        table.setItem(row, 0, name_item)
        table.setItem(row, 1, score_item)

    table.horizontalHeader().setStretchLastSection(True)
    table.setColumnWidth(0, 200)

    # Header row
    header_layout = QHBoxLayout()
    header_label = QLabel(team_name)
    header_label.setStyleSheet(
        f"background-color: {team_color}; color: white; "
        "font-weight: bold; font-size: 18px; padding: 4px;"
    )
    header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    total_label = QLabel(str(sum(p['score'] for p in players)))
    total_label.setStyleSheet(
        f"background-color: {team_color}; color: white; "
        "font-size: 16px; padding: 4px;"
    )
    total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    header_layout.addWidget(header_label)
    header_layout.addWidget(total_label)

    wrapper = QWidget()
    wrapper_layout = QVBoxLayout(wrapper)
    wrapper_layout.setSpacing(6)
    wrapper_layout.addLayout(header_layout)
    wrapper_layout.addWidget(table)

    return wrapper
