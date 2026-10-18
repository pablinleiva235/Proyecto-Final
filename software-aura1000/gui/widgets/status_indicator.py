"""Indicador circular vectorial para estados de equipos y señales."""

from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QPalette
from PyQt5.QtWidgets import QStyle, QStyleOption, QWidget


class StatusIndicatorWidget(QWidget):
    """Dibuja un pictograma de estado sin acceder a la lógica del equipo."""

    STATES = {"on", "running", "warning", "fault", "off"}
    ICON_SIZE = 42

    def __init__(self, state="off", label="", parent=None, size=42):
        super().__init__(parent)
        self.setObjectName("StatusIndicator")
        self._size = int(size)
        self.setFixedSize(self._size, self._size)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.set_state(state, label)

    def set_state(self, state, label=None):
        normalized = str(state).lower()
        if normalized not in self.STATES:
            raise ValueError(f"Estado visual desconocido: {state}")
        self._state = normalized
        self.setProperty("state", normalized)
        if label is not None:
            self.setAccessibleName(str(label))
            self.setToolTip(str(label))
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def paintEvent(self, event):
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.style().drawPrimitive(QStyle.PE_Widget, option, painter, self)
        painter.scale(self._size / self.ICON_SIZE, self._size / self.ICON_SIZE)

        foreground = self.palette().color(QPalette.WindowText)
        pen = QPen(foreground, 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        bounds = QRectF(11, 11, 20, 20)
        center_x = self.ICON_SIZE / 2
        center_y = self.ICON_SIZE / 2

        if self._state == "on":
            # Deja la abertura arriba, donde se une el vástago del símbolo.
            painter.drawArc(bounds, 135 * 16, 270 * 16)
            painter.drawLine(QPointF(center_x, 7), QPointF(center_x, center_y))
        elif self._state == "off":
            painter.drawEllipse(bounds)
            painter.drawLine(QPointF(12, 12), QPointF(30, 30))
        elif self._state == "running":
            path = QPainterPath(QPointF(6, center_y))
            path.lineTo(12, center_y)
            path.lineTo(16, 13)
            path.lineTo(21, 30)
            path.lineTo(26, 17)
            path.lineTo(30, center_y)
            path.lineTo(36, center_y)
            painter.drawPath(path)
        elif self._state == "warning":
            triangle = QPainterPath(QPointF(center_x, 7))
            triangle.lineTo(36, 34)
            triangle.lineTo(6, 34)
            triangle.closeSubpath()
            painter.drawPath(triangle)
            painter.drawLine(QPointF(center_x, 15), QPointF(center_x, 24))
            painter.drawPoint(QPointF(center_x, 29))
        else:  # fault
            painter.drawEllipse(bounds)
            painter.drawLine(QPointF(16, 16), QPointF(26, 26))
            painter.drawLine(QPointF(26, 16), QPointF(16, 26))

        painter.end()
