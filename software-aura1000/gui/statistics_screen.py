import csv
import math
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
    QScrollArea, QTabWidget, QTextEdit,
)

from config_gui.strings import (
    STATISTICS_TITLE,
    STATISTICS_PLACEHOLDER,
    STATISTICS_LOAD_DATA_TEXT,
    STATISTICS_NO_DATA,
    STATISTICS_LOAD_ERROR,
    STATISTICS_DATA_TAB,
    STATISTICS_LOGS_TAB,
    STATISTICS_LOAD_LOG_TEXT,
    STATISTICS_LOAD_FILE_TEXT,
    STATISTICS_NO_LOGS,
    STATISTICS_LOG_LOAD_ERROR,
    BACK_BUTTON_TEXT,
)
import config_gui.strings as strings
from services.recipe_log import RECIPE_DATA_PATH, RECIPE_LOG_DIRECTORY
from services.maintenance_data_log import MAINTENANCE_COLUMNS, MAINTENANCE_DATA_DIRECTORY
from services.shutdown_log import SHUTDOWN_LOG_DIRECTORY


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
        self.refresh_logs()

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
        self.mfc1_plot = ProcessPlot("MFC1", "SLPM", "#34D399")
        self.mfc2_plot = ProcessPlot("MFC2", "SLPM", "#A78BFA")
        self.throttle_plot = ProcessPlot("Posición throttle", "pasos", "#FB7185")
        self.plasma_plot = ProcessPlot("Estado plasma", "0 apagado / 1 encendido", "#F97316")
        self.signal_plots = {
            "BARATRON": self.pressure_plot, "CHAMBER_TEMP": self.temperature_plot,
            "MFC1_FLOW": self.mfc1_plot, "MFC2_FLOW": self.mfc2_plot,
            "THROTTLE_POSITION": self.throttle_plot, "PLASMA": self.plasma_plot,
        }
        self.load_file_button = QPushButton(STATISTICS_LOAD_FILE_TEXT)
        self.load_file_button.setObjectName("StatisticsLoadFileButton")
        # Backwards-compatible attribute for callers that refresh CSV data.
        self.refresh_button = self.load_file_button
        self.log_path = None
        self.logs_title_label = QLabel(STATISTICS_NO_LOGS)
        self.logs_title_label.setObjectName("SubtitleLabel")
        self.logs_view = QTextEdit()
        self.logs_view.setReadOnly(True)
        self.logs_view.setLineWrapMode(QTextEdit.NoWrap)
        self.back_button = QPushButton(BACK_BUTTON_TEXT)
        self.back_button.setObjectName("StatisticsBackButton")

    def setup_layout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 8, 16, 10)
        layout.setSpacing(6)
        layout.addWidget(self.title_label)
        self.tabs = QTabWidget()
        self.tabs.setObjectName("StatisticsTabs")
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        data_layout.setContentsMargins(0, 0, 0, 0)
        data_layout.addWidget(self.subtitle_label)
        plots_container = QWidget()
        plots_layout = QVBoxLayout(plots_container)
        plots_layout.setContentsMargins(0, 0, 0, 0)
        for plot in self.signal_plots.values():
            plots_layout.addWidget(plot)
        self.plots_scroll = QScrollArea()
        self.plots_scroll.setWidgetResizable(True)
        self.plots_scroll.setWidget(plots_container)
        data_layout.addWidget(self.plots_scroll, 1)
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        logs_layout.setContentsMargins(0, 0, 0, 0)
        logs_layout.addWidget(self.logs_title_label)
        logs_layout.addWidget(self.logs_view, 1)
        self.tabs.addTab(data_tab, STATISTICS_DATA_TAB)
        self.tabs.addTab(logs_tab, STATISTICS_LOGS_TAB)
        layout.addWidget(self.tabs, 1)
        self.footer_buttons = QHBoxLayout()
        self.footer_buttons.addWidget(self.load_file_button, 1)
        self.footer_buttons.addWidget(self.back_button, 1)
        layout.addLayout(self.footer_buttons)
        self.setLayout(layout)

    def connect_signals(self):
        self.load_file_button.clicked.connect(self.choose_active_file)
        self.back_button.clicked.connect(self.back_requested.emit)

    def choose_active_file(self):
        if self.tabs.currentIndex() == 1:
            self.choose_log_file()
        else:
            self.choose_data_file()

    def refresh_data(self):
        if self._explicit_data_path is not None:
            self._load_data_file(self._explicit_data_path)
            return

        latest_path = self._latest_data_path()
        if latest_path is None:
            self.data_path = None
            self.subtitle_label.setText(strings.tr(STATISTICS_NO_DATA))
            for plot in self.signal_plots.values():
                plot.set_points([])
            return
        self._load_data_file(latest_path)

    @staticmethod
    def _available_data_files():
        paths = set()
        try:
            paths.update(RECIPE_LOG_DIRECTORY.glob("recipe_data_*.csv"))
            paths.update(RECIPE_DATA_PATH.parent.glob("recipe_data*.csv"))
            paths.update(MAINTENANCE_DATA_DIRECTORY.glob("mantenimiento_*.csv"))
        except OSError:
            pass
        return list(paths)

    @classmethod
    def _latest_data_path(cls):
        try:
            return max(cls._available_data_files(), key=lambda path: path.stat().st_mtime_ns, default=None)
        except OSError:
            return None

    @staticmethod
    def _latest_recipe_data_path():
        try:
            paths = RECIPE_LOG_DIRECTORY.glob("recipe_data_*.csv")
            return max(paths, key=lambda path: path.stat().st_mtime_ns, default=None)
        except OSError:
            return None

    @staticmethod
    def _available_log_files():
        paths = set()
        for directory, pattern in (
            (RECIPE_LOG_DIRECTORY, "recipe_*.log"),
            (SHUTDOWN_LOG_DIRECTORY, "shutdown_*.log"),
        ):
            try:
                paths.update(directory.glob(pattern))
            except OSError:
                continue
        return list(paths)

    @classmethod
    def _latest_log_path(cls):
        try:
            return max(
                cls._available_log_files(),
                key=lambda path: path.stat().st_mtime_ns,
                default=None,
            )
        except OSError:
            return None

    def refresh_logs(self):
        path = self._latest_log_path()
        if path is None:
            self.log_path = None
            self.logs_title_label.setText(strings.tr(STATISTICS_NO_LOGS))
            self.logs_view.clear()
            return
        self._load_log_file(path)

    def choose_log_file(self):
        available_files = self._available_log_files()
        if not available_files:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            strings.tr(STATISTICS_LOAD_LOG_TEXT),
            str(available_files[0].parent),
            "Logs (*.log)",
        )
        if path:
            self._load_log_file(Path(path))

    def _load_log_file(self, path):
        path = Path(path)
        try:
            content = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            self.logs_title_label.setText(strings.tr(
                STATISTICS_LOG_LOAD_ERROR.format(filename=path.name)
            ))
            return False
        self.log_path = path
        self.logs_title_label.setText(path.name)
        self.logs_view.setPlainText(content)
        return True

    def choose_data_file(self):
        try:
            available_files = self._available_data_files()
        except OSError:
            available_files = []
        if not available_files:
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            strings.tr(STATISTICS_LOAD_DATA_TEXT),
            str(available_files[0].parent),
            "CSV (*.csv)",
        )
        if path:
            self._load_data_file(Path(path))

    def _load_data_file(self, path):
        path = Path(path)
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as file_handle:
                headers = next(csv.reader(file_handle), [])
            if any(column == "pressure_Torr" for column in headers):
                return self._load_maintenance_data_file(path)
        except (OSError, csv.Error, UnicodeError):
            pass
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
        for signal, plot in self.signal_plots.items():
            readings = sorted(data.get(signal, []), key=lambda item: item[0])
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

    def _load_maintenance_data_file(self, path):
        signals_by_column = {column: signal for column, signal, _ in MAINTENANCE_COLUMNS}
        data = {signal: [] for signal in self.signal_plots}
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as data_file:
                for row in csv.DictReader(data_file):
                    try:
                        timestamp = datetime.fromisoformat(row.get("timestamp", ""))
                    except (TypeError, ValueError, OverflowError):
                        continue
                    for column, signal in signals_by_column.items():
                        raw = row.get(column, "")
                        if raw in (None, ""):
                            continue
                        if signal == "PLASMA":
                            state = str(raw).strip().upper()
                            if state in ("ON", "TRUE", "1", "ACTIVO"):
                                value = 1.0
                            elif state in ("OFF", "FALSE", "0", "INACTIVO"):
                                value = 0.0
                            else:
                                continue
                        else:
                            try:
                                value = float(raw)
                            except (TypeError, ValueError, OverflowError):
                                continue
                            if not math.isfinite(value):
                                continue
                        data[signal].append((timestamp, value))
        except (OSError, csv.Error, UnicodeError):
            self.subtitle_label.setText(strings.tr(
                STATISTICS_LOAD_ERROR.format(filename=path.name)
            ))
            return False

        all_times = [timestamp for readings in data.values() for timestamp, _ in readings]
        start = min(all_times) if all_times else None
        count = 0
        for signal, plot in self.signal_plots.items():
            readings = sorted(data[signal], key=lambda item: item[0])
            count += len(readings)
            plot.set_points([
                (max(0.0, (timestamp - start).total_seconds()), value)
                for timestamp, value in readings
            ] if start else [])

        self.data_path = path
        subtitle = (
            f"{path.name} · {count} lecturas guardadas"
            if count else f"{path.name} · sin lecturas guardadas"
        )
        self.subtitle_label.setText(strings.tr(subtitle))
        return True
