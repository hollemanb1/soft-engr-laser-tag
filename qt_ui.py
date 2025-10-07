"""
qt_ui.py
---------
All PyQt UI components.

Responsibilities:
- ScoreboardWindow: main QMainWindow for the app.
- Build Settings Screen: where users configure and hit "Start Game."
- Build Scoreboard Screen: shows live game results.
- refresh_scoreboard(): pull player/score data from engine.state
                        and redraw tables.

Why keep this separate?
- Keeps UI layout/styling isolated from game logic.
- Easy to swap UI later (e.g. different theme) without touching engine.
"""

# header.py
import sys, json, time
from functools import partial

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QSplashScreen,
    QListWidget, QStackedWidget, QLineEdit, QApplication,
    QMainWindow, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QTimer
from db_helper import search_player, add_player  # add this import




########################################################################################
##################################### CONSTRUCTORS #####################################
########################################################################################

# ----- Start Constructors -----

# Initialize the QApplication with global fonts and styles
def init_app():
    app = QApplication(sys.argv)

    # Global font
    app.setFont(QFont("Courier New", 12))

    # Global stylesheet
    app.setStyleSheet("""
        QWidget {
            color: white;
            font-family: "Courier New";
            background-color: #333;
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
    def __init__(self, engine):
        super().__init__()

        self.engine = engine

        self.setWindowTitle("Game Launcher")
        self.setFixedSize(720, 480)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # --- Build pages ---
        self.settings_page = Build_Settings_Screen(self.start_game, self.engine)
        self.scoreboard_page = Build_Scoreboard_Screen(self.go_to_settings)

        # --- Add pages to stack ---
        self.stack.addWidget(self.settings_page)     # index 0
        self.stack.addWidget(self.scoreboard_page)   # index 1

        # Show settings first
        self.stack.setCurrentIndex(0)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            self.start_game()
        else:
            super().keyPressEvent(event)

    def start_game(self):
        self.engine.start_game()
        self.stack.setCurrentIndex(1)

        # Start poll timer here
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._poll_events)
        self.poll_timer.start(200)

    def _poll_events(self):
        self.engine.process_pending_events()
        self.refresh_scoreboard()

    def refresh_scoreboard(self):
        players = list(self.engine.players.values())

        red_team = players[:len(players)//2]
        green_team = players[len(players)//2:]

        # clear old scoreboard_page and rebuild
        self.stack.removeWidget(self.stack.widget(1))

        # Rebuild scoreboard with current teams
        self.scoreboard_page = Build_Scoreboard_Screen(self.go_to_settings, red_team, green_team)
        self.stack.addWidget(self.scoreboard_page)
        self.stack.setCurrentIndex(1)

    def go_to_settings(self):
        self.stack.setCurrentIndex(0)

    def go_to_scoreboard(self):
        self.stack.setCurrentIndex(1)





# Simply used for showing the splash screen
def Start_App(app, window):
    splash = QLabel()
    pixmap = QPixmap("logo.jpg").scaled(360, 229, Qt.KeepAspectRatioByExpanding)
    splash.setPixmap(pixmap)
    splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
    splash.setFixedSize(360, 229)
    splash.show()

    # after 5 seconds, close splash and show main window
    QTimer.singleShot(2000, lambda: (splash.close(), window.show()))

# ----- End Constructors -----






#######################################################################################
############################ BUILDER FUNCTIONS ########################################
#######################################################################################
#
#   In a Multi-window Qt app, the paradigm is to have builder functions
#     that you call from main, and when you need to switch windows, you
#     call a switcher function to change which page you display. These
#     functions below are builders, and they return a container to the
#     main window. That way everything is basically built and boxed up
#     right before main gets it
#





###############################
######## SETTINGS PAGE ########
###############################

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
    box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
    box_layout = QVBoxLayout(box)

    # Title
    title = QLabel(box_title)
    title.setAlignment(Qt.AlignLeft)
    title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
    box_layout.addWidget(title)

    inputs, buttons = [], []

    for field in fields:
        row = QHBoxLayout()

        line = QLineEdit()
        line.setPlaceholderText(field["field_placeholder"])
        inputs.append(line)

        button = QPushButton(field["button_text"])
        button.setFixedSize(120, 30)
        buttons.append(button)

        func = field["button_func"]
        button.clicked.connect(partial(func, line))   # pass the line itself

        row.addWidget(line)
        row.addWidget(button)
        box_layout.addLayout(row)

    return box, {"inputs": inputs, "buttons": buttons}



##### ADD USER PAGE (Settings Sub-Page) #####

def User_Page(engine):
    def Search(line):
        """Search for a player by ID and add them to the engine if found."""
        try:
            player_id = int(line.text())
        except ValueError:
            # Invalid input
            search_button.setEnabled(False)
            search_button.setText("Invalid ID")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")
            QTimer.singleShot(1500, Reset_User_UI)
            return

        result = search_player(player_id)

        if result:
            codename = result["codename"]
            engine.join_player(codename)
            local_ui_player_list.addItem(f"{codename} ({player_id})")

            search_button.setEnabled(False)
            search_button.setText("Player Added!")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #33f533;")
            QTimer.singleShot(1500, Reset_User_UI)

        else:
            # Not found → prompt for codename
            search_button.setEnabled(False)
            search_button.setText("Not Found")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")
            codename_input.show()
            add_button.show()

    def Add_User(line):
        player_id = int(id_input.text())
        codename = codename_input.text().strip()

        success = add_player(player_id, codename)

        if success:
            engine.join_player(codename)
            local_ui_player_list.addItem(f"{codename} ({player_id})")

            search_button.setEnabled(False)
            search_button.setText("User Added!")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #33f533;")
            QTimer.singleShot(1500, Reset_User_UI)
        else:
            search_button.setEnabled(False)
            search_button.setText("DB Error")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")
            QTimer.singleShot(1500, Reset_User_UI)


    def Reset_User_UI():
        codename_input.hide()
        add_button.hide()
        id_input.clear()
        codename_input.clear()
        search_button.setEnabled(True)
        search_button.setText("Search")
        search_button.setStyleSheet("background-color: #333; color: white;")

    # --- Page layout ---
    page = QWidget()
    page.setStyleSheet("background-color: #444444;")
    layout = QVBoxLayout(page)

    add_user_box, refs = build_form_box(
        "Add Player to Game:",
        [
            {"field_placeholder": "Enter Player ID...", "button_text": "Search", "button_func": Search},
            {"field_placeholder": "Enter Codename", "button_text": "Add User", "button_func": Add_User}
        ]
    )

    # Easier refs
    id_input, codename_input = refs["inputs"]
    search_button, add_button = refs["buttons"]

    codename_input.hide()
    add_button.hide()

    # --- Local player list widget ---
    local_ui_player_list = QListWidget()
    local_ui_player_list.setStyleSheet("background-color: #333; color: white; font-size: 18px; padding: 3px;")

    # Container for the "Players:" title + text box
    player_header = QWidget()
    header_layout = QHBoxLayout(player_header)
    header_layout.setContentsMargins(0, 0, 0, 0)

    header_label = QLabel("Players:")
    header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
    header_layout.addWidget(header_label)

    # unused text box (just placed to the right)
    dummy_box = QLineEdit()
    dummy_box.setPlaceholderText("Search Players (not working)")
    dummy_box.setFixedWidth(180)
    dummy_box.setAlignment(Qt.AlignCenter)
    header_layout.addStretch()
    header_layout.addWidget(dummy_box)

    layout.addWidget(add_user_box)
    layout.addWidget(player_header)
    layout.addWidget(local_ui_player_list)
    layout.addStretch()

    return page




##### NETWORK PAGE (Settings Sub-Page) #####
def Network_Page(engine):
    def change_ip(line):
        ip = line.text()
        engine.change_ip(ip)

    page = QWidget()
    page.setStyleSheet("background-color: #444444;")
    layout = QVBoxLayout(page)

    change_ip_box, refs = build_form_box(
        "Change IP:",
        [
            {
                "field_placeholder": "DEFAULT: LOCALHOST",
                "button_text": "Change",
                "button_func": change_ip
            }
        ]
    )

    address_input = refs["inputs"]
    change_button = refs["buttons"]

    layout.addWidget(change_ip_box)
    layout.addStretch()
    return page



##### Settings Builder (Sidebar + Pages) #####
def Build_Settings_Screen(start_callback, engine):
    container = QWidget()
    container.setStyleSheet("background-color: #333; color: white;")
    main_layout = QVBoxLayout(container)   # vertical: header on top, body below

    # --- Header row ---
    header_layout = QHBoxLayout()
    header_text = QLabel("Settings")
    header_text.setStyleSheet("font-size: 20px; font-weight: bold; padding: 1px;")
    start_button = QPushButton("Start Game")
    start_button.clicked.connect(start_callback)
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
    stack.addWidget(User_Page(engine))
    stack.addWidget(Network_Page(engine))
    body_layout.addWidget(stack, stretch=1)

    menu.currentRowChanged.connect(stack.setCurrentIndex)
    menu.setCurrentRow(0)

    main_layout.addLayout(body_layout)

    return container




#################################
######## SCOREBOARD PAGE ########
#################################

##### Scoreboard Builder #####
def Build_Scoreboard_Screen(start_callback, red_team=None, green_team=None):

    container = QWidget()
    container.setStyleSheet("background-color: #222;")
    h_layout = QHBoxLayout(container)

    red_team = red_team or []
    green_team = green_team or []

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
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setVisible(False)
    table.setShowGrid(False)
    table.setStyleSheet(
        "background-color: #1a1a1a; color: white; font-size: 16px; "
        "gridline-color: #1a1a1a; border-radius: 6px;"
    )

    for row, p in enumerate(players):
        name_item = QTableWidgetItem(" " + p.username)
        score_item = QTableWidgetItem(str(p.score))
        name_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        table.setItem(row, 0, name_item)
        table.setItem(row, 1, score_item)


    table.horizontalHeader().setStretchLastSection(True)
    table.setColumnWidth(0, 200)

    # Header row
    header_layout = QHBoxLayout()
    header_layout.setContentsMargins(0, 0, 0, 0)
    header_layout.setSpacing(0)
    header_label = QLabel(team_name)
    header_label.setStyleSheet(
        f"background-color: {team_color}; color: white; "
        "font-weight: bold; font-size: 18px; padding: 4px; border-top-left-radius: 2px; border-bottom-left-radius: 2px;"
    )
    header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    total_label = QLabel(str(sum(p.score for p in players)))
    total_label.setStyleSheet(
        f"background-color: {team_color}; color: white; "
        "font-size: 16px; padding: 4px; border-top-right-radius: 2px; border-bottom-right-radius: 2px;"
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
