"""Precalentamiento y regulación térmica por histéresis de las lámparas."""

from collections import deque
import math
import statistics
import time

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class TemperatureController(QObject):
    state_changed = pyqtSignal(str)
    temperature_changed = pyqtSignal(float)
    temperature_unavailable = pyqtSignal(str)
    setpoint_reached = pyqtSignal(float)
    operation_error = pyqtSignal(str)

    MIN_SETPOINT_C = 130.0
    MAX_SETPOINT_C = 200.0
    HYSTERESIS_C = 3.0
    RAMP_CUTOFF_OFFSET_C = 8.0
    FILTER_SAMPLES = 11
    STALE_READING_SECONDS = 1.5

    def __init__(self, process_controller, can_operate=None, parent=None):
        super().__init__(parent)
        self._process = process_controller
        self._can_operate = can_operate or (lambda: True)
        self._samples = deque(maxlen=self.FILTER_SAMPLES)
        self._temperature = None
        self._last_reading_at = None
        self._target = None
        self._state = "detenido"
        self._ramp_active = False
        self._target_reached = False
        self._watchdog = QTimer(self)
        self._watchdog.setInterval(250)
        self._watchdog.timeout.connect(self._check_runtime_conditions)

    @property
    def is_active(self):
        return self._state in ("precalentando", "manteniendo")

    @property
    def state(self):
        return self._state

    @property
    def temperature(self):
        return self._temperature

    def set_temperature_reading(self, value):
        try:
            temperature = float(value)
            if not math.isfinite(temperature):
                raise ValueError("La lectura de temperatura no es finita.")
        except (TypeError, ValueError) as error:
            self.invalidate_temperature(str(error))
            return

        self._last_reading_at = time.monotonic()
        self._samples.append(temperature)
        self._temperature = statistics.median(self._samples)
        self.temperature_changed.emit(self._temperature)
        if self.is_active:
            self._update_control(self._temperature)

    def invalidate_temperature(self, message="No hay una lectura válida de termocupla."):
        self._temperature = None
        self._last_reading_at = None
        self._samples.clear()
        self.temperature_unavailable.emit(message)
        if self.is_active:
            self._abort(message)

    def start(self, target_c):
        if self.is_active:
            self.operation_error.emit("El control automático de temperatura ya está activo.")
            return
        try:
            target = float(target_c)
            if not math.isfinite(target) or not self.MIN_SETPOINT_C <= target <= self.MAX_SETPOINT_C:
                raise ValueError("El setpoint debe estar entre 130 y 200 °C.")
            if not self._can_operate():
                raise RuntimeError("El control térmico requiere vacío principal activo, puerta cerrada y venteo inactivo.")
            if self._temperature is None or self._last_reading_at is None:
                raise RuntimeError("No hay una lectura actual de la termocupla.")
            if time.monotonic() - self._last_reading_at > self.STALE_READING_SECONDS:
                raise RuntimeError("La lectura de temperatura está desactualizada.")
            if self._process.plasma_active:
                raise RuntimeError("Apague el plasma antes de iniciar el control de lámparas.")

            self._target = target
            self._ramp_active = True
            self._target_reached = False
            self._set_state("precalentando")
            self._watchdog.start()
            if not self._process.set_lamps13(True) or not self._process.set_lamp2(True):
                self._abort("No se pudieron activar las lámparas para el precalentamiento.")
        except Exception as error:
            self._watchdog.stop()
            self._target = None
            self._ramp_active = False
            self._set_state("detenido")
            self.operation_error.emit(str(error))

    def stop(self):
        self._watchdog.stop()
        self._target = None
        self._ramp_active = False
        if not self._turn_lamps_off():
            self.operation_error.emit("No se pudieron confirmar todas las lámparas apagadas.")
        self._set_state("detenido")

    def abort(self, message):
        if self.is_active:
            self._abort(message)

    def _update_control(self, temperature):
        if self._target is None:
            return
        if self._ramp_active:
            if temperature >= self._target - self.RAMP_CUTOFF_OFFSET_C:
                if not self._process.set_lamps13(False):
                    self._abort("No se pudieron apagar las lámparas externas al finalizar la rampa.")
                    return
                self._ramp_active = False
                self._set_state("manteniendo")
            return

        low = self._target - self.HYSTERESIS_C
        high = self._target + self.HYSTERESIS_C
        if temperature <= low and not self._process.lamp2_active:
            if not self._process.set_lamp2(True):
                self._abort("No se pudo encender la lámpara central.")
                return
        elif temperature >= high and self._process.lamp2_active:
            if not self._process.set_lamp2(False):
                self._abort("No se pudo apagar la lámpara central.")
                return

        if not self._target_reached and abs(temperature - self._target) <= self.HYSTERESIS_C:
            self._target_reached = True
            self.setpoint_reached.emit(self._target)

    def _check_runtime_conditions(self):
        if not self.is_active:
            return
        if not self._can_operate():
            self._abort("Se perdió el vacío principal, la confirmación de puerta cerrada o el interlock de venteo.")
        elif self._last_reading_at is None or time.monotonic() - self._last_reading_at > self.STALE_READING_SECONDS:
            self._abort("Se perdió la lectura actualizada de la termocupla.")

    def _abort(self, message):
        self._watchdog.stop()
        self._target = None
        self._ramp_active = False
        if not self._turn_lamps_off():
            message += " No se pudieron confirmar todas las lámparas apagadas; verifique las salidas."
        self._set_state("detenido")
        self.operation_error.emit(message)

    def _turn_lamps_off(self):
        outer_lamps_off = self._process.set_lamps13(False)
        center_lamp_off = self._process.set_lamp2(False)
        return outer_lamps_off and center_lamp_off

    def _set_state(self, state):
        self._state = state
        self.state_changed.emit(state)
