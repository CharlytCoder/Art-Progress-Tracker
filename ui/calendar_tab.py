import os
import calendar as cal
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QTextEdit, QSizePolicy
)
from PyQt6.QtCore import Qt
from database import get_connection

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
THUMB_SIZE = 140
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class DayCell(QPushButton):
    """A single clickable day cell in the calendar grid."""

    def __init__(self, day_number, date_str, parent_tab):
        super().__init__(str(day_number))
        self.date_str = date_str
        self.parent_tab = parent_tab
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(36, 36)  # keeps cells from getting too cramped
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.on_click)
        self.set_practiced(False)

    def set_practiced(self, practiced: bool, image_path: str | None = None):
        if practiced:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #9FE1CB;
                    color: #04342C;
                    border-radius: 8px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #7FD4B8; }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #F4F4F4;
                    color: #333;
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #E8E8E8; }
            """)

        if image_path and os.path.exists(image_path):
            self.setToolTip(f'<img src="{image_path}" width="{THUMB_SIZE}">')
        else:
            self.setToolTip("")

    def on_click(self):
        self.parent_tab.show_day_detail(self.date_str)


class CustomCalendar(QWidget):
    """A self-contained month calendar built from a grid of DayCell buttons."""

    def __init__(self, parent_tab):
        super().__init__()
        self.parent_tab = parent_tab
        self.current_year = date.today().year
        self.current_month = date.today().month
        self.cells = {}  # date_str -> DayCell

        self.build_ui()
        self.render_month()

    def build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Header: prev button, month/year label, next button
        header = QHBoxLayout()
        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedWidth(36)
        self.prev_btn.clicked.connect(self.go_previous_month)

        self.month_label = QLabel()
        self.month_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton(">")
        self.next_btn.setFixedWidth(36)
        self.next_btn.clicked.connect(self.go_next_month)

        header.addWidget(self.prev_btn)
        header.addWidget(self.month_label, stretch=1)
        header.addWidget(self.next_btn)
        layout.addLayout(header)

        # Day-of-week labels
        dow_row = QHBoxLayout()
        for name in DAY_NAMES:
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #888; font-size: 11px;")
            lbl.setFixedWidth(56)
            dow_row.addWidget(lbl)
        layout.addLayout(dow_row)

        # Grid of day cells
        self.grid = QGridLayout()
        self.grid.setSpacing(6)
        layout.addLayout(self.grid)

        self.setLayout(layout)

    def go_previous_month(self):
        self.current_month -= 1
        if self.current_month == 0:
            self.current_month = 12
            self.current_year -= 1
        self.render_month()
        self.parent_tab.apply_highlights()

    def go_next_month(self):
        self.current_month += 1
        if self.current_month == 13:
            self.current_month = 1
            self.current_year += 1
        self.render_month()
        self.parent_tab.apply_highlights()

    def render_month(self):
        # Clear existing cells
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.cells = {}

        self.month_label.setText(
            f"{cal.month_name[self.current_month]} {self.current_year}"
        )

        # calendar.Calendar() with firstweekday=0 starts weeks on Monday
        month_calendar = cal.Calendar(firstweekday=0)
        weeks = month_calendar.monthdayscalendar(self.current_year, self.current_month)

        for row_index, week in enumerate(weeks):
            for col_index, day_number in enumerate(week):
                if day_number == 0:
                    continue  # day belongs to prev/next month, leave blank
                date_str = date(self.current_year, self.current_month, day_number).isoformat()
                cell = DayCell(day_number, date_str, self.parent_tab)
                self.grid.addWidget(cell, row_index, col_index)
                self.cells[date_str] = cell

        


class CalendarTab(QWidget):
    def __init__(self):
        super().__init__()
        self.build_ui()
        self.apply_highlights()

    def build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Practice calendar")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.calendar = CustomCalendar(self)
        layout.addWidget(self.calendar)

        hint = QLabel("Hover a highlighted day to preview your artwork")
        hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hint)

        self.detail_label = QLabel("Click a day to see what you practiced")
        self.detail_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.detail_label)

        self.detail_box = QTextEdit()
        self.detail_box.setReadOnly(True)
        self.detail_box.setMaximumHeight(100)
        layout.addWidget(self.detail_box)

        self.setLayout(layout)

    def apply_highlights(self):
        """Tell every visible day cell whether it was practiced,
        and attach a thumbnail tooltip if a photo exists for that day."""
        conn = get_connection()
        session_dates = {
            row["date"] for row in conn.execute("SELECT DISTINCT date FROM sessions").fetchall()
        }

        image_rows = conn.execute("""
            SELECT sessions.date, images.filename
            FROM images
            JOIN sessions ON images.session_id = sessions.id
            ORDER BY images.uploaded_at DESC
        """).fetchall()
        conn.close()

        thumb_by_date = {}
        for row in image_rows:
            if row["date"] not in thumb_by_date:
                thumb_by_date[row["date"]] = row["filename"]

        for date_str, cell in self.calendar.cells.items():
            practiced = date_str in session_dates
            image_path = None
            if date_str in thumb_by_date:
                image_path = os.path.join(IMAGES_DIR, thumb_by_date[date_str])
            cell.set_practiced(practiced, image_path)

    def refresh_highlights(self):
        """Kept for compatibility with main_window's tab-switch hook."""
        self.apply_highlights()

    def show_day_detail(self, date_str: str):
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM sessions WHERE date = ?", (date_str,)
        ).fetchall()
        conn.close()

        if not rows:
            self.detail_label.setText(f"{date_str} — no sessions logged")
            self.detail_box.setPlainText("")
            return

        self.detail_label.setText(f"{date_str} — {len(rows)} session(s)")
        lines = []
        for r in rows:
            line = f"• {r['art_type']}, {r['duration_minutes']} min"
            if r["notes"]:
                line += f" — {r['notes']}"
            lines.append(line)
        self.detail_box.setPlainText("\n".join(lines))