from PyQt6.QtWidgets import QMainWindow, QTabWidget
from ui.log_session_tab import LogSessionTab
from ui.calendar_tab import CalendarTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Art Practice Tracker")
        self.setMinimumSize(460, 560)

        tabs = QTabWidget()

        self.log_tab = LogSessionTab()
        self.calendar_tab = CalendarTab()

        tabs.addTab(self.log_tab, "Log session")
        tabs.addTab(self.calendar_tab, "Calendar")

        # Refresh the calendar's highlights whenever you switch to it,
        # so a session you just logged shows up immediately
        tabs.currentChanged.connect(self.on_tab_changed)
        self.tabs = tabs

        self.setCentralWidget(tabs)

    def on_tab_changed(self, index):
        if self.tabs.widget(index) is self.calendar_tab:
            self.calendar_tab.refresh_highlights()