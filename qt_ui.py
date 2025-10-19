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
import sys, json, time, os
from PIL import Image
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
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence





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
        QWidget {                                                                           # Q Widget's default style (all containers, including windows)
            color: white;
            font-family: "Courier New";
            background-color: #333;
        }
        QLineEdit {                                                                         # Q Line Edit's default style (text input box, single line)
            background-color: #333;
            border: 1px solid #555;
            padding: 4px;
            border-radius: 4px;
        }
        QPushButton {                                                                       # Q Push Button's default style (all buttons that are pushable)
            background-color: #444;
            border: 1px solid #666;
            padding: 6px;
            border-radius: 4px;
        }
        QPushButton:hover {                                                                 # Hover effect for buttons (mouse over the button, not pressed) 
            background-color: #555;
        }
    """)

    return app                                                                              # basically this function will establish the app's customizable features,
                                                                                            # allowing for quick changes that will be returned to be used in main



class ScoreboardWindow(QMainWindow):                                                        # main window containing stacked settings and scoreboard pages
    def __init__(self, engine):
        super().__init__()

        self.engine = engine                                                                # set engine reference for later usage

        self.setWindowTitle("Game Launcher")                                                # window title
        self.setFixedSize(720, 480)

        self.stack = QStackedWidget()                                                       # stack to hold multiple pages (settings + scoreboard)
        self.setCentralWidget(self.stack)                                                   # set stack as central widget of main window, allowing for page switching

        # --- Build pages ---
        #self.settings_page = Build_Settings_Screen(self.start_game, self.engine)            # settings page: consists of sidebar + sub-pages
        self.settings_page = Build_Settings_Screen(self.start_game_with_countdown_on_scoreboard, self.engine)

        self.scoreboard_page = Build_Scoreboard_Screen(self.go_to_settings)                 # scoreboard page: consists of team tables + message box

        # --- Add pages to stack ---
        self.stack.addWidget(self.settings_page)                                            # index 0
        self.stack.addWidget(self.scoreboard_page)                                          # index 1

        # Show settings first
        self.stack.setCurrentIndex(0)
        QShortcut(QKeySequence(Qt.Key_F5), self,
          activated=self.start_game_with_countdown_on_scoreboard)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            self.start_game()
        elif event.key()== Qt.Key_F12:
            self.engine.clear_player_list()
            print("Player List Cleared!")
        else:
            super().keyPressEvent(event)


    def start_game(self):
        self.engine.start_game()
        self.stack.setCurrentIndex(1)

        # Start poll timer here
        self.poll_timer = QTimer(self)                                                      # poll: to regularly check for new events from the engine 
        self.poll_timer.timeout.connect(self._poll_events)                                  # connect the timer's timeout signal to the _poll_events method
        self.poll_timer.start(200)                                                          # poll every 200 ms

    def _poll_events(self):
        self.engine.process_pending_events()                                                # process any pending events in the engine
        self.refresh_scoreboard()                                                           # refresh scoreboard to display accurate data

    # def refresh_scoreboard(self):
    #     players = list(self.engine.players.values())                                        # refreshing scoreboard starts by creating a list of all players in the game

    #     red_team = players[:len(players)//2]                                                # red team becomes the first half of the players list
    #     green_team = players[len(players)//2:]                                              # green team becomes the second half of the players list

    #     # clear old scoreboard_page and rebuild
    #     self.stack.removeWidget(self.stack.widget(1))                                       # remove old scoreboard page from stack,

    #     # Rebuild scoreboard with current teams
    #     self.scoreboard_page = Build_Scoreboard_Screen(self.go_to_settings, red_team, green_team)   # rebuild scoreboard page with current teams
    #     self.stack.addWidget(self.scoreboard_page)                                          # add new scoreboard page to stack
    #     self.stack.setCurrentIndex(1)                                                       # set current index to 1 to show the scoreboard page
    
    def refresh_scoreboard(self):
        players = list(self.engine.players.values())

        # TODO: replace this split with your real team logic if you have one
        mid = len(players) // 2
        red_team = players[:mid]
        green_team = players[mid:]

        red_table   = self.scoreboard_page.findChild(QTableWidget, "table_red")
        green_table = self.scoreboard_page.findChild(QTableWidget, "table_green")
        red_total   = self.scoreboard_page.findChild(QLabel, "total_red")
        green_total = self.scoreboard_page.findChild(QLabel, "total_green")

        self._populate_team_table(red_table, red_team)
        self._populate_team_table(green_table, green_team)

        if red_total:
            red_total.setText(str(sum(p.score for p in red_team)))
        if green_total:
            green_total.setText(str(sum(p.score for p in green_team)))

    def _populate_team_table(self, table, team):
        if table is None:
            return
        table.setRowCount(len(team))
        for row, p in enumerate(team):
            name_item  = QTableWidgetItem(" " + p.username)
            score_item = QTableWidgetItem(str(p.score))
            name_item.setTextAlignment(Qt.AlignLeft  | Qt.AlignVCenter)
            score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, score_item)


    def go_to_settings(self):
        self.stack.setCurrentIndex(0)                                                       # traversal: switch to settings page

    def go_to_scoreboard(self):
        self.stack.setCurrentIndex(1)                                                       # traversal: switch to scoreboard page
    def start_with_countdown(self):
        # ensure we're on the menu page
        self.stack.setCurrentIndex(0)
        # find the label in the settings page once
        self.countdown_label = self.settings_page.findChild(QLabel, "countdownLabel")
        self._count = 30

        # draw first frame immediately
        self._update_countdown_label(self._count)

        # tick every second
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._tick_countdown)
        self._countdown_timer.start(1000)

    def _tick_countdown(self):
        self._count -= 1
        if self._count < 0:
            # done → clear label, stop timer, start game
            self._countdown_timer.stop()
            if self.countdown_label:
                self.countdown_label.clear()
            self.start_game()
            return
        self._update_countdown_label(self._count)

    def _update_countdown_label(self, n: int):
        folder = "countdown_images"            # e.g., ./countdown_images/30.tif ... 0.tif
        path = os.path.join(folder, f"{n}.tif")
        if os.path.exists(path):
            pix = QPixmap(path).scaled(
                self.countdown_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.countdown_label.setPixmap(pix)
            self.countdown_label.setText("")   # ensure no text overlay
        else:
            # fallback: show plain number if image missing
            self.countdown_label.setPixmap(QPixmap())
            self.countdown_label.setText(str(n))
            self.countdown_label.setStyleSheet(
                "background:#1b1b1b; border:1px solid #444; font-size:36px; font-weight:bold;"
            )
    def start_game_with_countdown_on_scoreboard(self):
        self.stack.setCurrentIndex(1)

        # start polling NOW (if not already running)
        if not hasattr(self, "poll_timer") or self.poll_timer is None:
            self.poll_timer = QTimer(self)
            self.poll_timer.timeout.connect(self._poll_events)
            self.poll_timer.start(200)

        # make sure first frame shows current players
        self.refresh_scoreboard()

        self.countdown_label = self.scoreboard_page.findChild(QLabel, "countdownLabelScore")
        if not self.countdown_label:
            # no rebuilds — refresh_scoreboard no longer destroys widgets (see §2)
            pass

        self._count = 30
        self._update_scoreboard_countdown(self._count)

        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._tick_scoreboard_countdown)
        self._countdown_timer.start(1000)

    def _tick_scoreboard_countdown(self):
        self._count -= 1
        if self._count < 0:
            self._countdown_timer.stop()
            if self.countdown_label:
                self.countdown_label.clear()
            self.engine.start_game()
            self.stack.setCurrentIndex(1)
            return
        self._update_scoreboard_countdown(self._count)


    def _update_scoreboard_countdown(self, n: int):
        """Draw the countdown frame on the scoreboard label (image if present, else text)."""
        if not self.countdown_label:
            return
        folder = "countdown_images"
        path = os.path.join(folder, f"{n}.tif")
        if os.path.exists(path):
            pix = QPixmap(path).scaled(
                self.countdown_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.countdown_label.setPixmap(pix)
            self.countdown_label.setText("")
        else:
            self.countdown_label.setPixmap(QPixmap())
            self.countdown_label.setText(str(n))
            self.countdown_label.setStyleSheet(
                "background:#1b1b1b; border:1px solid #444; font-size:36px; font-weight:bold;"
            )




# Simply used for showing the splash screen
def Start_App(app, window):
    splash = QLabel()                                                                       # splash screen is a QLabel; it will display an image
    pixmap = QPixmap("logo.jpg").scaled(360, 229, Qt.KeepAspectRatioByExpanding)            # load and scale the image to fit the splash screen size
    splash.setPixmap(pixmap)                                                                # set the loaded image to the scaled splash QLabel
    splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)                         # set window flags to make it a splash screen and frameless   
    splash.setFixedSize(360, 229)                                                           # set fixed size for the splash screen
    splash.show()                                                                           # make the splash screen visible

    # after 5 seconds, close splash and show main window
    QTimer.singleShot(2000, lambda: (splash.close(), window.show()))                        # after 2 seconds, close splash and show main window, yay!


def build_form_box(box_title, fields):                                                      # builds a form box with a title and multiple fields                     
    box = QWidget()
    box.setStyleSheet("""
        background-color: #333;
        color: white;
        font-size: 16px;
    """)
    box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)                           # make box expand horizontally but not vertically       
    box_layout = QVBoxLayout(box)                                                           # vertical layout for the box         

    # Title
    title = QLabel(box_title)                                                               # title label at the top of the box           
    title.setAlignment(Qt.AlignLeft)
    title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
    box_layout.addWidget(title)

    inputs, buttons = [], []

    for field in fields:                                                                    # for each field in the fields list, create a row with a line edit and button
        row = QHBoxLayout()                                                                 # horizontal layout for each row

        line = QLineEdit()                                                                  # line edit for user input           
        line.setPlaceholderText(field["field_placeholder"])                                 # set placeholder text from field dict
        inputs.append(line)                                                                 # keep reference to line edit

        button = QPushButton(field["button_text"])                                          # button with text from field dict
        button.setFixedSize(120, 30)
        buttons.append(button)

        func = field["button_func"]                                                         # get the function from the field dict
        button.clicked.connect(partial(func, line))                                         # pass the line itself after button is clicked

        row.addWidget(line)                                                                 # adds the line edit to the row
        row.addWidget(button)                                                               # adds the button to the row
        box_layout.addLayout(row)                                                           # adds the row to the box layout, allowing it to be on our main box

    return box, {"inputs": inputs, "buttons": buttons}                                      # finally, return the box, inputs, and buttons for later reference



##### ADD USER PAGE (Settings Sub-Page) #####

def User_Page(start_callback, engine):                                                                      # page for adding users to the game, allows for inputting of ID and searching for the player
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            self.start_game_with_countdown_on_scoreboard()
        elif event.key()== Qt.Key_F12:
            engine.clear_player_list()
            local_ui_player_list.clear()
            print("Player List Cleared!")
        else:
            super().keyPressEvent(event)
    
    def Search(line):           
        """Search for a player by ID and add them to the engine if found."""
        try:
            player_id = int(line.text())                                                    # trys to get the player ID from the input line
        except ValueError:
            # Invalid input
            search_button.setEnabled(False)                                                 # simple error handling for invalid input                    
            search_button.setText("Invalid ID")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")
            QTimer.singleShot(1500, Reset_User_UI)
            return

        result = search_player(player_id)                                                   # searches for the player with given ID and saves the result of search

        if result:                                                                          # if the user is found in the DB, add them to the game engine. 
            codename = result["codename"]
            engine.join_player(codename)                                                    # adds the player to the game engine
            local_ui_player_list.addItem(f"{codename} ({player_id})")                       # adds the player to the local UI list

            search_button.setEnabled(False)                                                 # disables the search button to prevent multiple clicks
            search_button.setText("Player Added!")                                          # changes button text to indicate success               
            search_button.setStyleSheet("background-color: #2a2a2a; color: #33f533;")       # changes button color to green, representing validity
            QTimer.singleShot(1500, Reset_User_UI)                                          # resets the UI after 1.5 seconds, allowing for another search

        else:                                                                               # now if no player is found witht he ID inputted, the button operations will go as follows
            # Not found → prompt for codename
            search_button.setEnabled(False)                                                 # disables the search button to prevent multiple clicks
            search_button.setText("Not Found")                                              # changes button text to indicate failure
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")       # changes button color to red, representing invalidity
            codename_input.show()                                                           # shows the codename input field for user to enter a codename
            add_button.show()                                                               # shows the add button for user to click after entering codename

    def Add_User(line):                                                                     # now to handle actually adding the player after searching for them
        player_id = int(id_input.text())
        codename = codename_input.text().strip()                                            # normalizes the codename input for a user mapped to their ID; removes leading/trailing whitespace

        success = add_player(player_id, codename)                                           # attempts to add the player to the DB, returns True if successful, False otherwise

        if success:
            engine.join_player(codename)                                                    # adds the player to the game engine
            local_ui_player_list.addItem(f"{codename} ({player_id})")                       # adds the player to the local UI list

            search_button.setEnabled(False)
            search_button.setText("User Added!")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #33f533;")       # outputs a success message, changes button color to green, and resets the UI after 1.5 seconds
            QTimer.singleShot(1500, Reset_User_UI)
        else:
            search_button.setEnabled(False)
            search_button.setText("DB Error")                                               # if unsuccessful, outputs a failure message, changes button color to red, and resets the UI after 1.5 seconds
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")
            QTimer.singleShot(1500, Reset_User_UI)


    def Reset_User_UI():                                                                    # now we must handle resetting the UI after a search/add operation
        codename_input.hide()                                                               # hides the codename input field
        add_button.hide()                                                                   # hides the add button                 
        id_input.clear()                                                                    # clears the ID input field for next input
        codename_input.clear()                                                              # clears the codename input field for next input
        search_button.setEnabled(True)
        search_button.setText("Search")
        search_button.setStyleSheet("background-color: #333; color: white;")                # allows for searching, resets button text and color to default

    # --- Page layout ---
    page = QWidget()
    page.setStyleSheet("background-color: #444444;")                                        # creates a page with QWidget, sets background color to dark gray, and a vertical layout
    layout = QVBoxLayout(page)

    add_user_box, refs = build_form_box(                                                    # uses the build_form_box function to create the add user box with title and fields
        "Add Player to Game:",
        [
            {"field_placeholder": "Enter Player ID...", "button_text": "Search", "button_func": Search},
            {"field_placeholder": "Enter Codename", "button_text": "Add User", "button_func": Add_User}
        ]
    )

    # Easier refs
    id_input, codename_input = refs["inputs"]                                               # gets references to the input fields
    search_button, add_button = refs["buttons"]                                             # gets references to the buttons

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
    stack.addWidget(User_Page(start_callback, engine))
    stack.addWidget(Network_Page(engine))
    body_layout.addWidget(stack, stretch=1)

    menu.currentRowChanged.connect(stack.setCurrentIndex)
    menu.setCurrentRow(0)

    main_layout.addLayout(body_layout)
    # inside Build_Settings_Screen(), after creating start_button, before adding header_layout:
    # countdown_label = QLabel(" ")
    # countdown_label.setObjectName("countdownLabel")
    # countdown_label.setFixedSize(120, 120)
    # countdown_label.setAlignment(Qt.AlignCenter)
    # countdown_label.setStyleSheet("background:#1b1b1b; border:1px solid #444;")
    # header_layout.addWidget(countdown_label)


    return container




#################################
######## SCOREBOARD PAGE ########
#################################

##### Scoreboard Builder #####
# def Build_Scoreboard_Screen(start_callback, red_team=None, green_team=None):

#     container = QWidget()
#     container.setStyleSheet("background-color: #222;")
#     h_layout = QHBoxLayout(container)

#     red_team = red_team or []
#     green_team = green_team or []

#     # Left: stacked scoreboards
#     left_layout = QVBoxLayout()
#     left_layout.setSpacing(20)
#     left_layout.addWidget(Build_Team_Table("Red Team", red_team, "#cc0000"))
#     left_layout.addWidget(Build_Team_Table("Green Team", green_team, "#00cc00"))
#     h_layout.addLayout(left_layout)

#     # Right: message box
#     message_box = QTextEdit()
#     message_box.setReadOnly(True)
#     message_box.setPlaceholderText("Game messages will appear here...")
#     message_box.setStyleSheet("font-size: 14px; background-color: #333; color: white;")
#     h_layout.addWidget(message_box)

#     return container
def Build_Scoreboard_Screen(start_callback, red_team=None, green_team=None):
    container = QWidget()
    container.setStyleSheet("background-color: #222;")

    # MAIN layout now vertical: header (countdown) on top, then the two-column body
    v_layout = QVBoxLayout(container)
    v_layout.setSpacing(10)

    # --- Header: centered countdown label ---
    header = QHBoxLayout()
    header.setContentsMargins(0, 0, 0, 0)
    header.addStretch()
    countdown_label = QLabel(" ")
    countdown_label.setObjectName("countdownLabelScore")     # <-- we’ll find this later
    countdown_label.setFixedSize(160, 160)
    countdown_label.setAlignment(Qt.AlignCenter)
    countdown_label.setStyleSheet("background: transparent; border: none;")
    countdown_label.setAttribute(Qt.WA_TranslucentBackground, True)
    header.addWidget(countdown_label)
    header.addStretch()
    v_layout.addLayout(header)

    # --- Body: existing two-team tables (left) + message box (right) ---
    h_layout = QHBoxLayout()
    red_team = red_team or []
    green_team = green_team or []

    left_layout = QVBoxLayout()
    left_layout.setSpacing(20)
    left_layout.addWidget(Build_Team_Table("Red Team", red_team, "#cc0000"))
    left_layout.addWidget(Build_Team_Table("Green Team", green_team, "#00cc00"))
    h_layout.addLayout(left_layout)

    message_box = QTextEdit()
    message_box.setReadOnly(True)
    message_box.setPlaceholderText("Game messages will appear here...")
    message_box.setStyleSheet("font-size: 14px; background-color: #333; color: white;")
    h_layout.addWidget(message_box)

    v_layout.addLayout(h_layout)

    return container




##### TEAM TABLE BUILDER #####
def Build_Team_Table(team_name, players, team_color):
    table = QTableWidget(len(players), 2)
    key = team_name.lower().split()[0]                                  # "Red Team" -> "red" or "Green Team" -> "green"
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setObjectName(f"table_{key}")

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
    total_label.setObjectName(f"total_{key}")

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


# need to create a game start countdown that goes from 30 ... 0 
# this countdown will be at the top middle of the screen
# it will appear while in the main
# occurs after start is pressed and countdown begins

def start_countdown(self):
    folder = "countdown_images/"  # path to your folder
    for i in range(31):          # goes from 0 to 30
        filename = f"{i}.tif"  # or .jpg, .jpeg, etc.
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            print(f"Opening {path}")
            img = Image.open(path)
            # do something with img (e.g., display, resize, etc.)
        else:
            print(f"File {path} not found.")




    
    

