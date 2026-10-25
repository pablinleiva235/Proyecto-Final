"""Lazo de presión que coordina lecturas analógicas y movimiento de throttle."""

import math
import time

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class PressureController(QObject):
    state_changed = pyqtSignal(str)
    pressure_changed = pyqtSignal(float)
    pressure_unavailable = pyqtSignal(str)
    setpoint_reached = pyqtSignal(float)
    operation_error = pyqtSignal(str)

    MAX_PRESSURE_TORR = 3.0
    MAX_BARATRON_PRESSURE_TORR = 10.0
    DEADBAND_TORR = 0.015
    STALE_READING_SECONDS = 1.0

    def __init__(self, throttle_controller, can_operate=None, parent=None):
        super().__init__(parent)
        self._throttle = throttle_controller
        self._can_operate = can_operate or (lambda: True)
        self._pressure = None
        self._last_reading_at = None
        self._target = None
        self._target_reached = False
        self._state = "detenido"
        self._watchdog = QTimer(self)
        self._watchdog.setInterval(100)
        self._watchdog.timeout.connect(self._check_runtime_conditions)
        self._throttle.initial_position_reached.connect(self._on_initial_position_reached)
        self._throttle.automatic_motion_failed.connect(self._on_throttle_failure)

    @property
    def is_active(self):
        return self._state in ("posicionando", "regulando")

    @property
    def state(self):
        return self._state

    @property
    def pressure(self):
        return self._pressure

    def set_pressure_reading(self, pressure_torr):
        try:
            pressure = float(pressure_torr)
            if not math.isfinite(pressure) or not 0 <= pressure <= self.MAX_BARATRON_PRESSURE_TORR:
                raise ValueError("La lectura BARATRON debe ser finita y estar entre 0 y 10 Torr.")
        except (TypeError, ValueError) as error:
            self.invalidate_pressure(str(error))
            return
        self._pressure = pressure
        self._last_reading_at = time.monotonic()
        self.pressure_changed.emit(pressure)
        if self._state == "regulando":
            self._apply_pressure_correction(pressure)

    def invalidate_pressure(self, message="No hay una lectura BARATRON válida."):
        self._pressure = None
        self._last_reading_at = None
        self.pressure_unavailable.emit(message)
        if self.is_active:
            self._stop_with_error(message)

    def start(self, target_torr):
        if self.is_active:
            self.operation_error.emit("El control automático de presión ya está activo.")
            return
        try:
            target = float(target_torr)
            if not math.isfinite(target) or not 0.0 <= target <= self.MAX_PRESSURE_TORR:
                raise ValueError("El setpoint debe ser un valor finito entre 0 y 3 Torr.")
            if not self._can_operate():
                raise RuntimeError("El control requiere vacío principal activo y puerta cerrada.")
            if self._pressure is None or self._last_reading_at is None:
                raise RuntimeError("No hay una lectura BARATRON disponible.")
            if time.monotonic() - self._last_reading_at > self.STALE_READING_SECONDS:
                raise RuntimeError("La lectura BARATRON está desactualizada.")
            if target < self._pressure:
                raise ValueError(
                    f"El setpoint ({target:.3f} Torr) es menor que la presión actual "
                    f"({self._pressure:.3f} Torr). Ajuste el caudal de gas o espere a que baje la presión."
                )
            self._target = target
            self._target_reached = False
            self._set_state("posicionando")
            self._watchdog.start()
            self._throttle.move_to_pressure_start_position()
        except Exception as error:
            self._watchdog.stop()
            if self._throttle.is_reserved_for_pressure:
                self._throttle.stop_pressure_motion(release=True)
            self._target = None
            self._set_state("detenido")
            self.operation_error.emit(str(error))

    def stop(self):
        self._watchdog.stop()
        self._target = None
        if self._throttle.is_reserved_for_pressure:
            self._throttle.stop_pressure_motion(release=True)
        self._set_state("detenido")

    def abort(self, message):
        """Detiene el lazo y comunica por qué se perdió la condición de operación."""
        self._stop_with_error(message)

    def _on_initial_position_reached(self):
        if self._state != "posicionando":
            return
        if not self._can_operate():
            self._stop_with_error("Se perdió un interlock antes de iniciar el lazo de presión.")
            return
        if self._pressure is None:
            self._stop_with_error("No hay una lectura BARATRON para iniciar el lazo.")
            return
        self._set_state("regulando")
        self._apply_pressure_correction(self._pressure)

    def _apply_pressure_correction(self, pressure):
        if self._target is None:
            return
        error = self._target - pressure
        if abs(error) <= self.DEADBAND_TORR:
            self._throttle.stop_pressure_motion(release=False)
            if not self._target_reached:
                self._target_reached = True
                self.setpoint_reached.emit(self._target)
            return

        if error > 0.3:
            pulse_interval_ms = 2
        elif error > 0.15:
            pulse_interval_ms = 4
        elif error > 0.05:
            pulse_interval_ms = 6
        else:
            pulse_interval_ms = 10
        self._throttle.start_pressure_motion(error > 0, pulse_interval_ms)

    def _check_runtime_conditions(self):
        if not self.is_active:
            return
        if not self._can_operate():
            self._stop_with_error("Se perdió el vacío principal, la puerta cerrada o el interlock de venteo.")
        elif self._last_reading_at is None or time.monotonic() - self._last_reading_at > self.STALE_READING_SECONDS:
            self._stop_with_error("Se perdió la lectura actualizada del Baratron.")

    def _on_throttle_failure(self, message):
        if self.is_active:
            self._stop_with_error(message)

    def _stop_with_error(self, message):
        self._watchdog.stop()
        self._target = None
        try:
            self._throttle.stop_pressure_motion(release=True)
        finally:
            self._set_state("detenido")
            self.operation_error.emit(message)

    def _set_state(self, state):
        self._state = state
        self.state_changed.emit(state)
