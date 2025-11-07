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
from PIL import ImageQt, Image
from functools import partial

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTextEdit, QSplashScreen,
    QListWidget, QStackedWidget, QLineEdit, QApplication,
    QMainWindow, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont, QImage
from PyQt5.QtCore import Qt, QTimer, QTime
from db_helper import search_player, add_player  # add this import
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence, QPixmap


# at top of file:
def load_pix_safe(path: str):
    pm = QPixmap(path)
    if not pm.isNull():
        return pm
    try:
        from PIL import ImageQt, Image
        img = Image.open(path)
        qimg = ImageQt.ImageQt(img)
        pm = QPixmap.fromImage(qimg)
        if not pm.isNull():
            return pm
    except Exception as e:
        print(f"[WARN] load_pix_safe failed for {path}: {e}")
    return None







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

def append_message(message_box: QTextEdit, text: str, max_lines = 32):
    lines = message_box.toPlainText().splitlines()
    lines.append(text)
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    message_box.setPlainText("\n".join(lines))
    
    cursor = message_box.textCursor()
    cursor.movePosition(cursor.End)
    message_box.setTextCursor(cursor)

class ScoreboardWindow(QMainWindow):                                                        # main window containing stacked settings and scoreboard pages
    def __init__(self, engine):
        super().__init__()

        self.in_countdown = False

        self.engine = engine                                                                # set engine reference for later usage

        self.setWindowTitle("Game Launcher")                                                # window title

        self.stack = QStackedWidget()                                                       # stack to hold multiple pages (settings + scoreboard)
        self.setCentralWidget(self.stack)                                                   # set stack as central widget of main window, allowing for page switching

        # --- Build pages ---
        #self.settings_page = Build_Settings_Screen(self.start_game, self.engine)            # settings page: consists of sidebar + sub-pages
        self.settings_page = Build_Settings_Screen(self.start_game, self.qt_clear_list, self.engine)

        self.scoreboard_page = Build_Scoreboard_Screen(self.go_to_settings)                 # scoreboard page: consists of team tables + message box
        self.message_box = self.scoreboard_page.message_box

        # --- Add pages to stack ---
        self.stack.addWidget(self.settings_page)                                            # index 0
        self.stack.addWidget(self.scoreboard_page)                                          # index 1

        # Show settings first
        self.stack.setCurrentIndex(0)


    def keyPressEvent(self, event):
        if self.stack.currentWidget() is self.settings_page:
            if event.key() == Qt.Key_F5:
                self.start_game()
                return
            elif event.key() == Qt.Key_F12:
                qt_clear_list(self)
                return
        super().keyPressEvent(event)

    def qt_clear_list(self):
        self.engine.clear_player_list()
        # also clear the visible list in Settings UI
        lst = self.settings_page.findChild(QListWidget, "local_ui_player_list")
        if lst:
            lst.clear()
            print("Player List Cleared!")

    def start_game(self):
        self.refresh_scoreboard()
        self.start_game_countdown("Get Ready: ", 30, self.start_main_game)


    def start_main_game(self):
        self.refresh_scoreboard()
        self.start_game_countdown("Time Left: ", 360, self.stop_game)

        self.engine.start_game()
        self.stack.setCurrentIndex(1)

        # Start poll timer here
        self.poll_timer = QTimer(self)                                                      # poll: to regularly check for new events from the engine
        self.poll_timer.timeout.connect(self._poll_events)                                  # connect the timer's timeout signal to the _poll_events method
        self.poll_timer.start(200)                                                          # poll every 200 ms

    def stop_game(self):
        print("stopping game...")
        self.engine.stop_game

    def _poll_events(self):
        self.engine.process_pending_events()                                                # process any pending events in the engine
        self.refresh_scoreboard()                                                           # refresh scoreboard to display accurate data

    def refresh_scoreboard(self):
        players = list(self.engine.players.values())
        
        red_team   = [p for p in players if getattr(p, "team", "").lower() == "red"]
        green_team = [p for p in players if getattr(p, "team", "").lower() == "green"]

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

    def _populate_team_table(self, table: QTableWidget, team):
        if table is None:
            return
        table.setRowCount(len(team))
        for row, p in enumerate(team):
            name_item  = QTableWidgetItem(" " + p.username)
            score_item = QTableWidgetItem(str(p.score))

            # accept either attribute name
            has_icon = getattr(p, "has_base_icon", getattr(p, "has_icon", False))
            if has_icon:
                BASE_DIR = os.path.dirname(__file__)
                icon_path = os.path.join(BASE_DIR, "baseicon.jpg")
                if os.path.exists(icon_path):
                    icon = QPixmap(icon_path).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    name_item.setData(Qt.DecorationRole, icon)

            name_item.setTextAlignment(Qt.AlignLeft  | Qt.AlignVCenter)
            score_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, score_item)


    def go_to_settings(self):
        self.stack.setCurrentIndex(0)                                                       # traversal: switch to settings page

    def go_to_scoreboard(self):
        self.stack.setCurrentIndex(1)                                                       # traversal: switch to scoreboard page


    def start_game_countdown(self, message: str, count: int, func=None):
        self.stack.setCurrentIndex(1)
        self.countdown_label = self.scoreboard_page.findChild(QLabel, "countdownLabel")
        if not self.countdown_label:
            raise RuntimeError("QLabel 'countdownLabel' not found on scoreboard_page")

        self._message = message
        self._count = int(count)
        self.countdown_label.setText(f"{self._message}{self._count}")

        if getattr(self, "_countdown_timer", None):
            self._countdown_timer.stop()

        self._countdown_timer = QTimer(self)
        # pass a callable, don't call it
        self._countdown_timer.timeout.connect(partial(self._tick_game_countdown, func))
        self._countdown_timer.start(1000)

    def _tick_game_countdown(self, func):
        self._count -= 1

        # Start Music at 17 (For timing purposes)
        if self._count == 16:
            self.engine.start_music()

        if self._count < 0:
            self._countdown_timer.stop()
            self.countdown_label.clear()
            if callable(func):
                func()  # <— actually call it
            return
        self.countdown_label.setText(f"{self._message}{self._count}")



    def _poll_events(self):
        self.engine.process_pending_events()
        self.refresh_scoreboard()





