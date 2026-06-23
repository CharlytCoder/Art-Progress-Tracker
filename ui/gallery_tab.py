import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QGridLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from database import get_connection

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
THUMB_SIZE = 160


class GalleryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.build_ui()

    def build_ui(self):
        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Your artwork")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        outer_layout.addWidget(title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(16)
        self.grid_container.setLayout(self.grid_layout)

        self.scroll_area.setWidget(self.grid_container)
        outer_layout.addWidget(self.scroll_area)

        self.empty_label = QLabel("No images uploaded yet")
        self.empty_label.setStyleSheet("color: #888;")
        outer_layout.addWidget(self.empty_label)

        self.setLayout(outer_layout)

    def refresh(self):
        # Clear existing thumbnails
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        conn = get_connection()
        rows = conn.execute("""
            SELECT images.filename, sessions.date, sessions.art_type
            FROM images
            JOIN sessions ON images.session_id = sessions.id
            ORDER BY images.uploaded_at DESC
        """).fetchall()
        conn.close()

        self.empty_label.setVisible(len(rows) == 0)

        columns = 3
        for index, row in enumerate(rows):
            thumb_widget = self.build_thumbnail(row)
            r, c = divmod(index, columns)
            self.grid_layout.addWidget(thumb_widget, r, c)

    def build_thumbnail(self, row):
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        image_label = QLabel()
        image_path = os.path.join(IMAGES_DIR, row["filename"])
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                THUMB_SIZE, THUMB_SIZE,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
        image_label.setPixmap(pixmap)
        image_label.setFixedSize(THUMB_SIZE, THUMB_SIZE)
        image_label.setStyleSheet("border-radius: 8px; background-color: #eee;")
        image_label.setScaledContents(False)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        caption = QLabel(f"{row['date']} — {row['art_type']}")
        caption.setStyleSheet("font-size: 11px; color: #555;")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(image_label)
        layout.addWidget(caption)
        container.setLayout(layout)
        return container