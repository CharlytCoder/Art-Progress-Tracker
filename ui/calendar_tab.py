from PyQt6.QtWidgets import QWidget, QVBoxLayout, QCalendarWidget, QLabel, QTextEdit
from PyQt6.QtGui import QTextCharFormat, QColor
from PyQt6.QtCore import QDate
from database import get_connection


class CalendarTab(QWidget):
    def __init__(self):
        super().__init__()
        self.build_ui()
        self.refresh_highlights()
        self.calendar.clicked.connect(self.show_day_detail)

    def build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Practice calendar")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        self.calendar = QCalendarWidget()
        layout.addWidget(self.calendar)

        self.detail_label = QLabel("Click a day to see what you practiced")
        self.detail_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.detail_label)

        self.detail_box = QTextEdit()
        self.detail_box.setReadOnly(True)
        self.detail_box.setMaximumHeight(100)
        layout.addWidget(self.detail_box)

        self.setLayout(layout)

    def refresh_highlights(self):
        """Mark every day that has at least one logged session."""
        conn = get_connection()
        rows = conn.execute("SELECT DISTINCT date FROM sessions").fetchall()
        conn.close()

        practiced_format = QTextCharFormat()
        practiced_format.setBackground(QColor("#9FE1CB"))  # soft teal
        practiced_format.setForeground(QColor("#04342C"))

        for row in rows:
            qdate = QDate.fromString(row["date"], "yyyy-MM-dd")
            self.calendar.setDateTextFormat(qdate, practiced_format)

    def show_day_detail(self, qdate: QDate):
        date_str = qdate.toString("yyyy-MM-dd")
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