import csv
import math
from datetime import datetime

from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout

from config_gui.strings import (
    STATISTICS_TITLE,
    STATISTICS_PLACEHOLDER,
    BACK_BUTTON_TEXT,
)
import config_gui.strings as strings
from services.recipe_log import RECIPE_DATA_PATH


class ProcessPlot(QWidget):
    """Gráfico liviano pintado con Qt para no agregar dependencias externas."""

    def __init__(self, title, unit, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.color = QColor(color)
        self.points = []
        self.setMinimumHeight(190)

    def set_points(self, points):
        self.points = points
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.palette().text().color())
        painter.drawText(8, 22, f"{strings.tr(self.title)} ({self.unit})")

        left, top, right, bottom = 58, 36, self.width() - 18, self.height() - 34
        if right <= left or bottom <= top:
            return
        values = [value for _, value in self.points]
        if not values:
            painter.setPen(self.palette().mid().color())
            painter.drawText(left, (top + bottom) // 2, STATISTICS_PLACEHOLDER)
            return

        low, high = min(values), max(values)
        if low == high:
            margin = max(abs(low) * 0.05, 1.0)
            low, high = low - margin, high + margin
        t_end = max(self.points[-1][0], 1.0)
        painter.setPen(QPen(self.palette().mid().color(), 1))
        for fraction in (0, .25, .5, .75, 1):
            y = bottom - fraction * (bottom - top)
            painter.drawLine(left, int(y), right, int(y))
            painter.drawText(2, int(y + 5), f"{low + fraction * (high-low):.3g}")
        painter.drawText(left, self.height() - 8, "0 s")
        painter.drawText(right - 42, self.height() - 8, f"{t_end:.0f} s")

        path = QPainterPath()
        for index, (seconds, value) in enumerate(self.points):
            x = left + seconds / t_end * (right - left)
            y = bottom - (value - low) / (high - low) * (bottom - top)
            point = QPointF(x, y)
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)
        painter.setPen(QPen(self.color, 2))
        painter.drawPath(path)


class StatisticsScreen(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, data_path=None):
        super().__init__()
        self.data_path = data_path or RECIPE_DATA_PATH
        self.create_widgets()
        self.setup_layout()
        self.connect_signals()
        self.refresh_data()

    def create_widgets(self):
        self.title_label = QLabel(STATISTICS_TITLE)
        self.title_label.setObjectName("TitleLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label = QLabel(STATISTICS_PLACEHOLDER)
        self.subtitle_label.setObjectName("SubtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.pressure_plot = ProcessPlot("Presión", "Torr", "#38BDF8")
        self.temperature_plot = ProcessPlot("Temperatura", "°C", "#FACC15")
        self.refresh_button = QPushButton("Actualizar gráficos")
        self.back_button = QPushButton(BACK_BUTTON_TEXT)

    def setup_layout(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.pressure_plot, 1)
        layout.addWidget(self.temperature_plot, 1)
        buttons = QHBoxLayout()
        buttons.addWidget(self.refresh_button)
        buttons.addWidget(self.back_button)
        layout.addLayout(buttons)
        self.setLayout(layout)

    def connect_signals(self):
        self.refresh_button.clicked.connect(self.refresh_data)
        self.back_button.clicked.connect(self.back_requested.emit)

    def refresh_data(self):
        data = {"BARATRON": [], "CHAMBER_TEMP": []}
        try:
            with open(self.data_path, "r", encoding="utf-8-sig", newline="") as data_file:
                for row in csv.DictReader(data_file):
                    signal = row.get("señal") or row.get("seÃ±al") or row.get("signal")
                    if signal not in data:
                        continue
                    try:
                        timestamp = datetime.fromisoformat(row["timestamp"])
                        value = float(row["valor"] if "valor" in row else row["value"])
                        if not math.isfinite(value):
                            continue
                    except (KeyError, TypeError, ValueError, OverflowError):
                        continue
                    data[signal].append((timestamp, value))
        except (OSError, csv.Error):
            pass

        all_times = [timestamp for readings in data.values() for timestamp, _ in readings]
        start = min(all_times) if all_times else None
        for signal, plot in (("BARATRON", self.pressure_plot), ("CHAMBER_TEMP", self.temperature_plot)):
            readings = sorted(data[signal], key=lambda item: item[0])
            plot.set_points([
                (max(0.0, (timestamp - start).total_seconds()), value)
                for timestamp, value in readings
            ] if start else [])

        count = sum(map(len, data.values()))
        subtitle = (
            f"Última receta ejecutada · {count} lecturas guardadas"
            if count else "No hay datos guardados de una receta ejecutada."
        )
        self.subtitle_label.setText(strings.tr(subtitle))
