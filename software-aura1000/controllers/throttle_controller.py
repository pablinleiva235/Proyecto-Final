"""Movimiento manual del throttle con límites por finales de carrera."""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class ThrottleController(QObject):
    movement_changed = pyqtSignal(bool, str)
    operation_error = pyqtSignal(str)

    PULSE_INTERVAL_MS = 5

    def __init__(self, hardware, can_operate=None, parent=None):
        super().__init__(parent)
        self._hardware = hardware
        self._can_operate = can_operate or (lambda: True)
        self._closing = None
        self._step_state = False
        self._timer = QTimer(self)
        self._timer.setInterval(self.PULSE_INTERVAL_MS)
        self._timer.timeout.connect(self._pulse)

    def start(self, closing):
        if self._timer.isActive():
            return
        try:
            if not self._can_operate():
                raise RuntimeError("El movimiento manual requiere el vacío principal activo.")
            self._closing = bool(closing)
            if self._limit_reached():
                self.movement_changed.emit(False, "final de carrera alcanzado")
                return
            self._hardware.digital_set("STEPPER_DIR", self._closing)
            self._hardware.digital_set("STEPPER_HALF_STEP", False)
            self._hardware.digital_set("STEPPER_STEP", False)
            self._hardware.digital_set("STEPPER_OUTPUT_ENABLE", True)
            self._step_state = False
            self._timer.start()
            self.movement_changed.emit(True, "cerrando" if self._closing else "abriendo")
        except Exception as error:
            self._safe_stop()
            self.operation_error.emit(str(error))

    def stop(self):
        try:
            self._safe_stop()
            self.movement_changed.emit(False, "detenido")
        except Exception as error:
            self.operation_error.emit(str(error))

    def stop_if_limit_reached(self):
        if self._timer.isActive():
            try:
                if self._limit_reached():
                    self.stop()
            except Exception as error:
                self.stop()
                self.operation_error.emit(str(error))

    def _pulse(self):
        try:
            if self._limit_reached():
                self.stop()
                return
            self._step_state = not self._step_state
            self._hardware.digital_set("STEPPER_STEP", self._step_state)
        except Exception as error:
            self.stop()
            self.operation_error.emit(str(error))

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
