import sys
from PyQt6.QtWidgets import QApplication
from database import init_db
from ui.main_window import MainWindow


if __name__ == "__main__":
    init_db()
    #print("Database initialized.") 

    #open the main application window
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())