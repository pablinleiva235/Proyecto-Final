"""Movimiento manual del throttle con límites por finales de carrera."""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class ThrottleController(QObject):
    movement_changed = pyqtSignal(bool, str)
    operation_error = pyqtSignal(str)
    initial_position_reached = pyqtSignal()
    automatic_motion_failed = pyqtSignal(str)

    PULSE_INTERVAL_MS = 5
    REST_POSITION_STEPS = 400
    HOMING_TIMEOUT_MS = 30000

    def __init__(self, hardware, can_operate=None, parent=None):
        super().__init__(parent)
        self._hardware = hardware
        self._can_operate = can_operate or (lambda: True)
        self._closing = None
        self._step_state = False
        self._position_steps = None
        self._automatic_mode = False
        self._homing_active = False
        self._remaining_steps = None
        self._homing_timer = QTimer(self)
        self._homing_timer.setSingleShot(True)
        self._homing_timer.timeout.connect(self._homing_timed_out)
        self._timer = QTimer(self)
        self._timer.setInterval(self.PULSE_INTERVAL_MS)
        self._timer.timeout.connect(self._pulse)

    def start(self, closing):
        if self._automatic_mode:
            self.operation_error.emit("El movimiento manual está bloqueado durante el control automático de presión.")
            return
        try:
            if not closing and self._hardware.digital_read("THROTTLE_OPEN"):
                self._position_steps = 0
        except Exception as error:
            self.operation_error.emit(str(error))
            return
        self._start_motion(bool(closing), self.PULSE_INTERVAL_MS)

    @property
    def is_reserved_for_pressure(self):
        return self._automatic_mode

    def _start_motion(self, closing, pulse_interval_ms):
        if self._timer.isActive():
            return
        try:
            if not self._can_operate():
                raise RuntimeError("El movimiento manual requiere el vacío principal activo.")
            self._closing = closing
            if self._limit_reached():
                if self._automatic_mode:
                    self._fail_automatic_motion("La throttle está en el final de carrera solicitado.")
                else:
                    self.movement_changed.emit(False, "final de carrera alcanzado")
                return
            self._hardware.digital_set("STEPPER_DIR", self._closing)
            self._hardware.digital_set("STEPPER_HALF_STEP", False)
            self._hardware.digital_set("STEPPER_STEP", False)
            self._hardware.digital_set("STEPPER_OUTPUT_ENABLE", True)
            self._step_state = False
            self._timer.start(pulse_interval_ms)
            self.movement_changed.emit(True, "cerrando" if self._closing else "abriendo")
        except Exception as error:
            self._safe_stop()
            if self._automatic_mode:
                self._fail_automatic_motion(str(error))
            else:
                self.operation_error.emit(str(error))

    def move_to_pressure_start_position(self):
        """Homing al límite abierto si hace falta y posicionamiento a 400 pasos."""
        if self._automatic_mode:
            raise RuntimeError("La throttle ya está reservada para un movimiento automático.")
        if self._timer.isActive():
            raise RuntimeError("Detenga el movimiento manual de la throttle antes de iniciar el control de presión.")
        if not self._can_operate():
            raise RuntimeError("El posicionamiento requiere vacío principal activo y puerta cerrada.")
        self._automatic_mode = True
        self._remaining_steps = None
        try:
            opened = self._hardware.digital_read("THROTTLE_OPEN")
            closed = self._hardware.digital_read("THROTTLE_CLOSED")
            if opened and closed:
                raise RuntimeError("Los dos finales de carrera del throttle están activos.")
            if opened:
                self._position_steps = 0
        except Exception:
            self._automatic_mode = False
            raise
        if self._position_steps is None:
            self._homing_active = True
            self._closing = False
            self._homing_timer.start(self.HOMING_TIMEOUT_MS)
            self._start_motion(False, self.PULSE_INTERVAL_MS)
            if not self._timer.isActive() and self._automatic_mode:
                self._fail_automatic_motion("No se pudo iniciar el homing de apertura.")
            return
        self._move_to_rest_position()

    def _move_to_rest_position(self):
        distance = self.REST_POSITION_STEPS - self._position_steps
        if distance == 0:
            self._homing_active = False
            self.initial_position_reached.emit()
            return
        self._remaining_steps = abs(distance)
        self._closing = distance > 0
        self._start_motion(self._closing, self.PULSE_INTERVAL_MS)
        if not self._timer.isActive() and self._automatic_mode:
            self._fail_automatic_motion("No se pudo alcanzar la posición inicial de la throttle.")

    def start_pressure_motion(self, closing, pulse_interval_ms):
        if not self._automatic_mode:
            raise RuntimeError("El control automático de presión no reservó la throttle.")
        if self._timer.isActive() and self._closing == bool(closing):
            self._timer.setInterval(pulse_interval_ms)
            return
        if self._timer.isActive():
            self._timer.stop()
            self._step_state = False
            self._hardware.digital_set("STEPPER_STEP", False)
        self._start_motion(bool(closing), pulse_interval_ms)

    def stop_pressure_motion(self, release=True):
        self._timer.stop()
        self._homing_timer.stop()
        self._step_state = False
        error = None
        try:
            self._hardware.digital_set("STEPPER_STEP", False)
        except Exception as stop_error:
            error = str(stop_error)
        finally:
            self._closing = None
            self._remaining_steps = None
            self._homing_active = False
            if release:
                self._automatic_mode = False
            self.movement_changed.emit(False, "detenido")
        if error:
            self.operation_error.emit(error)

    def _fail_automatic_motion(self, message):
        self.stop_pressure_motion()
        self._position_steps = None
        self._homing_active = False
        self.automatic_motion_failed.emit(message)

    def stop(self):
        if self._automatic_mode:
            self.operation_error.emit("Use el botón Detener del control de presión para detener el movimiento automático.")
            return
        try:
            self._safe_stop()
            self.movement_changed.emit(False, "detenido")
        except Exception as error:
            self.operation_error.emit(str(error))

    def stop_if_limit_reached(self):
        if self._timer.isActive() and not self._automatic_mode:
            try:
                if self._limit_reached():
                    self.stop()
            except Exception as error:
                self.stop()
                self.operation_error.emit(str(error))

    def _pulse(self):
        if not self._timer.isActive():
            return
        try:
            if not self._can_operate():
                if self._automatic_mode:
                    self._fail_automatic_motion("Se perdió un interlock durante el movimiento de la throttle.")
                else:
                    self.stop()
                    self.operation_error.emit("Se perdió el interlock de vacío o puerta cerrada.")
                return
            if self._limit_reached():
                if self._automatic_mode and self._homing_active and not self._closing:
                    self._timer.stop()
                    self._homing_timer.stop()
                    self._step_state = False
                    self._hardware.digital_set("STEPPER_STEP", False)
                    self._position_steps = 0
                    self._homing_active = False
                    self._remaining_steps = None
                    self._move_to_rest_position()
                elif self._automatic_mode:
                    self._fail_automatic_motion("Se alcanzó un final de carrera antes de completar el movimiento.")
                else:
                    if not self._closing and self._position_steps is not None:
                        self._position_steps = 0
                    self.stop()
                return
            self._step_state = not self._step_state
            self._hardware.digital_set("STEPPER_STEP", self._step_state)
            if self._step_state:
                if self._position_steps is not None:
                    self._position_steps += 1 if self._closing else -1
                if self._remaining_steps is not None:
                    self._remaining_steps -= 1
                    if self._remaining_steps <= 0:
                        self._timer.stop()
                        self._step_state = False
                        self._hardware.digital_set("STEPPER_STEP", False)
                        self._closing = None
                        self._remaining_steps = None
                        if self._automatic_mode:
                            self._homing_active = False
                            self.initial_position_reached.emit()
                        else:
                            self.movement_changed.emit(False, "detenido")
        except Exception as error:
            if self._automatic_mode:
                self._fail_automatic_motion(str(error))
            else:
                self.stop()
                self.operation_error.emit(str(error))

    def _homing_timed_out(self):
        if self._automatic_mode and self._homing_active:
            self._fail_automatic_motion("No se confirmó el final de carrera de apertura durante el homing.")

    def _limit_reached(self):
        opened = self._hardware.digital_read("THROTTLE_OPEN")
        closed = self._hardware.digital_read("THROTTLE_CLOSED")
        if opened and closed:
            raise RuntimeError("Los dos finales de carrera del throttle están activos.")
        return closed if self._closing else opened

    def _safe_stop(self):
        self._timer.stop()
        self._step_state = False
        self._closing = None
        errors = []
        for signal_name in ("STEPPER_STEP", "STEPPER_OUTPUT_ENABLE"):
            try:
                self._hardware.digital_set(signal_name, False)
            except Exception as error:
                errors.append(f"{signal_name}: {error}")
        if errors:
            self.operation_error.emit("; ".join(errors))
