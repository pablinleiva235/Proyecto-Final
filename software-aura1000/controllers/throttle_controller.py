"""Movimiento manual del throttle con límites por finales de carrera."""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class ThrottleController(QObject):
    movement_changed = pyqtSignal(bool, str)
    position_changed = pyqtSignal(object)
    operation_error = pyqtSignal(str)
    initial_position_reached = pyqtSignal()
    automatic_motion_failed = pyqtSignal(str)
    safety_return_finished = pyqtSignal(bool, str)
    limit_state_changed = pyqtSignal(str, bool)

    PULSE_INTERVAL_MS = 5
    REST_POSITION_STEPS = 400
    HOMING_TIMEOUT_MS = 30000
    MAX_BURST_STEPS = 1400
    LIMIT_DEBOUNCE_READS = 3

    def __init__(self, hardware, can_operate=None, parent=None):
        super().__init__(parent)
        self._hardware = hardware
        self._can_operate = can_operate or (lambda: True)
        self._closing = None
        self._step_state = False
        self._position_steps = None
        self._automatic_mode = False
        self._homing_active = False
        self._safety_return_active = False
        self._remaining_steps = None
        self._motion_half_step = False
        self._starting_motion = False
        self._limit_counts = {"THROTTLE_OPEN": 0, "THROTTLE_CLOSED": 0}
        self._limit_stable = {"THROTTLE_OPEN": False, "THROTTLE_CLOSED": False}
        self._homing_timer = QTimer(self)
        self._homing_timer.setSingleShot(True)
        self._homing_timer.timeout.connect(self._homing_timed_out)
        self._safety_return_timer = QTimer(self)
        self._safety_return_timer.setSingleShot(True)
        self._safety_return_timer.timeout.connect(self._safety_return_timed_out)
        self._timer = QTimer(self)
        self._timer.setInterval(self.PULSE_INTERVAL_MS)
        self._timer.timeout.connect(self._pulse)
        self.initial_position_reached.connect(self._complete_safety_return)

    def start(self, closing):
        if self._automatic_mode:
            # debugg de control de presion y throttle
            print("[THROTTLE] Movimiento manual rechazado: control automático de presión activo.")
            self.operation_error.emit("El movimiento manual está bloqueado durante el control automático de presión.")
            return
        try:
            self._sample_limit_states()
            if not closing and self._limit_stable["THROTTLE_OPEN"]:
                self._set_position_steps(0.0)
        except Exception as error:
            # debugg de control de presion y throttle
            print(f"[THROTTLE] No se pudieron leer los finales de carrera antes de mover: {error}")
            self.operation_error.emit(str(error))
            return
        self._start_motion(bool(closing), self.PULSE_INTERVAL_MS)

    @property
    def position_steps(self):
        return self._position_steps

    def move_steps(self, closing, steps, half_step=False):
        """Ejecuta una ráfaga donde cada paso es un pulso del controlador."""
        if self._automatic_mode:
            # debugg de control de presion y throttle
            print("[THROTTLE] Movimiento por pasos rechazado: control automático de presión activo.")
            self.operation_error.emit("El movimiento por pasos está bloqueado durante el control de presión.")
            return
        if self._timer.isActive():
            # debugg de control de presion y throttle
            print("[THROTTLE] Movimiento por pasos rechazado: ya hay un movimiento activo.")
            self.operation_error.emit("Detenga el movimiento actual antes de solicitar pasos.")
            return
        try:
            count = int(steps)
            if isinstance(steps, bool) or count != steps or not 1 <= count <= self.MAX_BURST_STEPS:
                raise ValueError(f"La cantidad de pasos debe estar entre 1 y {self.MAX_BURST_STEPS}.")
            self._start_motion(
                bool(closing), self.PULSE_INTERVAL_MS,
                half_step=bool(half_step), remaining_steps=count,
            )
        except (TypeError, ValueError, OverflowError) as error:
            # debugg de control de presion y throttle
            print(f"[THROTTLE] Solicitud de pasos inválida: {error}")
            self.operation_error.emit(str(error))

    @property
    def is_reserved_for_pressure(self):
        return self._automatic_mode

    def _start_motion(self, closing, pulse_interval_ms, half_step=False, remaining_steps=None):
        if self._timer.isActive():
            return
        try:
            if not self._can_operate():
                raise RuntimeError("El movimiento manual requiere el vacío principal activo.")
            self._closing = closing
            self._starting_motion = True
            try:
                limit_active = self._limit_reached()
            finally:
                self._starting_motion = False
            if limit_active:
                limit_name = "THROTTLE_CLOSED" if closing else "THROTTLE_OPEN"
                # debugg de control de presion y throttle
                print(f"[THROTTLE] Movimiento no iniciado: final {limit_name} ya activo.")
                if self._automatic_mode and self._homing_active and not closing:
                    self._write("STEPPER_STEP", False)
                    self._step_state = False
                    return
                if self._automatic_mode:
                    self._fail_automatic_motion("La throttle está en el final de carrera solicitado.")
                else:
                    self.movement_changed.emit(False, "final de carrera alcanzado")
                return
            self._write("STEPPER_DIR", self._closing)
            self._write("STEPPER_HALF_STEP", bool(half_step))
            self._write("STEPPER_STEP", False)
            self._write("STEPPER_OUTPUT_ENABLE", True)
            self._step_state = False
            self._motion_half_step = bool(half_step)
            self._remaining_steps = remaining_steps
            self._timer.start(pulse_interval_ms)
            direction = "cerrando" if self._closing else "abriendo"
            if remaining_steps is not None and not self._automatic_mode:
                direction += " pasos"
            mode = "automático" if self._automatic_mode else "manual"
            if remaining_steps is None:
                step_description = "movimiento continuo"
            elif self._automatic_mode:
                step_description = f"{remaining_steps} pulsos programados"
            else:
                step_description = f"{remaining_steps} pasos solicitados"
            # debugg de control de presion y throttle
            print(
                f"[THROTTLE] Inicio {mode}: {direction}; {step_description}; "
                f"intervalo={pulse_interval_ms} ms; medio paso="
                f"{'sí' if half_step else 'no'}; posición="
                f"{self._position_steps!r} pasos."
            )
            self.movement_changed.emit(True, direction)
        except Exception as error:
            self._safe_stop()
            if self._automatic_mode:
                self._fail_automatic_motion(str(error))
            else:
                # debugg de control de presion y throttle
                print(f"[THROTTLE] No se pudo iniciar el movimiento manual: {error}")
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
        # debugg de control de presion y throttle
        print(
            f"[THROTTLE] Posicionamiento inicial para presión: "
            f"posición actual={self._position_steps!r} pasos."
        )
        try:
            self._sample_limit_states()
            if self._limit_stable["THROTTLE_OPEN"]:
                self._set_position_steps(0.0)
        except Exception:
            self._automatic_mode = False
            raise
        if self._position_steps is None:
            self._homing_active = True
            self._closing = False
            # debugg de control de presion y throttle
            print("[THROTTLE] Posición desconocida; iniciando homing hacia THROTTLE_OPEN.")
            self._homing_timer.start(self.HOMING_TIMEOUT_MS)
            self._start_motion(False, self.PULSE_INTERVAL_MS)
            if not self._timer.isActive() and self._automatic_mode and not self._homing_active:
                self._fail_automatic_motion("No se pudo iniciar el homing de apertura.")
            return
        self._move_to_rest_position()

    def return_to_rest_for_safety(self):
        """Stops current throttle motion and starts a bounded return to rest."""
        if self._safety_return_active:
            raise RuntimeError("Ya hay un retorno de seguridad de la throttle en curso.")
        if self._automatic_mode:
            stopped = self.stop_pressure_motion(release=True)
        else:
            stopped = self._safe_stop()
        if not stopped:
            raise RuntimeError(
                "No se pudo confirmar la detención previa de la throttle."
            )
        if not self._can_operate():
            raise RuntimeError(
                "No se puede llevar la throttle a reposo sin interlocks de operación confirmados."
            )

        self._safety_return_active = True
        # debugg de control de presion y throttle
        print("[THROTTLE] Inicio del retorno de seguridad a la posición de reposo.")
        self._safety_return_timer.start(self.HOMING_TIMEOUT_MS)
        try:
            self.move_to_pressure_start_position()
        except Exception as error:
            self._complete_safety_return(False, str(error))
            return False
        return self._safety_return_active

    def _move_to_rest_position(self):
        self.move_to_rest_position()

    def move_to_rest_position(self):
        """Reposiciona a 400 pasos mientras la presión mantiene reservado el motor."""
        if not self._automatic_mode:
            raise RuntimeError("El control automático de presión no reservó la throttle.")
        if self._position_steps is None:
            self._sample_limit_states()
            if self._limit_stable["THROTTLE_OPEN"]:
                self._set_position_steps(0.0)
            else:
                self._homing_active = True
                self._closing = False
                # debugg de control de presion y throttle
                print("[THROTTLE] Posición desconocida; iniciando homing para reposición.")
                self._homing_timer.start(self.HOMING_TIMEOUT_MS)
                self._start_motion(False, self.PULSE_INTERVAL_MS)
                if not self._timer.isActive() and self._automatic_mode and not self._homing_active:
                    self._fail_automatic_motion("No se pudo iniciar el homing para volver a reposo.")
                return
        distance = self.REST_POSITION_STEPS - self._position_steps
        # debugg de control de presion y throttle
        print(
            f"[THROTTLE] Reposición automática: posición={self._position_steps:.1f} "
            f"pasos; objetivo={self.REST_POSITION_STEPS} pasos; "
            f"distancia={distance:+.1f} pasos."
        )
        if distance == 0:
            self._homing_active = False
            self.initial_position_reached.emit()
            return
        self._closing = distance > 0
        half_step = not float(distance).is_integer()
        pulse_count = round(abs(distance) * (2 if half_step else 1))
        self._start_motion(
            self._closing, self.PULSE_INTERVAL_MS,
            half_step=half_step, remaining_steps=pulse_count,
        )
        if not self._timer.isActive() and self._automatic_mode:
            self._fail_automatic_motion("No se pudo alcanzar la posición inicial de la throttle.")

    def start_pressure_motion(self, closing, pulse_interval_ms, half_step=False):
        if not self._automatic_mode:
            raise RuntimeError("El control automático de presión no reservó la throttle.")
        if self._timer.isActive() and self._closing == bool(closing):
            self._timer.setInterval(pulse_interval_ms)
            if self._motion_half_step != bool(half_step):
                self._write("STEPPER_STEP", False)
                self._write("STEPPER_HALF_STEP", bool(half_step))
                self._step_state = False
                self._motion_half_step = bool(half_step)
            return
        if self._timer.isActive():
            self._timer.stop()
            self._step_state = False
            self._write("STEPPER_STEP", False)
        self._start_motion(bool(closing), pulse_interval_ms, half_step=half_step)

    def stop_pressure_motion(self, release=True):
        cancel_safety_return = release and self._safety_return_active
        if cancel_safety_return:
            self._safety_return_active = False
            self._safety_return_timer.stop()
        self._timer.stop()
        self._homing_timer.stop()
        self._step_state = False
        error = None
        try:
            self._write("STEPPER_STEP", False)
        except Exception as stop_error:
            error = str(stop_error)
        if release:
            try:
                self._write("STEPPER_OUTPUT_ENABLE", False)
            except Exception as stop_error:
                error = f"{error}; {stop_error}" if error else str(stop_error)
        self._closing = None
        self._remaining_steps = None
        self._homing_active = False
        if release:
            self._automatic_mode = False
        self.movement_changed.emit(False, "detenido")
        if error:
            # debugg de control de presion y throttle
            print(f"[THROTTLE] Error al detener el movimiento automático: {error}")
            self.operation_error.emit(error)
        if cancel_safety_return:
            self.safety_return_finished.emit(
                False, "El retorno de seguridad de la throttle fue interrumpido."
            )
        return error is None

    def _fail_automatic_motion(self, message):
        # debugg de control de presion y throttle
        print(f"[THROTTLE] Falló el movimiento automático: {message}")
        safety_return = self._safety_return_active
        self._safety_return_timer.stop()
        self._safety_return_active = False
        self.stop_pressure_motion()
        self._set_position_steps(None)
        self._homing_active = False
        if safety_return:
            self.safety_return_finished.emit(False, message)
        else:
            self.automatic_motion_failed.emit(message)

    def _complete_safety_return(self, success=True, message=None):
        if not self._safety_return_active:
            return
        self._safety_return_active = False
        self._safety_return_timer.stop()
        stopped = self.stop_pressure_motion(release=True)
        if not success:
            # debugg de control de presion y throttle
            print(f"[THROTTLE] Falló el retorno de seguridad: {message}")
            self.safety_return_finished.emit(
                False, message or "No se pudo llevar la throttle a reposo."
            )
        elif stopped:
            # debugg de control de presion y throttle
            print(
                f"[THROTTLE] Retorno de seguridad completado; "
                f"posición={self._position_steps!r} pasos."
            )
            self.safety_return_finished.emit(
                True, "La throttle llegó a la posición de reposo."
            )
        else:
            self.safety_return_finished.emit(
                False,
                "La throttle llegó a reposo, pero no se pudo confirmar la deshabilitación del motor.",
            )

    def _safety_return_timed_out(self):
        if self._safety_return_active:
            self._fail_automatic_motion(
                "La throttle no llegó a reposo dentro del tiempo límite de homing."
            )

    def stop(self):
        if self._automatic_mode:
            # debugg de control de presion y throttle
            print("[THROTTLE] Detención manual rechazada: use el control de presión.")
            self.operation_error.emit("Use el botón Detener del control de presión para detener el movimiento automático.")
            return
        try:
            was_moving = self._timer.isActive()
            self._safe_stop()
            if was_moving:
                # debugg de control de presion y throttle
                print(
                    f"[THROTTLE] Movimiento manual detenido; "
                    f"posición={self._position_steps!r} pasos."
                )
            self.movement_changed.emit(False, "detenido")
        except Exception as error:
            # debugg de control de presion y throttle
            print(f"[THROTTLE] Error al detener el movimiento manual: {error}")
            self.operation_error.emit(str(error))

    def stop_if_limit_reached(self):
        try:
            self._sample_limit_states()
            if self._timer.isActive() and not self._automatic_mode:
                if self._limit_reached():
                    self.stop()
        except Exception as error:
            if self._timer.isActive() and not self._automatic_mode:
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
                    self._step_state = False
                    self._write("STEPPER_STEP", False)
                    self._remaining_steps = None
                    self.movement_changed.emit(False, "detenido")
                    if self._limit_stable["THROTTLE_OPEN"]:
                        self._homing_timer.stop()
                        self._set_position_steps(0.0)
                        self._homing_active = False
                        self._move_to_rest_position()
                elif self._automatic_mode:
                    self._fail_automatic_motion("Se alcanzó un final de carrera antes de completar el movimiento.")
                else:
                    limit_name = "THROTTLE_CLOSED" if self._closing else "THROTTLE_OPEN"
                    # debugg de control de presion y throttle
                    print(f"[THROTTLE] Movimiento manual detenido por límite {limit_name}.")
                    self.stop()
                return
            self._step_state = not self._step_state
            self._write("STEPPER_STEP", self._step_state)
            if self._step_state:
                if self._position_steps is not None:
                    increment = 0.5 if self._motion_half_step else 1.0
                    position = self._position_steps + (
                        increment if self._closing else -increment
                    )
                    self._set_position_steps(position)
                if self._remaining_steps is not None:
                    self._remaining_steps -= 1
                    if self._remaining_steps <= 0:
                        self._timer.stop()
                        self._step_state = False
                        self._write("STEPPER_STEP", False)
                        self._closing = None
                        self._remaining_steps = None
                        if self._automatic_mode:
                            self._homing_active = False
                            self.initial_position_reached.emit()
                        else:
                            # debugg de control de presion y throttle
                            print(
                                f"[THROTTLE] Ráfaga manual completada; "
                                f"posición={self._position_steps!r} pasos."
                            )
                            self.movement_changed.emit(False, "detenido")
        except Exception as error:
            if self._automatic_mode:
                self._fail_automatic_motion(str(error))
            else:
                self.stop()
                # debugg de control de presion y throttle
                print(f"[THROTTLE] Error durante el movimiento manual: {error}")
                self.operation_error.emit(str(error))

    def _homing_timed_out(self):
        if self._automatic_mode and self._homing_active:
            self._fail_automatic_motion("No se confirmó el final de carrera de apertura durante el homing.")

    def _limit_reached(self):
        opened = self._hardware.digital_read("THROTTLE_OPEN")
        closed = self._hardware.digital_read("THROTTLE_CLOSED")
        self._record_limit_sample("THROTTLE_OPEN", opened)
        self._record_limit_sample("THROTTLE_CLOSED", closed)
        if (
            self._limit_stable["THROTTLE_OPEN"]
            and self._limit_stable["THROTTLE_CLOSED"]
        ):
            raise RuntimeError("Los dos finales de carrera del throttle están activos.")
        limit_name = "THROTTLE_CLOSED" if self._closing else "THROTTLE_OPEN"
        return self._limit_stable[limit_name]

    def _sample_limit_states(self):
        for name in ("THROTTLE_OPEN", "THROTTLE_CLOSED"):
            self._record_limit_sample(name, self._hardware.digital_read(name))

    def _record_limit_sample(self, name, active):
        active = bool(active)
        if active:
            self._limit_counts[name] = min(self.LIMIT_DEBOUNCE_READS, self._limit_counts[name] + 1)
        else:
            self._limit_counts[name] = max(0, self._limit_counts[name] - 1)
        stable = (
            self._limit_counts[name] >= self.LIMIT_DEBOUNCE_READS
            or (
                self._limit_stable[name]
                and self._limit_counts[name] > 0
            )
        )
        if stable != self._limit_stable[name]:
            self._limit_stable[name] = stable
            # debugg de control de presion y throttle
            print(
                f"[THROTTLE] Final {name}: "
                f"{'ACTIVO' if stable else 'INACTIVO'} estable."
            )
            self.limit_state_changed.emit(name, stable)
            if name == "THROTTLE_OPEN" and stable:
                self._set_position_steps(0.0)
                if (
                    self._automatic_mode and self._homing_active
                    and not self._timer.isActive() and not self._starting_motion
                ):
                    self._homing_timer.stop()
                    self._homing_active = False
                    self._move_to_rest_position()

    def _set_position_steps(self, position):
        if position == self._position_steps:
            return
        self._position_steps = position
        self.position_changed.emit(position)

    def _write(self, signal_name, active):
        if self._hardware.digital_read("DRIVER_ENABLE") is not True:
            raise RuntimeError("DRIVER_ENABLE debe estar activo para accionar la throttle.")
        self._hardware.digital_set(signal_name, active)
        if signal_name in ("STEPPER_DIR", "STEPPER_HALF_STEP", "STEPPER_OUTPUT_ENABLE"):
            # debugg de control de presion y throttle
            print(
                f"[THROTTLE] Señal {signal_name} cambiada a "
                f"{'ACTIVO' if active else 'INACTIVO'}."
            )

    def _safe_stop(self):
        self._timer.stop()
        self._step_state = False
        self._closing = None
        errors = []
        for signal_name in ("STEPPER_STEP", "STEPPER_OUTPUT_ENABLE"):
            try:
                self._write(signal_name, False)
            except Exception as error:
                errors.append(f"{signal_name}: {error}")
        if errors:
            # debugg de control de presion y throttle
            print(f"[THROTTLE] Falló la parada segura: {'; '.join(errors)}")
            self.operation_error.emit("; ".join(errors))
            return False
        return True
