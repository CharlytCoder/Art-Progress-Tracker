from datetime import date, timedelta
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt
from database import get_connection


class BarChart(QWidget):
    """A minimal custom bar chart comparing practice time by art type."""

    def __init__(self):
        super().__init__()
        self.data = {}  # e.g. {"Drawing": 120, "Digital art": 45}
        self.setMinimumHeight(180)

    def set_data(self, data: dict):
        self.data = data
        self.update()  # triggers a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.data:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No data yet")
            return

        width = self.width()
        height = self.height()
        padding = 30
        max_value = max(self.data.values()) if self.data.values() else 1
        max_value = max(max_value, 1)  # avoid divide-by-zero

        bar_count = len(self.data)
        bar_area_width = width - (padding * 2)
        bar_width = bar_area_width / bar_count * 0.5
        gap = bar_area_width / bar_count

        colors = [QColor("#7BC8A4"), QColor("#7AA7E0"), QColor("#E0A37A"), QColor("#B57AE0")]

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        for i, (label, value) in enumerate(self.data.items()):
            bar_height = (value / max_value) * (height - padding * 2)
            x = padding + i * gap + (gap - bar_width) / 2
            y = height - padding - bar_height

            painter.setBrush(colors[i % len(colors)])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_height), 4, 4)

            painter.setPen(QColor("#222222"))
            painter.drawText(
                int(x - 10), int(y - 18), int(bar_width + 20), 16,
                Qt.AlignmentFlag.AlignCenter, f"{value} min"
            )
            painter.drawText(
                int(x - 10), height - padding + 4, int(bar_width + 20), 20,
                Qt.AlignmentFlag.AlignCenter, label
            )


class StatCard(QFrame):
    """A small labeled box for a single stat, e.g. Total time: 4h 30m"""

    def __init__(self, title: str):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            "QFrame { background-color: #F4F4F4; border-radius: 10px; padding: 8px; }"
        )

        layout = QVBoxLayout()

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 12px; color: #666;")

        self.value_label = QLabel("—")
        self.value_label.setStyleSheet("font-size: 22px; font-weight: bold;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def set_value(self, value: str):
        self.value_label.setText(value)


class StatsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Your stats")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        cards_row = QHBoxLayout()
        self.total_card = StatCard("Total practice time")
        self.streak_card = StatCard("Current streak")
        self.sessions_card = StatCard("Sessions logged")
        cards_row.addWidget(self.total_card)
        cards_row.addWidget(self.streak_card)
        cards_row.addWidget(self.sessions_card)
        layout.addLayout(cards_row)

        chart_label = QLabel("Time by art type")
        chart_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(chart_label)

        self.chart = BarChart()
        layout.addWidget(self.chart)

        layout.addStretch()
        self.setLayout(layout)

    def refresh(self):
        conn = get_connection()
        rows = conn.execute("SELECT date, duration_minutes, art_type FROM sessions").fetchall()
        conn.close()

        total_minutes = sum(r["duration_minutes"] for r in rows)
        session_count = len(rows)
        practiced_dates = {r["date"] for r in rows}

        # Total time, formatted as Xh Ym
        hours, minutes = divmod(total_minutes, 60)
        self.total_card.set_value(f"{hours}h {minutes}m")

        # Sessions count
        self.sessions_card.set_value(str(session_count))

        # Streak: walk backward from today while each day is in practiced_dates
        streak = 0
        cursor_date = date.today()
        while cursor_date.isoformat() in practiced_dates:
            streak += 1
            cursor_date -= timedelta(days=1)
        self.streak_card.set_value(f"{streak} day{'s' if streak != 1 else ''}")

        # Breakdown by art type
        breakdown = {}
        for r in rows:
            breakdown[r["art_type"]] = breakdown.get(r["art_type"], 0) + r["duration_minutes"]
        self.chart.set_data(breakdown)