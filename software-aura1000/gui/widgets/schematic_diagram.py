"""Composable, theme-aware equipment schematic for normal operation."""

from pathlib import Path

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QLabel


class SchematicDiagramWidget(QLabel):
    """Draw the pipework and each equipment SVG independently on one canvas."""

    CANVAS_WIDTH = 1047
    CANVAS_HEIGHT = 579

    # Rectangles use the coordinate system of the original 1047 x 579 diagram.
    COMPONENTS = {
        "pump": ("Bomba", "bom", QRectF(0, 506, 132, 69), "alert", "open", "idle"),
        "left_valve_1": ("Valves", "val", QRectF(175, 60, 124, 105), "close", "half", "open"),
        "left_valve_2": ("Valves", "val", QRectF(175, 184, 124, 105), "close", "half", "open"),
        "left_valve_3": ("Valves", "val", QRectF(175, 308, 124, 105), "close", "half", "open"),
        "vent_valve": ("Valves", "val", QRectF(423, 0, 124, 105), "close", "half", "open"),
        "right_valve_1": ("Valves", "val", QRectF(707, 60, 124, 105), "close", "half", "open"),
        "right_valve_2": ("Valves", "val", QRectF(707, 184, 124, 105), "close", "half", "open"),
        "right_valve_3": ("Valves", "val", QRectF(707, 308, 124, 105), "close", "half", "open"),
        "mfc_o2": ("MFCs", "mfc", QRectF(862, 81, 162, 77), "alert", "open", "idle"),
        "mfc_n2": ("MFCs", "mfc", QRectF(862, 205, 162, 77), "alert", "open", "idle"),
        "mfc_aux": ("MFCs", "mfc", QRectF(862, 329, 162, 77), "alert", "open", "idle"),
        "chamber": ("Chamber", "cam", QRectF(411, 319, 164, 133), "heating", "open", "plasma", "idle"),
        "arm": ("Brazo y carrete", "br", QRectF(369, 456, 250, 116), "idle"),
        "magnetron": ("Magnetron", "mag", QRectF(577, 371, 67, 36), "idle"),
    }

    LABELS = (
        ("N₂", 277, 89),
        ("Soft", 277, 213),
        ("Main", 277, 337),
        ("Vent", 527, 21),
        ("MFC O₂", 910, 185),
        ("MFC N₂", 910, 309),
        ("MFC", 910, 433),
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OperationDiagramImage")
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumSize(1, 1)
        self._assets_dir = Path(__file__).resolve().parents[2] / "assets"
        self._theme = "dark"
        self._states = {name: "idle" for name in self.COMPONENTS}
        for name, component in self.COMPONENTS.items():
            if component[1] == "val":
                self._states[name] = "close"
        self._renderers = {}
        self._pipes = None
        self._assets_available = False
        self._fallback_text = self.tr("No se pudo cargar el esquema del equipo.")
        self._load_all_assets()

    @property
    def theme(self):
        return self._theme

    def set_theme(self, theme):
        if theme not in ("light", "dark"):
            raise ValueError("El tema debe ser 'light' o 'dark'.")
        if theme == self._theme:
            return
        self._theme = theme
        self._load_all_assets()
        self.update()

    def set_component_state(self, component, state):
        """Set a component variant; component names are keys in COMPONENTS."""
        if component not in self.COMPONENTS:
            raise KeyError(f"Componente de esquema desconocido: {component}")
        variants = self.COMPONENTS[component][3:]
        if state not in variants:
            raise ValueError(
                f"Estado {state!r} no disponible para {component}; "
                f"opciones: {', '.join(variants)}"
            )
        self._states[component] = state
        self._load_component(component)
        self._update_asset_status()
        self.update()

    def set_component_states(self, states):
        """Update several components together, validating before changing any."""
        for component, state in states.items():
            if component not in self.COMPONENTS:
                raise KeyError(f"Componente de esquema desconocido: {component}")
            variants = self.COMPONENTS[component][3:]
            if state not in variants:
                raise ValueError(
                    f"Estado {state!r} no disponible para {component}; "
                    f"opciones: {', '.join(variants)}"
                )

        changed = []
        for component, state in states.items():
            if self._states[component] == state:
                continue
            self._states[component] = state
            self._load_component(component)
            changed.append(component)
        if changed:
            self._update_asset_status()
            self.update()

    def set_pump_state(self, state):
        self.set_component_state("pump", state)

    def set_valve_state(self, valve, state):
        self.set_component_state(valve, state)

    def set_mfc_state(self, mfc, state):
        self.set_component_state(mfc, state)

    def set_chamber_state(self, state):
        self.set_component_state("chamber", state)

    def set_fallback_text(self, message):
        self._fallback_text = str(message)
        if not self._assets_available:
            self.setText(self._fallback_text)
        self.update()

    @property
    def assets_available(self):
        return self._assets_available

    def _load_all_assets(self):
        pipe_name = "tubos_dark.svg" if self._theme == "dark" else "tubos_ligth.svg"
        pipe = QSvgRenderer(str(self._assets_dir / pipe_name))
        self._pipes = pipe if pipe.isValid() else None
        self._renderers.clear()
        for name in self.COMPONENTS:
            self._load_component(name)
        self._update_asset_status()

    def _update_asset_status(self):
        self._assets_available = self._pipes is not None and all(
            renderer is not None for renderer in self._renderers.values()
        )
        self.setObjectName(
            "OperationDiagramImage" if self._assets_available else "OperationDiagramFallback"
        )
        self.setText("" if self._assets_available else self._fallback_text)
        self.style().unpolish(self)
        self.style().polish(self)

    def _load_component(self, name):
        folder, prefix, _rect, *_variants = self.COMPONENTS[name]
        state = self._states[name]
        filename = f"{prefix}_{state}_{self._theme}.svg"
        if name == "pump" and state == "alert" and self._theme == "dark":
            # Preserve the legacy asset filename, which contains a stray ']'.
            filename = "bom_alert]_dark.svg"
        renderer = QSvgRenderer(str(self._assets_dir / folder / filename))
        self._renderers[name] = renderer if renderer.isValid() else None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        scale = min(
            self.width() / self.CANVAS_WIDTH,
            self.height() / self.CANVAS_HEIGHT,
        )
        x_offset = (self.width() - self.CANVAS_WIDTH * scale) / 2
        y_offset = (self.height() - self.CANVAS_HEIGHT * scale) / 2
        painter.translate(x_offset, y_offset)
        painter.scale(scale, scale)
        if not self._assets_available:
            painter.end()
            super().paintEvent(event)
            return
        if self._pipes is not None:
            self._pipes.render(painter, QRectF(0, 0, self.CANVAS_WIDTH, 563))
        for name, (_folder, _prefix, rect, *_variants) in self.COMPONENTS.items():
            renderer = self._renderers.get(name)
            if renderer is not None:
                if name in self.VALVE_NAMES:
                    self._render_valve(painter, renderer, name, rect)
                else:
                    renderer.render(
                        painter,
                        self._component_render_rect(name, rect, self._states[name]),
                    )
        self._draw_labels(painter)
        painter.end()

    VALVE_NAMES = {
        "left_valve_1", "left_valve_2", "left_valve_3",
        "right_valve_1", "right_valve_2", "right_valve_3",
        "vent_valve",
    }

    @staticmethod
    def _component_render_rect(name, rect, state):
        if name == "chamber" and state == "open":
            return QRectF(rect.x(), rect.y(), rect.width(), 183)
        return rect

    @staticmethod
    def _render_valve(painter, renderer, name, rect):
        painter.save()
        if name in {"right_valve_1", "right_valve_2", "right_valve_3"}:
            painter.translate(rect.center())
            painter.scale(-1, 1)
            painter.translate(-rect.center())
        elif name == "vent_valve":
            painter.translate(rect.center())
            painter.rotate(-90)
            painter.translate(-rect.center())
        renderer.render(painter, rect)
        painter.restore()

    def _draw_labels(self, painter):
        painter.setPen(QColor("#D8E5F0" if self._theme == "dark" else "#121358"))
        painter.setFont(QFont("Arial", 20, QFont.Bold))
        for label, x, y in self.LABELS:
            painter.drawText(x, y, label)