# Simply used for showing the splash screen
def Start_App(app, window):
    splash = QLabel()                                                                       # splash screen is a QLabel; it will display an image
    pixmap = QPixmap("logo.jpg").scaled(720, 458, Qt.KeepAspectRatioByExpanding)            # load and scale the image to fit the splash screen size
    splash.setPixmap(pixmap)                                                                # set the loaded image to the scaled splash QLabel
    splash.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)                         # set window flags to make it a splash screen and frameless
    splash.setFixedSize(720, 458)                                                           # set fixed size for the splash screen
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

        line = QLineEdit() 
        line.setFixedWidth(430)
        line.setPlaceholderText(field["field_placeholder"])                                 # set placeholder text from field dict
        inputs.append(line)                                                                 # keep reference to line edit

        if field["button_text"] != "blank":
            button = QPushButton(field["button_text"])                                          # button with text from field dict
            button.setFixedSize(120, 30)
            buttons.append(button)

            func = field["button_func"]                                                         # get the function from the field dict
            button.clicked.connect(partial(func, line))                                         # pass the line itself after button is clicked
            row.addWidget(line)
            row.addStretch()
            row.addWidget(button)
        else:
            row.addWidget(line)                                                                 
            row.addStretch()
                                                                       
        box_layout.addLayout(row)                                                           # adds the row to the box layout, allowing it to be on our main box

    return box, {"inputs": inputs, "buttons": buttons}                                      # finally, return the box, inputs, and buttons for later reference



##### ADD USER PAGE (Settings Sub-Page) #####

