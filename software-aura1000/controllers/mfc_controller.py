"""Control calibrado de MFC1/MFC2, interlocks y supervisión de caudal."""

from collections import deque
import math
import time

from PyQt5.QtCore import QObject, pyqtSignal

from config.analog_signals import ANALOG_OUTPUTS


class MFCController(QObject):
    flow_applied = pyqtSignal(str, float)
    flow_measured = pyqtSignal(str, float)
    flow_fault = pyqtSignal(str)
    plasma_disable_requested = pyqtSignal()
    valve_state_changed = pyqtSignal(str, bool)
    operation_error = pyqtSignal(str, str)

    _CONFIG = {
        "MFC1": {"max_flow": 6.5, "min_flow": 0.0, "rated_flow": 10.0,
                 "offset": 0.16, "factor": 0.981, "tolerance": 0.15,
                 "output": "MFC1_SETPOINT", "valve": "MFC1_OPEN", "input": "MFC1_FLOW"},
        "MFC2": {"max_flow": 0.65, "min_flow": 0.1, "rated_flow": 1.0,
                 "offset": 0.0, "factor": 1.0, "tolerance": 0.25,
                 "output": "MFC2_SETPOINT", "valve": "MFC2_OPEN", "input": "MFC2_FLOW"},
    }
    MONITOR_WINDOW_S = 3.0

    def __init__(self, hardware, can_operate=None, parent=None):
        super().__init__(parent)
        self._hardware = hardware
        self._can_operate = can_operate or (lambda: True)
        self._valves = {name: False for name in self._CONFIG}
        self._targets = {name: 0.0 for name in self._CONFIG}
        self._samples = {name: deque() for name in self._CONFIG}
        self._fault_latched = False

    @classmethod
    def flow_to_voltage(cls, mfc_name, flow_slpm):
        config = cls._config(mfc_name)
        flow = float(flow_slpm)
        if not math.isfinite(flow) or not config["min_flow"] <= flow <= config["max_flow"]:
            raise ValueError(f"El flujo de {mfc_name} debe estar entre {config['min_flow']:g} y {config['max_flow']:g} SLPM.")
        corrected = max(0.0, flow - config["offset"]) / config["factor"]
        voltage = corrected / config["rated_flow"] * 5.0
        return min(5.0, max(0.0, voltage))

    @classmethod
    def voltage_to_flow(cls, mfc_name, voltage):
        config = cls._config(mfc_name)
        value = float(voltage)
        if not math.isfinite(value):
            raise ValueError("La lectura analógica no es finita.")
        return max(0.0, value / 5.0 * config["rated_flow"]) * config["factor"]

    def set_flow(self, mfc_name, flow_slpm):
        try:
            config = self._config(mfc_name)
            flow = float(flow_slpm)
            voltage = self.flow_to_voltage(mfc_name, flow)
            if not self._can_operate():
                self._clear_samples()
                raise RuntimeError("El vacío principal debe estar activo para controlar los MFC.")
            self._write_analog(config["output"], voltage)
            self._targets[mfc_name] = flow
            self._clear_samples(mfc_name)
            self._fault_latched = False
            if mfc_name == "MFC1" and flow <= 0:
                self.plasma_disable_requested.emit()
            self.flow_applied.emit(mfc_name, flow)
        except Exception as error:
            self.operation_error.emit(mfc_name, str(error))

    def set_valve(self, mfc_name, opened):
        try:
            config = self._config(mfc_name)
            opened = bool(opened)
            if opened and not self._can_operate():
                self._clear_samples()
                raise RuntimeError("El vacío principal debe estar activo para controlar los MFC.")
            if opened:
                self._write_digital(config["valve"], True)
            else:
                self._clear_samples(mfc_name)
                errors = []
                try:
                    self._write_analog(config["output"], 0.0)
                except Exception as error:
                    errors.append(f"setpoint a cero: {error}")
                try:
                    self._write_digital(config["valve"], False)
                    self._valves[mfc_name] = False
                    self._targets[mfc_name] = 0.0
                except Exception as error:
                    errors.append(f"cierre de válvula: {error}")
                if mfc_name == "MFC1":
                    self.plasma_disable_requested.emit()
                if errors:
                    raise RuntimeError("; ".join(errors))
            self._valves[mfc_name] = opened
            self.valve_state_changed.emit(mfc_name, opened)
        except Exception as error:
            if mfc_name in self._valves:
                self.valve_state_changed.emit(mfc_name, self._valves[mfc_name])
            self.operation_error.emit(mfc_name, str(error))

    def can_enable_plasma(self):
        return self._valves["MFC1"] and self._targets["MFC1"] > 0

    def update_flow_measurement(self, mfc_name, voltage):
        try:
            flow = self.voltage_to_flow(mfc_name, voltage)
        except Exception as error:
            self.operation_error.emit(mfc_name, f"Lectura de caudal inválida: {error}")
            return
        self.flow_measured.emit(mfc_name, flow)
        if not self._can_operate():
            self._clear_samples()
            return
        now = time.monotonic()
        samples = self._samples[mfc_name]
        samples.append((now, flow))
        while samples and now - samples[0][0] > self.MONITOR_WINDOW_S:
            samples.popleft()
        target = self._targets[mfc_name]
        if (not self._fault_latched and self._valves[mfc_name] and target > 0
                and samples and now - samples[0][0] >= self.MONITOR_WINDOW_S):
            average = sum(value for _, value in samples) / len(samples)
            if abs(average - target) / target > self._CONFIG[mfc_name]["tolerance"]:
                self._fault_latched = True
                self._clear_samples()
                self.flow_fault.emit(f"{mfc_name}: consigna {target:g} SLPM, promedio medido {average:.3f} SLPM.")

    def shutdown(self):
        for name in self._CONFIG:
            self.set_valve(name, False)

    def _clear_samples(self, mfc_name=None):
        names = (mfc_name,) if mfc_name else tuple(self._samples)
        for name in names:
            self._samples[name].clear()

    def _require_driver_enabled(self):
        if self._hardware.digital_read("DRIVER_ENABLE") is not True:
            raise RuntimeError("DRIVER_ENABLE debe estar activo para modificar las salidas de MFC.")

    def _write_digital(self, signal_name, active):
        self._require_driver_enabled()
        self._hardware.digital_set(signal_name, active)

    def _write_analog(self, signal_name, value):
        self._require_driver_enabled()
        self._hardware.analog_write(signal_name, value)

    @classmethod
    def _config(cls, name):
        try:
            return cls._CONFIG[name]
        except KeyError as error:
            raise ValueError(f"MFC no soportado: {name}") from error
