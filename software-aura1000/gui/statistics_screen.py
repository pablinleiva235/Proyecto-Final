import csv
import math
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
)

from config_gui.strings import (
    STATISTICS_TITLE,
    STATISTICS_PLACEHOLDER,
    STATISTICS_LOAD_DATA_TEXT,
    STATISTICS_NO_DATA,
    STATISTICS_LOAD_ERROR,
    BACK_BUTTON_TEXT,
)
import config_gui.strings as strings
from services.recipe_log import RECIPE_DATA_PATH, RECIPE_LOG_DIRECTORY


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
        metrics = painter.fontMetrics()
        values = [value for _, value in self.points]
        if values:
            low, high = min(values), max(values)
            if low == high:
                margin = max(abs(low) * 0.05, 1.0)
                low, high = low - margin, high + margin
            tick_width = max(
                metrics.horizontalAdvance(f"{low + fraction * (high - low):.3g}")
                for fraction in (0, .25, .5, .75, 1)
            )
        else:
            low = high = None
            tick_width = metrics.horizontalAdvance("0")

        left = tick_width + 18
        top = metrics.height() + 18
        right = self.width() - 16
        bottom = self.height() - metrics.height() - 12

        painter.setPen(self.palette().text().color())
        painter.drawText(left, metrics.ascent() + 4, f"{strings.tr(self.title)} ({self.unit})")
        if right <= left or bottom <= top:
            return
        if not values:
            painter.setPen(self.palette().mid().color())
            painter.drawText(left, (top + bottom) // 2, STATISTICS_PLACEHOLDER)
            return

        t_end = max(self.points[-1][0], 1.0)
        painter.setPen(QPen(self.palette().mid().color(), 1))
        for fraction in (0, .25, .5, .75, 1):
            y = bottom - fraction * (bottom - top)
            painter.drawLine(left, int(y), right, int(y))
            label = f"{low + fraction * (high-low):.3g}"
            painter.drawText(left - metrics.horizontalAdvance(label) - 8, int(y + metrics.ascent() / 2), label)
        painter.drawText(left, self.height() - metrics.descent() - 2, "0 s")
        end_label = f"{t_end:.0f} s"
        painter.drawText(right - metrics.horizontalAdvance(end_label), self.height() - metrics.descent() - 2, end_label)

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
        self._explicit_data_path = Path(data_path) if data_path is not None else None
        self.data_path = self._explicit_data_path or RECIPE_DATA_PATH
        self.create_widgets()
        self.setup_layout()
        self.connect_signals()
        self.refresh_data()

    def create_widgets(self):
        self.title_label = QLabel(STATISTICS_TITLE)
        self.title_label.setObjectName("StatisticsTitle")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label = QLabel(STATISTICS_PLACEHOLDER)
        self.subtitle_label.setObjectName("SubtitleLabel")
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setWordWrap(True)
        self.pressure_plot = ProcessPlot("Presión", "Torr", "#38BDF8")
        self.temperature_plot = ProcessPlot("Temperatura", "°C", "#FACC15")
        self.refresh_button = QPushButton(STATISTICS_LOAD_DATA_TEXT)
        self.back_button = QPushButton(BACK_BUTTON_TEXT)

    def setup_layout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 8, 16, 10)
        layout.setSpacing(6)
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
        self.refresh_button.clicked.connect(self.choose_data_file)
        self.back_button.clicked.connect(self.back_requested.emit)

    def refresh_data(self):
        if self._explicit_data_path is not None:
            self._load_data_file(self._explicit_data_path)
            return

        latest_path = self._latest_recipe_data_path()
        if latest_path is None:
            self.data_path = None
            self.subtitle_label.setText(strings.tr(STATISTICS_NO_DATA))
            self.pressure_plot.set_points([])
            self.temperature_plot.set_points([])
            return
        self._load_data_file(latest_path)

    @staticmethod
    def _latest_recipe_data_path():
        try:
            paths = RECIPE_LOG_DIRECTORY.glob("recipe_data_*.csv")
            return max(paths, key=lambda path: path.stat().st_mtime_ns, default=None)
        except OSError:
            return None

    def choose_data_file(self):
        try:
            available_files = list(RECIPE_LOG_DIRECTORY.glob("recipe_data_*.csv"))
        except OSError:
            available_files = []
        if not available_files:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            strings.tr(STATISTICS_LOAD_DATA_TEXT),
            str(RECIPE_LOG_DIRECTORY),
            "CSV (*.csv)",
        )
        if path:
            self._load_data_file(Path(path))

    def _load_data_file(self, path):
        path = Path(path)
        data = {"BARATRON": [], "CHAMBER_TEMP": []}
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as data_file:
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
        except (OSError, csv.Error, UnicodeError):
            self.subtitle_label.setText(strings.tr(
                STATISTICS_LOAD_ERROR.format(filename=path.name)
            ))
            return False

        all_times = [timestamp for readings in data.values() for timestamp, _ in readings]
        start = min(all_times) if all_times else None
        for signal, plot in (("BARATRON", self.pressure_plot), ("CHAMBER_TEMP", self.temperature_plot)):
            readings = sorted(data[signal], key=lambda item: item[0])
            plot.set_points([
                (max(0.0, (timestamp - start).total_seconds()), value)
                for timestamp, value in readings
            ] if start else [])

        count = sum(map(len, data.values()))
        self.data_path = path
        subtitle = (
            f"{path.name} · {count} lecturas guardadas"
            if count else f"{path.name} · sin lecturas guardadas"
        )
        self.subtitle_label.setText(strings.tr(subtitle))
        return True
