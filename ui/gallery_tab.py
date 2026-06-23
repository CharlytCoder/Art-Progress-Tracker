import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGridLayout, QLabel, QSizePolicy
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from database import get_connection

IMAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
MIN_THUMB_SIZE = 120
MAX_THUMB_SIZE = 220


class Thumbnail(QWidget):
    """A single flexible image + caption block in the gallery grid."""

    def __init__(self, image_path: str, caption_text: str):
        super().__init__()
        self.image_path = image_path
        self._pixmap = QPixmap(image_path)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setStyleSheet("""
            background-color: #F0EFEA;
            border: 1px solid #DDDAD2;
            border-radius: 8px;
        """)
        self.image_label.setContentsMargins(8, 8, 8, 8)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        layout.addWidget(self.image_label, stretch=1)

        caption = QLabel(caption_text)
        caption.setStyleSheet("font-size: 11px; color: #555;")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(caption)

        self.setLayout(layout)
        self.setMinimumSize(MIN_THUMB_SIZE, MIN_THUMB_SIZE + 20)
        self.setMaximumWidth(MAX_THUMB_SIZE)
        self.setMaximumHeight(MAX_THUMB_SIZE + 30)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self):
        if self._pixmap.isNull() or self.image_label.width() <= 0:
            return
        size = self.image_label.size()
        scaled = self._pixmap.scaled(
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)


class GalleryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.rows_data = []
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def refresh(self):
        conn = get_connection()
        rows = conn.execute("""
            SELECT images.filename, sessions.date, sessions.art_type
            FROM images
            JOIN sessions ON images.session_id = sessions.id
            ORDER BY images.uploaded_at DESC
        """).fetchall()
        conn.close()

        self.rows_data = rows
        self.empty_label.setVisible(len(rows) == 0)
        self._rebuild_thumbnails()

    def _rebuild_thumbnails(self):
        # Clear existing thumbnails
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self._thumbnails = []
        for row in self.rows_data:
            image_path = os.path.join(IMAGES_DIR, row["filename"])
            caption = f"{row['date']} — {row['art_type']}"
            self._thumbnails.append(Thumbnail(image_path, caption))

        self._relayout()

    def _relayout(self):
        """Recompute how many columns fit the current width and re-place thumbnails."""
        if not getattr(self, "_thumbnails", None):
            return

        available_width = self.scroll_area.viewport().width()
        target_col_width = MIN_THUMB_SIZE + 40
        columns = max(1, available_width // target_col_width)

        if getattr(self, "_current_columns", None) == columns:
            return  # nothing to do, avoids unnecessary re-layout thrashing
        self._current_columns = columns

        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        for col in range(columns): 
            self.grid_layout.setColumnStretch(col, 1)

        for index, thumb in enumerate(self._thumbnails):
            r, c = divmod(index, columns)
            self.grid_layout.addWidget(thumb, r, c)