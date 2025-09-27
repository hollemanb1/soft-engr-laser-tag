import sys, json
#from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from qt_header import init_app, ScoreboardWindow, Start_App, Setup_Screen, Start_Button_Page, Scoreboard_Page




if __name__ == "__main__":
    app = init_app()
    window = ScoreboardWindow()

    Start_App(app, window)

    window.layout.addWidget(Setup_Screen())

    sys.exit(app.exec())
