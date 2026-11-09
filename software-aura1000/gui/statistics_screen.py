import csv
import math
import re
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QTextBlockFormat, QTextCharFormat,
    QTextCursor,
)
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
from config_gui.theme import THEMES


_LOG_TIMESTAMP_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?) \| "
)
THROTTLE_FULL_TRAVEL_STEPS = 1400.0


class ProcessPlot(QWidget):
    """Gráfico liviano pintado con Qt para no agregar dependencias externas."""

    def __init__(self, title, unit, color, parent=None, fixed_range=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.color = QColor(color)
        self.points = []
        self.fixed_range = fixed_range
        self.setMinimumHeight(190)

    def set_points(self, points):
        self.points = points
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        metrics = painter.fontMetrics()
        values = [value for _, value in self.points]
        if self.fixed_range is not None:
            low, high = self.fixed_range
        elif values:
            low, high = min(values), max(values)
            if low == high:
                margin = max(abs(low) * 0.05, 1.0)
                low, high = low - margin, high + margin
        else:
            low = high = None
        if low is None:
            tick_width = metrics.horizontalAdvance("0")
        else:
            tick_width = max(
                metrics.horizontalAdvance(f"{low + fraction * (high - low):.3g}")
                for fraction in (0, .25, .5, .75, 1)
            )

        left = tick_width + 18
        top = metrics.height() + 18
        right = self.width() - 16
        bottom = self.height() - metrics.height() - 12

        painter.setPen(self.palette().text().color())
        painter.drawText(left, metrics.ascent() + 4, f"{strings.tr(self.title)} [{self.unit}]")
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


class CombinedProcessPlot(QWidget):
    """Grafica dos señales sobre el mismo eje temporal, con escalas opcionales."""

    def __init__(self, title, series, dual_axis=False, parent=None):
        super().__init__(parent)
        self.title = title
        self.series = {
            name: {"label": label, "unit": unit, "color": QColor(color), "points": []}
            for name, label, unit, color in series
        }
        self.dual_axis = dual_axis
        self.setMinimumHeight(210)

    def set_points(self, signal, points):
        self.series[signal]["points"] = points
        self.update()

    def points_for(self, signal):
        return self.series[signal]["points"]

    @staticmethod
    def _bounds(values):
        if not values:
            return 0.0, 1.0
        low, high = min(values), max(values)
        if low == high:
            margin = max(abs(low) * 0.05, 1.0)
            return low - margin, high + margin
        return low, high

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        metrics = painter.fontMetrics()
        title = strings.tr(self.title)
        painter.setPen(self.palette().text().color())
        painter.drawText(12, metrics.ascent() + 4, title)

        populated = [
            (name, item) for name, item in self.series.items() if item["points"]
        ]
        if not populated:
            painter.setPen(self.palette().mid().color())
            painter.drawText(12, self.height() // 2, strings.tr(STATISTICS_PLACEHOLDER))
            return

        left_values = [value for _, item in populated for _, value in item["points"]]
        left_low, left_high = self._bounds(left_values)
        if self.dual_axis and len(self.series) > 1:
            first_name = next(iter(self.series))
            left_values = [value for _, value in self.series[first_name]["points"]]
            left_low, left_high = self._bounds(left_values)
            second_name = list(self.series)[1]
            right_values = [value for _, value in self.series[second_name]["points"]]
            right_low, right_high = self._bounds(right_values)
        else:
            right_low = right_high = None

        all_times = [seconds for _, item in populated for seconds, _ in item["points"]]
        t_end = max(max(all_times), 1.0)
        left_width = max(metrics.horizontalAdvance(f"{left_low + f * (left_high-left_low):.3g}") for f in (0, .25, .5, .75, 1))
        right_width = 0
        if right_low is not None:
            right_width = max(metrics.horizontalAdvance(f"{right_low + f * (right_high-right_low):.3g}") for f in (0, .25, .5, .75, 1))
        left = left_width + 22
        right = self.width() - right_width - 22
        top = metrics.height() + 28
        bottom = self.height() - metrics.height() - 18
        if self.dual_axis:
            bottom -= metrics.height() + 2
        if right <= left or bottom <= top:
            return

        painter.setPen(QPen(self.palette().mid().color(), 1))
        for fraction in (0, .25, .5, .75, 1):
            y = bottom - fraction * (bottom - top)
            painter.drawLine(left, int(y), right, int(y))
            left_label = f"{left_low + fraction * (left_high-left_low):.3g}"
            painter.drawText(left - metrics.horizontalAdvance(left_label) - 6, int(y + metrics.ascent()/2), left_label)
            if right_low is not None:
                right_label = f"{right_low + fraction * (right_high-right_low):.3g}"
                painter.drawText(right + 6, int(y + metrics.ascent()/2), right_label)

        names = list(self.series)
        legend_x = 12
        for index, (name, item) in enumerate(self.series.items()):
            legend = f"{strings.tr(item['label'])} [{item['unit']}]"
            color = item["color"]
            painter.setPen(QPen(color, 3))
            painter.drawLine(legend_x, metrics.height() + 16, legend_x + 14, metrics.height() + 16)
            painter.setPen(self.palette().text().color())
            painter.drawText(legend_x + 19, metrics.height() + 20, legend)
            legend_x += metrics.horizontalAdvance(legend) + 40

        painter.setPen(self.palette().text().color())
        painter.drawText(left, self.height() - metrics.descent() - 2, "0 s")
        end_label = f"{t_end:.0f} s"
        painter.drawText(right - metrics.horizontalAdvance(end_label), self.height() - metrics.descent() - 2, end_label)
        if self.dual_axis:
            left_unit = f"[{self.series[names[0]]['unit']}]"
            unit_y = bottom + metrics.height() + 6
            painter.drawText(
                int((left - metrics.horizontalAdvance(left_unit)) / 2), unit_y, left_unit
            )
            if right_low is not None:
                right_unit = f"[{self.series[names[1]]['unit']}]"
                painter.drawText(
                    int(right + (self.width() - right - metrics.horizontalAdvance(right_unit)) / 2),
                    unit_y,
                    right_unit,
                )

        for index, (name, item) in enumerate(self.series.items()):
            points = item["points"]
            if not points:
                continue
            low, high = (left_low, left_high)
            if self.dual_axis and index == 1 and right_low is not None:
                low, high = right_low, right_high
            path = QPainterPath()
            for point_index, (seconds, value) in enumerate(points):
                x = left + seconds / t_end * (right - left)
                y = bottom - (value - low) / (high - low) * (bottom - top)
                point = QPointF(x, y)
                path.moveTo(point) if point_index == 0 else path.lineTo(point)
            painter.setPen(QPen(item["color"], 2))
            painter.drawPath(path)


class StatisticsScreen(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, data_path=None):
        super().__init__()
        self._explicit_data_path = Path(data_path) if data_path is not None else None
        self.data_path = self._explicit_data_path or RECIPE_DATA_PATH
        self._theme = "dark"
        self._log_content = None
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
        self.pressure_temperature_plot = CombinedProcessPlot(
            "Presión y temperatura",
            (("BARATRON", "Presión", "Torr", "#38BDF8"), ("CHAMBER_TEMP", "Temperatura", "°C", "#FACC15")),
            dual_axis=True,
        )
        self.mfc_plot = CombinedProcessPlot(
            "Caudales MFC",
            (("MFC1_FLOW", "MFC1 · O₂", "SLPM", "#34D399"),
             ("MFC2_FLOW", "MFC2 · N₂", "SLPM", "#A78BFA")),
        )
        self.throttle_plot = ProcessPlot(
            "Apertura throttle", "%", "#FB7185", fixed_range=(0.0, 100.0)
        )
        self.plasma_plot = ProcessPlot("Estado plasma", "0 apagado / 1 encendido", "#F97316")
        self.signal_plots = {
            "BARATRON": self.pressure_temperature_plot,
            "CHAMBER_TEMP": self.pressure_temperature_plot,
            "MFC1_FLOW": self.mfc_plot, "MFC2_FLOW": self.mfc_plot,
            "THROTTLE_POSITION": self.throttle_plot, "PLASMA": self.plasma_plot,
        }
        self.data_plots = [self.pressure_temperature_plot, self.mfc_plot,
                           self.throttle_plot, self.plasma_plot]
        self.load_file_button = QPushButton(STATISTICS_LOAD_FILE_TEXT)
        self.load_file_button.setObjectName("StatisticsLoadFileButton")
        # Backwards-compatible attribute for callers that refresh CSV data.
        self.refresh_button = self.load_file_button
        self.log_path = None
        self.logs_title_label = QLabel(STATISTICS_NO_LOGS)
        self.logs_title_label.setObjectName("SubtitleLabel")
        self.logs_title_label.setAlignment(Qt.AlignCenter)
        title_font = self.logs_title_label.font()
        title_font.setBold(True)
        self.logs_title_label.setFont(title_font)
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
        for plot in self.data_plots:
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

    def set_theme(self, theme):
        if theme not in THEMES:
            raise ValueError("El tema debe ser 'light' o 'dark'.")
        self._theme = theme
        if self._log_content is not None:
            self._render_log_content(self._log_content)

    def _render_log_content(self, content):
        palette = THEMES[self._theme]
        background = QColor(palette["background"])
        surface = QColor(palette["surface"])
        primary = QColor(palette["primary"])
        self.logs_view.setPlainText(content)

        document = self.logs_view.document()
        block = document.begin()
        line_index = 0
        while block.isValid():
            block_format = QTextBlockFormat(block.blockFormat())
            block_format.setBackground(background if line_index % 2 == 0 else surface)
            cursor = QTextCursor(block)
            cursor.setBlockFormat(block_format)

            match = _LOG_TIMESTAMP_PATTERN.match(block.text())
            if match:
                timestamp_format = QTextCharFormat()
                timestamp_format.setForeground(primary)
                timestamp_format.setFontWeight(QFont.Bold)
                cursor.setPosition(block.position())
                cursor.setPosition(
                    block.position() + len(match.group(1)),
                    QTextCursor.KeepAnchor,
                )
                cursor.mergeCharFormat(timestamp_format)

            line_index += 1
            block = block.next()

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
            self._clear_data_plots()
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
        self._log_content = content
        self.logs_title_label.setText(path.name)
        self._render_log_content(content)
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
        data = {signal: [] for signal in self.signal_plots}
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as data_file:
                for row in csv.DictReader(data_file):
                    signal = row.get("señal") or row.get("seÃ±al") or row.get("signal")
                    try:
                        timestamp = datetime.fromisoformat(row["timestamp"])
                        value = float(row["valor"] if "valor" in row else row["value"])
                        if not math.isfinite(value):
                            continue
                    except (KeyError, TypeError, ValueError, OverflowError):
                        continue
                    if signal not in data:
                        continue
                    data[signal].append((timestamp, value))
        except (OSError, csv.Error, UnicodeError):
            self.subtitle_label.setText(strings.tr(
                STATISTICS_LOAD_ERROR.format(filename=path.name)
            ))
            return False

        all_times = [timestamp for readings in data.values() for timestamp, _ in readings]
        start = min(all_times) if all_times else None
        for signal in self.signal_plots:
            readings = sorted(data.get(signal, []), key=lambda item: item[0])
            points = [
                (max(0.0, (timestamp - start).total_seconds()), value)
                for timestamp, value in readings
            ] if start else []
            self._set_signal_points(signal, points)

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
        for signal in self.signal_plots:
            readings = sorted(data[signal], key=lambda item: item[0])
            count += len(readings)
            points = [
                (max(0.0, (timestamp - start).total_seconds()), value)
                for timestamp, value in readings
            ] if start else []
            self._set_signal_points(signal, points)

        self.data_path = path
        subtitle = (
            f"{path.name} · {count} lecturas guardadas"
            if count else f"{path.name} · sin lecturas guardadas"
        )
        self.subtitle_label.setText(strings.tr(subtitle))
        return True

    def _set_signal_points(self, signal, points):
        if signal == "THROTTLE_POSITION":
            points = [
                (
                    seconds,
                    max(
                        0.0,
                        min(
                            100.0,
                            100.0 * (1.0 - steps / THROTTLE_FULL_TRAVEL_STEPS),
                        ),
                    ),
                )
                for seconds, steps in points
            ]
        plot = self.signal_plots[signal]
        if isinstance(plot, CombinedProcessPlot):
            plot.set_points(signal, points)
        else:
            plot.set_points(points)

    def _clear_data_plots(self):
        for plot in self.data_plots:
            if isinstance(plot, CombinedProcessPlot):
                for signal in plot.series:
                    plot.set_points(signal, [])
            else:
                plot.set_points([])
