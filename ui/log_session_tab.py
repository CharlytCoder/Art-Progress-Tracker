import os
import shutil
import uuid
from datetime import date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QComboBox, QSpinBox, QTextEdit, QPushButton, QMessageBox, QFileDialog
)
from database import get_connection

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")


class LogSessionTab(QWidget):
    def __init__(self):
        super().__init__()
        self.last_session_id = None
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

        self.attach_btn = QPushButton("Attach image to this session")
        self.attach_btn.clicked.connect(self.attach_image)
        self.attach_btn.setEnabled(False)
        layout.addWidget(self.attach_btn)

        self.attach_status = QLabel("")
        self.attach_status.setStyleSheet("color: #2E7D32;")
        layout.addWidget(self.attach_status)

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
        self.last_session_id = cursor.lastrowid
        conn.close()

        QMessageBox.information(self, "Saved", f"Logged {duration} minutes of {art_type}!")
        self.notes_box.clear()
        self.duration_spin.setValue(30)

        self.attach_btn.setEnabled(True)
        self.attach_status.setText("")

    def attach_image(self):
        if self.last_session_id is None:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select an image", "", "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if not file_path:
            return

        os.makedirs(IMAGES_DIR, exist_ok=True)

        ext = os.path.splitext(file_path)[1]
        new_filename = f"{uuid.uuid4().hex}{ext}"
        dest_path = os.path.join(IMAGES_DIR, new_filename)
        shutil.copy2(file_path, dest_path)

        conn = get_connection()
        conn.execute(
            "INSERT INTO images (session_id, filename) VALUES (?, ?)",
            (self.last_session_id, new_filename)
        )
        conn.commit()
        conn.close()

        self.attach_status.setText(f"Image attached ✓ ({os.path.basename(file_path)})")