def User_Page(start_callback, clear_local, engine):                                                                      # page for adding users to the game, allows for inputting of ID and searching for the player
    joined_codenames = set()
    local_ui_player_list = QListWidget()
    local_ui_player_list.setFixedSize(600, 400)
    local_ui_player_list.setObjectName("local_ui_player_list")
    local_ui_player_list.setStyleSheet("background-color: #333; color: white; font-size: 18px; padding: 3px;")

    def Search(line):
        try:
            player_id = int(line.text())                                                    # trys to get the player ID from the input line
            hw_id = int(hw_id_input.text().strip())
        except ValueError:
            search_button.setEnabled(False)                                                 # simple error handling for invalid input
            search_button.setText("Invalid ID")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")
            QTimer.singleShot(1500, Reset_User_UI)
            return

        result = search_player(player_id)
        codename = result.get("codename") if result else None


        if codename != None and codename in joined_codenames:
            print("username dupe!")
            search_button.setEnabled(False)                                                 # simple error handling for invalid input
            search_button.setText("User Dupe")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")
            QTimer.singleShot(1500, Reset_User_UI)
            return

        if codename != None and not engine.join_player(codename, hw_id):
            print("HWID Dupe!")
            search_button.setEnabled(False)                                                 # simple error handling for invalid input
            search_button.setText("HWID Dupe")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")
            QTimer.singleShot(1500, Reset_User_UI)
            return
            
        if codename != None and result:
            print("adding user")
            joined_codenames.add(codename)
            local_ui_player_list.addItem(f"{codename}({player_id}) HWID = {hw_id}")
            search_button.setEnabled(False)                                                 # disables the search button to prevent multiple clicks
            search_button.setText("Player Added!")                                          # changes button text to indicate success
            search_button.setStyleSheet("background-color: #2a2a2a; color: #33f533;")       # changes button color to green, representing validity
            QTimer.singleShot(1500, Reset_User_UI)                                          # resets the UI after 1.5 seconds, allowing for another search
        else:
            search_button.setEnabled(False)                                                     # disables the search button to prevent multiple clicks
            search_button.setText("Not Found")                                                  # changes button text to indicate failure
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")           # changes button color to red, representing invalidity
            codename_input.show()                                                               # shows the codename input field for user to enter a codename
            add_button.show()


    def Add_User(line):                                                                     # now to handle actually adding the player after searching for them
        player_id = int(id_input.text())
        codename = codename_input.text().strip()
        hw_id = int(hw_id_input.text().strip())

        success = add_player(player_id, codename)                                           # attempts to add the player to the DB, returns True if successful, False otherwise

        if not success and not engine.join_player(codename, hw_id):
            print("HWID Dupe!")
            search_button.setEnabled(False)                                                 # simple error handling for invalid input
            search_button.setText("HWID Dupe")
            search_button.setStyleSheet("background-color: #2a2a2a; color: #f53333;")
            QTimer.singleShot(1500, Reset_User_UI)
            return
        
        if success:
            engine.join_player(codename, hw_id)                                             # adds the player to the game engine
            local_ui_player_list.addItem(f"{codename}({player_id}) HWID = {hw_id}")                       # adds the player to the local UI list

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
        hw_id_input.clear()
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
            {"field_placeholder": "Enter HW ID...", "button_text": "blank", "button_func": None},
            {"field_placeholder": "Enter Codename", "button_text": "Add User", "button_func": Add_User}
        ]
    )

    # Easier refs
    id_input, hw_id_input, codename_input = refs["inputs"]                                               # gets references to the input fields
    search_button, add_button = refs["buttons"]                                             # gets references to the buttons

    codename_input.hide()
    add_button.hide()

    # Container for the "Players:" title + text box
    player_header = QWidget()
    header_layout = QHBoxLayout(player_header)
    header_layout.setContentsMargins(0, 0, 0, 0)

    header_label = QLabel("Players:")
    header_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
    header_layout.addWidget(header_label)

    # unused text box (just placed to the right)
    clear_players = QPushButton("Clear Players (F12)")
    clear_players.clicked.connect(clear_local)
    clear_players.setFixedWidth(180)
    header_layout.addStretch()
    header_layout.addWidget(clear_players)

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
def Build_Settings_Screen(start_callback, clear_local, engine):
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
    stack.addWidget(User_Page(start_callback, clear_local, engine))
    stack.addWidget(Network_Page(engine))
    body_layout.addWidget(stack, stretch=1)

    menu.currentRowChanged.connect(stack.setCurrentIndex)
    menu.setCurrentRow(0)

    main_layout.addLayout(body_layout)

    return container




#################################
######## SCOREBOARD PAGE ########
#################################

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
    countdown_label = QLabel()
    countdown_label.setObjectName("countdownLabel")
    countdown_label.setFixedSize(200, 20)
    countdown_label.setAlignment(Qt.AlignCenter)
    countdown_label.setStyleSheet("background-color: #1a1a1a; border: none; font-weight: bold; font-size: 18px; color: red;")
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
    message_box.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    message_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    message_box.setReadOnly(True)
    container.message_box = message_box
    h_layout.addWidget(message_box)
    
    for i in range(50):
        append_message(container.message_box, str(i))
        

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

