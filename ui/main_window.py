from PyQt6.QtWidgets import QMainWindow, QTabWidget
from ui.log_session_tab import LogSessionTab
from ui.calendar_tab import CalendarTab
from ui.stats_tab import StatsTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Art Practice Tracker")
        self.setMinimumSize(460, 560)

        tabs = QTabWidget()

        self.log_tab = LogSessionTab()
        self.calendar_tab = CalendarTab()
        self.stats_tab = StatsTab()

        tabs.addTab(self.log_tab, "Log session")
        tabs.addTab(self.calendar_tab, "Calendar")
        tabs.addTab(self.stats_tab, "Stats")

        tabs.currentChanged.connect(self.on_tab_changed)
        self.tabs = tabs

        self.setCentralWidget(tabs)

    def on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if widget is self.calendar_tab:
            self.calendar_tab.refresh_highlights()
        elif widget is self.stats_tab:
            self.stats_tab.refresh()