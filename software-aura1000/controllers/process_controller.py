"""Control de lámparas/plasma y supervisión de sus señales de falla."""

import time
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class ProcessController(QObject):
    operation_error = pyqtSignal(str, str)
    alarm_raised = pyqtSignal(str)
    warning_raised = pyqtSignal(str)
    state_changed = pyqtSignal(str, bool)

    IGNITION_DELAY_S = 2.0

    def __init__(self, hardware, can_operate=None, can_enable_plasma=None, parent=None):
        super().__init__(parent)
        self._hardware = hardware
        self._can_operate = can_operate or (lambda: True)
        self._can_enable_plasma = can_enable_plasma or (lambda: True)
        self._lamps13 = False
        self._lamp2 = False
        self._plasma = False
        self._plasma_started_at = 0.0
        self._warning_shown = False
        self._pulse_timer = QTimer(self)
        self._pulse_timer.setSingleShot(True)
        self._pulse_timer.timeout.connect(self._finish_lamps13)

    def set_controls_enabled(self, enabled):
        if not enabled:
            self.stop_all()

    @property
    def lamp2_active(self):
        return self._lamp2

    @property
    def plasma_active(self):
        return self._plasma

    def fault_monitoring_state(self):
        """Indica qué entradas de falla están habilitadas para interpretación."""
        plasma_grace_passed = (
            self._plasma
            and time.monotonic() - self._plasma_started_at > self.IGNITION_DELAY_S
        )
        return {
            "LAMP1_FAIL": self._lamps13,
            "LAMP2_FAIL": self._lamp2,
            "LAMP3_FAIL": self._lamps13,
            "PLASMA_FAIL": plasma_grace_passed,
        }

    def start_lamps13(self, seconds):
        hardware_attempted = False
        try:
            duration = float(seconds)
            if not 0 < duration <= 28:
                raise ValueError("El pulso debe durar más de 0 y hasta 28 segundos.")
            self._require_operation()
            hardware_attempted = True
            self._write("LAMP1_ON_CMD", True)
            self._write("LAMP3_ON_CMD", True)
            self._lamps13 = True
            self._pulse_timer.start(round(duration * 1000))
            self.state_changed.emit("lamps13", True)
        except Exception as error:
            if hardware_attempted:
                for signal in ("LAMP1_ON_CMD", "LAMP3_ON_CMD"):
                    try:
                        self._write(signal, False)
                    except Exception:
                        pass
                self._lamps13 = False
                self.state_changed.emit("lamps13", False)
            self.operation_error.emit("Lámparas 1 y 3", str(error))

    def set_lamps13(self, enabled):
        """Mantiene L1/L3 en el estado solicitado, sin temporizador de pulso."""
        enabled = bool(enabled)
        try:
            if enabled:
                self._require_operation()
            self._pulse_timer.stop()
            self._write("LAMP1_ON_CMD", enabled)
            self._write("LAMP3_ON_CMD", enabled)
            self._lamps13 = enabled
            self.state_changed.emit("lamps13", enabled)
            return True
        except Exception as error:
            # A partial write must not leave one outer lamp energized.
            for signal in ("LAMP1_ON_CMD", "LAMP3_ON_CMD"):
                try:
                    self._write(signal, False)
                except Exception:
                    pass
            self._lamps13 = False
            self.state_changed.emit("lamps13", False)
            self.operation_error.emit("L?mparas 1 y 3", str(error))
            return False

    def set_lamp2(self, enabled):
        return self._set_output("LAMP2_ON_CMD", "lamp2", enabled)

    def set_plasma(self, enabled):
        if enabled:
            try:
                self._require_operation()
                if not self._can_enable_plasma():
                    raise RuntimeError("Para activar plasma, abra MFC1 y configure una consigna de O₂ mayor que cero.")
                self._write("RF_ON_CMD", True)
                self._plasma = True
                self._plasma_started_at = time.monotonic()
                self.state_changed.emit("plasma", True)
            except Exception as error:
                try:
                    self._write("RF_ON_CMD", False)
                except Exception:
                    pass
                self._plasma = False
                self.state_changed.emit("plasma", False)
                self.operation_error.emit("Plasma", str(error))
        else:
            self._set_output("RF_ON_CMD", "plasma", False)
            self._plasma_started_at = 0.0

    def check_faults(self):
        try:
            lamp1 = self._lamps13 and self._hardware.digital_read("LAMP1_FAIL")
            lamp2 = self._lamp2 and self._hardware.digital_read("LAMP2_FAIL")
            lamp3 = self._lamps13 and self._hardware.digital_read("LAMP3_FAIL")
            plasma = (
                self._plasma
                and time.monotonic() - self._plasma_started_at > self.IGNITION_DELAY_S
                and self._hardware.digital_read("PLASMA_FAIL")
            )
            warning = self._hardware.digital_read("MAGNETRON_WARNING")
            overheat = self._hardware.digital_read("MAGNETRON_OVERHEAT")
            failures = []
            if lamp1: failures.append("Falla en lámpara 1 (pérdida de corriente).")
            if lamp2: failures.append("Falla en lámpara 2 (pérdida de corriente).")
            if lamp3: failures.append("Falla en lámpara 3 (pérdida de corriente).")
            if plasma: failures.append("Falla en plasma (no encendió o se interrumpió la RF).")
            if overheat: failures.append("Sobretemperatura del magnetrón.")
            if failures:
                self.stop_all()
                self._write("ALARM_INDICATION", True)
                self.alarm_raised.emit("\n".join(failures))
            elif warning and not self._warning_shown:
                self._warning_shown = True
                self._write("ALARM_INDICATION", True)
                self.warning_raised.emit("El magnetrón alcanzó la señal de advertencia de temperatura.")
            elif not warning:
                self._warning_shown = False
                self._write("ALARM_INDICATION", False)
        except Exception as error:
            self.operation_error.emit("Monitoreo de fallas", str(error))

    def stop_all(self):
        self._pulse_timer.stop()
        errors = []
        for signal in ("LAMP1_ON_CMD", "LAMP2_ON_CMD", "LAMP3_ON_CMD", "RF_ON_CMD"):
            try:
                self._write(signal, False)
            except Exception as error:
                errors.append(f"{signal}: {error}")
        self._lamps13 = self._lamp2 = self._plasma = False
        self._plasma_started_at = 0.0
        for name in ("lamps13", "lamp2", "plasma"):
            self.state_changed.emit(name, False)
        if errors:
            raise RuntimeError("; ".join(errors))

    def _finish_lamps13(self):
        try:
            self._write("LAMP1_ON_CMD", False)
            self._write("LAMP3_ON_CMD", False)
            self._lamps13 = False
            self.state_changed.emit("lamps13", False)
        except Exception as error:
            self.operation_error.emit("Lámparas 1 y 3", str(error))

    def _set_output(self, signal, state_name, enabled):
        try:
            if enabled:
                self._require_operation()
            self._write(signal, bool(enabled))
            setattr(self, "_" + state_name, bool(enabled))
            self.state_changed.emit(state_name, bool(enabled))
            if state_name == "plasma" and not enabled:
                self._plasma_started_at = 0.0
            return True
        except Exception as error:
            if enabled:
                try:
                    self._write(signal, False)
                except Exception:
                    pass
                setattr(self, "_" + state_name, False)
                self.state_changed.emit(state_name, False)
            self.operation_error.emit(state_name, str(error))
            return False

    def _require_operation(self):
        if not self._can_operate():
            raise RuntimeError("Para activar lámparas o plasma, el vacío principal debe estar activo y la puerta cerrada.")

    def _write(self, signal, active):
        self._hardware.digital_set(signal, active)
