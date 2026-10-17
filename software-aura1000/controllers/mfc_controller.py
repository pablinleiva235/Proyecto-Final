"""Control validado de las consignas y válvulas de MFC1/MFC2."""

import math
from PyQt5.QtCore import QObject, pyqtSignal
from config.analog_signals import ANALOG_OUTPUTS


class MFCController(QObject):
    flow_applied = pyqtSignal(str, float)
    valve_state_changed = pyqtSignal(str, bool)
    operation_error = pyqtSignal(str, str)

    _CONFIG = {
        "MFC1": (10.0, "MFC1_SETPOINT", "MFC1_OPEN"),
        "MFC2": (1.0, "MFC2_SETPOINT", "MFC2_OPEN"),
    }

    def __init__(self, hardware, can_operate=None, parent=None):
        super().__init__(parent)
        self._hardware = hardware
        self._can_operate = can_operate or (lambda: True)
        self._valves = {"MFC1": False, "MFC2": False}

    def set_flow(self, mfc_name, flow_slpm):
        try:
            maximum, output_name, _ = self._config(mfc_name)
            flow = float(flow_slpm)
            if not math.isfinite(flow) or not 0.0 <= flow <= maximum:
                raise ValueError(f"El flujo debe estar entre 0 y {maximum:g} SLPM.")
            if not self._can_operate():
                raise RuntimeError("El vacío principal debe estar activo para controlar los MFC.")
            output = ANALOG_OUTPUTS[output_name]
            voltage = flow / maximum * output["max_voltage"]
            self._hardware.analog_write(output_name, voltage)
            self.flow_applied.emit(mfc_name, flow)
        except Exception as error:
            self.operation_error.emit(mfc_name, str(error))

    def set_valve(self, mfc_name, opened):
        try:
            _, output_name, valve_name = self._config(mfc_name)
            if opened and not self._can_operate():
                raise RuntimeError("El vacío principal debe estar activo para controlar los MFC.")
            if opened:
                self._hardware.digital_set(valve_name, True)
            else:
                errors = []
                try:
                    self._hardware.analog_write(output_name, 0.0)
                except Exception as error:
                    errors.append(f"setpoint a cero: {error}")
                try:
                    self._hardware.digital_set(valve_name, False)
                    self._valves[mfc_name] = False
                except Exception as error:
                    errors.append(f"cierre de válvula: {error}")
                if errors:
                    raise RuntimeError("; ".join(errors))
            self._valves[mfc_name] = bool(opened)
            self.valve_state_changed.emit(mfc_name, bool(opened))
        except Exception as error:
            if mfc_name in self._valves:
                self.valve_state_changed.emit(mfc_name, self._valves[mfc_name])
            self.operation_error.emit(mfc_name, str(error))

    def shutdown(self):
        for name in self._CONFIG:
            self.set_valve(name, False)

    @classmethod
    def _config(cls, name):
        try:
            return cls._CONFIG[name]
        except KeyError as error:
            raise ValueError(f"MFC no soportado: {name}") from error
