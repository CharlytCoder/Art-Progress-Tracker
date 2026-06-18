from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QComboBox, QSpinBox, QTextEdit, QPushButton, QMessageBox
)
from database import get_connection


class LogSessionTab(QWidget):
    def __init__(self):
        super().__init__()
        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Log a practice session")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Art type"))
        self.art_type_combo = QComboBox()
        self.art_type_combo.addItems(["Drawing", "Digital art"])
        layout.addWidget(self.art_type_combo)

        layout.addWidget(QLabel("Duration (minutes)"))
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 600)
        self.duration_spin.setValue(30)
        layout.addWidget(self.duration_spin)

        layout.addWidget(QLabel("Notes (optional)"))
        self.notes_box = QTextEdit()
        self.notes_box.setPlaceholderText("What did you work on?")
        self.notes_box.setMaximumHeight(100)
        layout.addWidget(self.notes_box)

        save_btn = QPushButton("Save session")
        save_btn.clicked.connect(self.save_session)
        layout.addWidget(save_btn)

        layout.addStretch()
        self.setLayout(layout)

    def save_session(self):
        art_type = self.art_type_combo.currentText()
        duration = self.duration_spin.value()
        notes = self.notes_box.toPlainText().strip()
        today = date.today().isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (date, duration_minutes, art_type, notes) VALUES (?, ?, ?, ?)",
            (today, duration, art_type, notes)
        )
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Saved", f"Logged {duration} minutes of {art_type}!")
        self.notes_box.clear()
        self.duration_spin.setValue(30)