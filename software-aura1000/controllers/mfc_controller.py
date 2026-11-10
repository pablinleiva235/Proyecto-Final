"""Control calibrado de MFC1/MFC2, interlocks y supervisión de caudal."""

from collections import deque
from datetime import datetime
import math
import time

from PyQt5.QtCore import QObject, QSettings, QTimer, pyqtSignal

from config.analog_signals import ANALOG_OUTPUTS


class MFCController(QObject):
    flow_applied = pyqtSignal(str, float)
    flow_measured = pyqtSignal(str, float)
    flow_fault = pyqtSignal(str)
    plasma_disable_requested = pyqtSignal()
    valve_state_changed = pyqtSignal(str, bool)
    operation_error = pyqtSignal(str, str)
    calibration_finished = pyqtSignal(str, bool, float, str, bool)
    calibration_state_changed = pyqtSignal(str, bool)
    calibration_progress = pyqtSignal(str, str, int, int, float, object)

    _CONFIG = {
        "MFC1": {"max_flow": 6.5, "min_flow": 0.0, "rated_flow": 10.0,
                 "offset": 0.0, "factor": 0.981, "tolerance": 0.25,
                 "output": "MFC1_SETPOINT", "valve": "MFC1_OPEN", "input": "MFC1_FLOW"},
        "MFC2": {"max_flow": 0.65, "min_flow": 0.1, "rated_flow": 1.0,
                 "offset": 0.0, "factor": 1.0, "tolerance": 0.25,
                 "output": "MFC2_SETPOINT", "valve": "MFC2_OPEN", "input": "MFC2_FLOW"},
    }
    CALIBRATION_FLOWS = {
        "MFC1": (1.0, 2.0, 3.0, 4.0, 5.0, 6.0),
        "MFC2": (0.1, 0.2, 0.3, 0.4, 0.5, 0.6),
    }
    MONITOR_WINDOW_S = 3.0

    CALIBRATION_WINDOW_MS = 3000

    def __init__(self, hardware, can_operate=None, parent=None):
        super().__init__(parent)
        self._hardware = hardware
        self._can_operate = can_operate or (lambda: True)
        self._valves = {name: False for name in self._CONFIG}
        self._targets = {name: 0.0 for name in self._CONFIG}
        self._samples = {name: deque() for name in self._CONFIG}
        self._fault_latched = False
        self._settings = QSettings("UTN", "Plasma Asher AURA 1000")
        self._output_offsets = {}
        self._calibration_dates = {}
        self._calibrations = {}
        self._calibration_timers = {}
        for name, config in self._CONFIG.items():
            try:
                offsets = {}
                for flow in self.CALIBRATION_FLOWS[name]:
                    stored = self._settings.value(self._offset_setting_key(name, flow), 0.0, type=float)
                    offsets[flow] = stored if math.isfinite(stored) else 0.0
                self._output_offsets[name] = offsets
            except (TypeError, ValueError):
                self._output_offsets[name] = dict.fromkeys(self.CALIBRATION_FLOWS[name], 0.0)
            self._calibration_dates[name] = self._settings.value(
                f"mfc/last_calibration/{name}", "", type=str
            )

    @classmethod
    def flow_to_voltage(cls, mfc_name, flow_slpm, offset=None):
        config = cls._config(mfc_name)
        flow = float(flow_slpm)
        if not math.isfinite(flow) or not config["min_flow"] <= flow <= config["max_flow"]:
            raise ValueError(f"El flujo de {mfc_name} debe estar entre {config['min_flow']:g} y {config['max_flow']:g} SLPM.")
        output_offset = config["offset"] if offset is None else float(offset)
        if not math.isfinite(output_offset):
            raise ValueError("El offset de salida debe ser un número finito.")
        corrected = max(0.0, flow - output_offset) / config["factor"]
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
            if mfc_name in self._calibrations:
                raise RuntimeError(f"No se puede modificar {mfc_name} durante su calibración.")
            flow = float(flow_slpm)
            voltage = self.flow_to_voltage(
                mfc_name, flow, offset=self.output_offset(mfc_name, flow)
            )
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
            if not opened and mfc_name in self._calibrations:
                self._finish_calibration(
                    mfc_name, "La válvula se cerró antes de completar la calibración."
                )
        except Exception as error:
            if mfc_name in self._valves:
                self.valve_state_changed.emit(mfc_name, self._valves[mfc_name])
            self.operation_error.emit(mfc_name, str(error))

    def can_enable_plasma(self):
        return self._valves["MFC1"] and self._targets["MFC1"] > 0

    def target_flow(self, mfc_name):
        self._config(mfc_name)
        return self._targets[mfc_name]

    def update_flow_measurement(self, mfc_name, voltage):
        try:
            flow = self.voltage_to_flow(mfc_name, voltage)
        except Exception as error:
            self.operation_error.emit(mfc_name, f"Lectura de caudal inválida: {error}")
            return
        self.flow_measured.emit(mfc_name, flow)
        calibration = self._calibrations.get(mfc_name)
        if calibration is not None:
            calibration["samples"].append(flow)
            return
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

    def calibrate_output_offset(self, mfc_name, *_unused):
        """Calibrate six output points, sampling each for three seconds."""
        opened_for_calibration = False
        try:
            config = self._config(mfc_name)
            if mfc_name in self._calibrations:
                raise RuntimeError(f"Ya hay una calibracion en curso para {mfc_name}.")
            if not self._can_operate():
                raise RuntimeError("El vacio principal debe estar activo para calibrar los MFC.")

            was_open = self._valves[mfc_name]
            previous_target = self._targets[mfc_name]
            if not was_open:
                self._write_digital(config["valve"], True)
                self._valves[mfc_name] = True
                opened_for_calibration = True
                self.valve_state_changed.emit(mfc_name, True)

            self._calibrations[mfc_name] = {
                "flows": self.CALIBRATION_FLOWS[mfc_name],
                "index": 0,
                "offsets": dict.fromkeys(self.CALIBRATION_FLOWS[mfc_name], 0.0),
                "was_open": was_open,
                "previous_target": previous_target,
                "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "samples": [],
            }
            self._start_calibration_point(mfc_name)
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda name=mfc_name: self._complete_calibration_point(name))
            self._calibration_timers[mfc_name] = timer
            self.calibration_state_changed.emit(mfc_name, True)
            timer.start(self.CALIBRATION_WINDOW_MS)
        except Exception as error:
            self._calibrations.pop(mfc_name, None)
            timer = self._calibration_timers.pop(mfc_name, None)
            if timer is not None:
                timer.stop()
                timer.deleteLater()
            if opened_for_calibration:
                try:
                    self._write_analog(config["output"], 0.0)
                    self._write_digital(config["valve"], False)
                    self._valves[mfc_name] = False
                    self._targets[mfc_name] = 0.0
                    self.valve_state_changed.emit(mfc_name, False)
                except Exception:
                    pass
            self.calibration_finished.emit(
                mfc_name, False, self._mean_output_offset(mfc_name), str(error), False
            )

    def _start_calibration_point(self, mfc_name):
        calibration = self._calibrations[mfc_name]
        reference = calibration["flows"][calibration["index"]]
        config = self._config(mfc_name)
        self._write_analog(config["output"], self.flow_to_voltage(mfc_name, reference, offset=0.0))
        self._targets[mfc_name] = reference
        calibration["samples"] = []
        self._clear_samples(mfc_name)
        self._emit_calibration_progress(mfc_name, "measuring", reference)

    def _complete_calibration_point(self, mfc_name):
        calibration = self._calibrations.get(mfc_name)
        if calibration is None:
            return
        try:
            if not self._can_operate():
                raise RuntimeError("Se perdio un interlock durante la calibracion.")
            samples = calibration["samples"]
            if not samples:
                raise RuntimeError("No se recibieron lecturas validas durante los 3 segundos del punto de calibracion.")
            reference = calibration["flows"][calibration["index"]]
            calibration["offsets"][reference] = sum(samples) / len(samples) - reference
            calibration["index"] += 1
            self._emit_calibration_progress(mfc_name, "point_complete", reference)
            if calibration["index"] < len(calibration["flows"]):
                self._start_calibration_point(mfc_name)
                self._calibration_timers[mfc_name].start(self.CALIBRATION_WINDOW_MS)
            else:
                self._emit_calibration_progress(mfc_name, "saving", reference)
                self._finish_calibration(mfc_name)
        except Exception as error:
            self._finish_calibration(mfc_name, str(error))

    def _finish_calibration(self, mfc_name, abort_reason=None):
        calibration = self._calibrations.pop(mfc_name, None)
        timer = self._calibration_timers.pop(mfc_name, None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()
        if calibration is None:
            return

        success = False
        saved = False
        message = ""
        offset = self._mean_output_offset(mfc_name)
        try:
            if abort_reason:
                raise RuntimeError(abort_reason)
            if not self._can_operate():
                raise RuntimeError("Se perdio un interlock durante la calibracion.")
            if calibration["index"] != len(calibration["flows"]):
                raise RuntimeError("La calibracion no completo los seis puntos.")

            old_offsets = self._output_offsets[mfc_name]
            old_date = self._calibration_dates[mfc_name]
            for flow, point_offset in calibration["offsets"].items():
                self._settings.setValue(self._offset_setting_key(mfc_name, flow), point_offset)
            calibrated_at = datetime.now().astimezone().isoformat(timespec="seconds")
            self._settings.setValue(f"mfc/last_calibration/{mfc_name}", calibrated_at)
            self._settings.sync()
            if self._settings.status() != QSettings.NoError:
                for flow, point_offset in old_offsets.items():
                    self._settings.setValue(self._offset_setting_key(mfc_name, flow), point_offset)
                self._settings.setValue(f"mfc/last_calibration/{mfc_name}", old_date)
                self._settings.sync()
                raise RuntimeError("No se pudo guardar la tabla de offsets.")
            self._output_offsets[mfc_name] = dict(calibration["offsets"])
            self._calibration_dates[mfc_name] = calibrated_at
            offset = self._mean_output_offset(mfc_name)
            saved = success = True
        except Exception as error:
            message = str(error)
        finally:
            config = self._config(mfc_name)
            try:
                if calibration["was_open"] and self._valves[mfc_name] and self._can_operate():
                    previous_target = calibration["previous_target"]
                    if previous_target > 0:
                        voltage = self.flow_to_voltage(
                            mfc_name, previous_target,
                            offset=self.output_offset(mfc_name, previous_target),
                        )
                    else:
                        voltage = 0.0
                    self._write_analog(config["output"], voltage)
                    self._targets[mfc_name] = previous_target
                else:
                    self._write_analog(config["output"], 0.0)
                    if self._valves[mfc_name]:
                        self._write_digital(config["valve"], False)
                        self._valves[mfc_name] = False
                    self._targets[mfc_name] = 0.0
                    self.valve_state_changed.emit(mfc_name, False)
            except Exception as error:
                success = False
                message = f"{message}; " if message else ""
                message += f"No se pudo restaurar el estado del MFC: {error}"
        self._clear_samples(mfc_name)
        current_index = min(calibration["index"], len(calibration["flows"]) - 1)
        phase = "completed" if success else "failed"
        self._emit_calibration_progress(
            mfc_name, phase, calibration["flows"][current_index], calibration
        )
        self.calibration_state_changed.emit(mfc_name, False)
        self.calibration_finished.emit(mfc_name, success, offset, message, saved)

    def _emit_calibration_progress(self, mfc_name, phase, reference_flow, calibration=None):
        calibration = calibration or self._calibrations.get(mfc_name)
        if calibration is None:
            return
        self.calibration_progress.emit(
            mfc_name,
            phase,
            calibration["index"],
            len(calibration["flows"]),
            reference_flow,
            dict(calibration["offsets"]),
        )

    def output_offset(self, mfc_name, flow_slpm=None):
        self._config(mfc_name)
        offsets = self._output_offsets[mfc_name]
        if flow_slpm is None:
            return offsets[self.CALIBRATION_FLOWS[mfc_name][0]]
        target = float(flow_slpm)
        reference = min(offsets, key=lambda reference: (abs(reference - target), reference))
        return offsets[reference]

    def calibration_table(self, mfc_name):
        self._config(mfc_name)
        return dict(self._output_offsets[mfc_name])

    def calibration_date(self, mfc_name):
        self._config(mfc_name)
        return self._calibration_dates[mfc_name]

    def _mean_output_offset(self, mfc_name):
        offsets = self._output_offsets.get(mfc_name, {})
        return sum(offsets.values()) / len(offsets) if offsets else 0.0

    @staticmethod
    def _offset_setting_key(mfc_name, flow):
        return f"mfc/output_offsets/{mfc_name}/{flow:g}"

    def shutdown(self):
        for name, timer in tuple(self._calibration_timers.items()):
            timer.stop()
            timer.deleteLater()
            self._calibrations.pop(name, None)
            self.calibration_state_changed.emit(name, False)
        self._calibration_timers.clear()
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
