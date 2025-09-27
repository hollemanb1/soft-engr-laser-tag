from PySide6.QtWidgets import QApplication, QPushButton
import sys

app = QApplication(sys.argv)
app.setStyleSheet("""
QPushButton {
    background-color: #444;
    color: white;
    padding: 6px;
}
QPushButton:hover {
    background-color: red;
}
""")

btn = QPushButton("Hover me")
btn.show()

sys.exit(app.exec())
