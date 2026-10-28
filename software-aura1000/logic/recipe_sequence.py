"""Coordinación del ciclo automático de una receta."""

from enum import Enum
from datetime import datetime

from PyQt5.QtCore import QObject, pyqtSignal

from controllers.mfc_controller import MFCController
from logic.door_sequence import DoorState
from logic.main_vacuum_sequence import MainVacuumState
from logic.soft_vacuum_sequence import SoftVacuumState
from logic.vent_sequence import VentState
from services.recipe_log import (
    RECIPE_DATA_PATH, RECIPE_LOG_PATH, RecipeDataLog, RecipeLog,
    next_recipe_log_paths,
)


class RecipeState(Enum):
    IDLE = "idle"
    WAITING_FOR_WAFER = "waiting_for_wafer"
    WAITING_FOR_WAFER_REMOVAL = "waiting_for_wafer_removal"
    CLOSING_DOOR = "closing_door"
    CLOSING_DOOR_AFTER_RECIPE = "closing_door_after_recipe"
    VERIFYING_DOOR_CLOSED = "verifying_door_closed"
    VERIFYING_DOOR_CLOSED_AFTER_RECIPE = "verifying_door_closed_after_recipe"
    STARTING_SOFT_VACUUM = "starting_soft_vacuum"
    STARTING_MAIN_VACUUM = "starting_main_vacuum"
    PUMPING_TO_BASE = "pumping_to_base"
    STARTING_GAS_FLOW = "starting_gas_flow"
    CONTROLLING_PRESSURE = "controlling_pressure"
    CONTROLLING_TEMPERATURE = "controlling_temperature"
    RUNNING_PLASMA = "running_plasma"
    STOPPING_PROCESS = "stopping_process"
    VENTING = "venting"
    COMPLETED = "completed"
    ERROR = "error"


class RecipeSequence(QObject):
    """Coordina controladores existentes sin bloquear el event loop de Qt."""

    state_changed = pyqtSignal(object)
    wafer_confirmation_requested = pyqtSignal()
    wafer_removal_confirmation_requested = pyqtSignal()
    error_raised = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(
        self, door_sequence, soft_vacuum_sequence, main_vacuum_sequence,
        vent_sequence, mfc_controller, pressure_controller,
        temperature_controller, process_controller, digital_state_getter=None,
        recipe_log_factory=None, parent=None, recipe_data_log_factory=None,
        digital_state_setter=None, digital_hardware_reader=None,
    ):
        super().__init__(parent)
        self.door = door_sequence
        self.soft_vacuum = soft_vacuum_sequence
        self.main_vacuum = main_vacuum_sequence
        self.vent = vent_sequence
        self.mfc = mfc_controller
        self.pressure = pressure_controller
        self.temperature = temperature_controller
        self.process = process_controller
        self._digital_state_getter = digital_state_getter or (lambda _name: None)
        self._digital_state_setter = digital_state_setter
        self._digital_hardware_reader = digital_hardware_reader
        self._recipe_log_factory = recipe_log_factory or RecipeLog
        self._recipe_data_log_factory = recipe_data_log_factory or RecipeDataLog
        self._use_rotating_recipe_paths = (
            recipe_log_factory is None and recipe_data_log_factory is None
        )
        self._recipe_log = None
        self._recipe_data_log = None
        self._analog_readings = {}
        self._logging_failed = False
        self._data_logging_failed = False
        self._log_saved = False
        self._data_log_saved = False
        self._finalizing = False
        self._recipe = None
        self._state = RecipeState.IDLE
        self._stopping = False
        self._eop = None
        self._vacuum_started = False

    @property
    def state(self):
        return self._state

    @property
    def is_active(self):
        return self._state not in (
            RecipeState.IDLE, RecipeState.COMPLETED, RecipeState.ERROR,
        )

    @property
    def log_path(self):
        return self._recipe_log.path if self._recipe_log is not None else RECIPE_LOG_PATH

    @property
    def log_saved(self):
        return self._log_saved

    @property
    def data_log_path(self):
        return self._recipe_data_log.path if self._recipe_data_log is not None else RECIPE_DATA_PATH

    @property
    def data_log_saved(self):
        return self._data_log_saved

    def start(self, recipe):
        if self.is_active:
            self.error_raised.emit("Ya hay una receta en ejecución.")
            return False
        self._recipe = recipe
        self._stopping = False
        self._eop = None
        self._failed = False
        self._completion_message = ""
        self._shutdown_errors = []
        self._vacuum_started = False
        if self.door.state != DoorState.CLOSED:
            self.error_raised.emit("La puerta debe estar cerrada antes de iniciar una receta.")
            return False
        if self.vent.state != VentState.IDLE:
            self.error_raised.emit("El venteo debe estar detenido antes de iniciar una receta.")
            return False
        if (self.soft_vacuum.state != SoftVacuumState.IDLE
                or self.main_vacuum.state != MainVacuumState.IDLE):
            self.error_raised.emit("Soft Vacuum y Main Vacuum deben estar detenidos antes de iniciar una receta.")
            return False
        if (self._digital_state_getter("DOOR_OPEN") is not False
                or self._digital_state_getter("DOOR_CLOSE") is not True):
            self.error_raised.emit("Las entradas digitales no confirman la puerta cerrada.")
            return False
        if self._use_rotating_recipe_paths:
            log_path, data_log_path = next_recipe_log_paths()
            self._recipe_log = self._recipe_log_factory(log_path)
            self._recipe_data_log = self._recipe_data_log_factory(data_log_path)
        else:
            self._recipe_log = self._recipe_log_factory()
            self._recipe_data_log = self._recipe_data_log_factory()
        self._logging_failed = not self._recipe_log.available
        self._data_logging_failed = not self._recipe_data_log.available
        self._log_saved = False
        self._data_log_saved = False
        if self._logging_failed:
            self._handle_log_failure()
            return False
        if self._data_logging_failed:
            self._handle_data_log_failure()
            return False
        if not self._log_event(
            f"INICIO DE RECETA | nombre={recipe.name} | descripcion={recipe.description} | "
            f"O2={recipe.o2_flow:g} SLPM | N2={recipe.n2_flow:g} SLPM | "
            f"presion_base={recipe.base_pressure:g} Torr | "
            f"presion_proceso={recipe.process_pressure:g} Torr | "
            f"temperatura={recipe.process_temperature:g} C"
        ):
            return False
        try:
            driver_enabled = (
                self._digital_hardware_reader("DRIVER_ENABLE")
                if self._digital_hardware_reader is not None
                else self._digital_state_getter("DRIVER_ENABLE")
            )
            if driver_enabled is not True:
                if self._digital_state_setter is None:
                    raise RuntimeError("No hay un controlador disponible para activar la salida.")
                if not self._perform_action(
                    "Activar DRIVER_ENABLE",
                    lambda: self._digital_state_setter("DRIVER_ENABLE", True),
                    outputs={"DRIVER_ENABLE": True},
                ):
                    return False
                driver_enabled = (
                    self._digital_hardware_reader("DRIVER_ENABLE")
                    if self._digital_hardware_reader is not None
                    else self._digital_state_getter("DRIVER_ENABLE")
                )
            if driver_enabled is not True:
                raise RuntimeError("La lectura de confirmación sigue inactiva.")
        except Exception as error:
            message = f"No se pudo confirmar DRIVER_ENABLE activa: {error}"
            self._finish(True, message)
            return False
        if not self._set_state(RecipeState.WAITING_FOR_WAFER):
            return False
        if not self._perform_action("Abrir puerta para cargar la oblea", self.door.open,
                                    outputs={"DOOR_CLOSE_CMD": False, "DOOR_OPEN_CMD": True}):
            return False
        if self.door.state != DoorState.OPEN:
            self._fail("No se pudo abrir la puerta para cargar la oblea.")
            return False
        self.wafer_confirmation_requested.emit()
        return True

    def confirm_wafer_loaded(self, confirmed):
        if self._state != RecipeState.WAITING_FOR_WAFER:
            return
        if not confirmed:
            self._finish(False, "Inicio cancelado por el usuario.")
            return
        if not self._set_state(RecipeState.CLOSING_DOOR):
            return
        if not self._perform_action("Cerrar puerta", self.door.close,
                                    outputs={"DOOR_OPEN_CMD": False, "DOOR_CLOSE_CMD": True}):
            return
        if self.door.state != DoorState.CLOSED:
            self._fail("No se pudo confirmar el cierre de la puerta.")
            return
        if not self._set_state(RecipeState.VERIFYING_DOOR_CLOSED):
            return
        self._try_start_vacuum()

    def _try_start_vacuum(self):
        if self._state != RecipeState.VERIFYING_DOOR_CLOSED:
            return
        if (self._digital_state_getter("DOOR_OPEN") is not False
                or self._digital_state_getter("DOOR_CLOSE") is not True):
            return
        if not self._set_state(RecipeState.STARTING_SOFT_VACUUM):
            return
        if not self._perform_action("Activar Soft Vacuum", self.soft_vacuum.start,
                                    outputs={"SOFT_START_CONTROL": True}):
            return
        if self.soft_vacuum.state != SoftVacuumState.RUNNING:
            self._fail("No se pudo iniciar Soft Vacuum.")
            return
        self._vacuum_started = True
        if not self._set_state(RecipeState.STARTING_MAIN_VACUUM):
            return
        if not self._perform_action("Activar Main Vacuum", self.main_vacuum.start,
                                    outputs={"MAIN_VACUUM_CONTROL": True}):
            return
        if self.main_vacuum.state != MainVacuumState.RUNNING:
            self._fail("No se pudo iniciar Main Vacuum.")
            return
        self._set_state(RecipeState.PUMPING_TO_BASE)

    def main_vacuum_started(self):
        if (self.is_active and self._state == RecipeState.STARTING_MAIN_VACUUM
                and self.soft_vacuum.state == SoftVacuumState.RUNNING):
            self._perform_action(
                "Desactivar Soft Vacuum al iniciar Main Vacuum",
                self.soft_vacuum.stop,
                outputs={"SOFT_START_CONTROL": False},
            )

    def update_analog(self, name, value):
        self.cache_analog(name, value)
        if not self.is_active:
            return
        if name in ("BARATRON", "CHAMBER_TEMP") and not self._data_logging_failed:
            reading = self._analog_readings.get(name)
            timestamp = reading[1] if reading is not None else None
            if not self._recipe_data_log.record(name, value, timestamp):
                self._data_logging_failed = True
                self._handle_data_log_failure()
                return
        if name == "BARATRON" and self._state == RecipeState.PUMPING_TO_BASE:
            if value <= self._recipe.base_pressure:
                self._start_gas_flow()
        elif name == "EOP":
            self._eop = value
            if self._state == RecipeState.RUNNING_PLASMA and value < 2.0:
                self._begin_shutdown("Receta finalizada: EOP inferior a 2 V.", failed=False)

    def cache_analog(self, name, value):
        try:
            numeric_value = float(value)
            read_at = datetime.now().astimezone().isoformat(timespec="milliseconds")
            self._analog_readings[name] = (numeric_value, read_at)
        except (TypeError, ValueError):
            self._analog_readings[name] = None

    def analog_error(self, name, message):
        self.cache_analog_error(name)
        if not self.is_active or self._stopping:
            return
        if name == "BARATRON" and self._state in (
            RecipeState.PUMPING_TO_BASE, RecipeState.STARTING_GAS_FLOW,
            RecipeState.CONTROLLING_PRESSURE,
        ):
            self._fail(f"Se perdió la lectura BARATRON: {message}")
        elif name == "CHAMBER_TEMP" and self._state == RecipeState.CONTROLLING_TEMPERATURE:
            self._fail(f"Se perdió la lectura de temperatura: {message}")
        elif name == "EOP" and self._state == RecipeState.RUNNING_PLASMA:
            self._fail(f"Se perdió la lectura EOP: {message}")

    def cache_analog_error(self, name, _message=None):
        self._analog_readings[name] = None

    def digital_value(self, name, active):
        if not self.is_active:
            return
        if self._state == RecipeState.VERIFYING_DOOR_CLOSED_AFTER_RECIPE:
            self._try_finish_after_door_close()
            return
        if self._state == RecipeState.VERIFYING_DOOR_CLOSED:
            self._try_start_vacuum()
            return
        if name in ("DOOR_OPEN", "DOOR_CLOSE") and self._state not in (
            RecipeState.WAITING_FOR_WAFER, RecipeState.CLOSING_DOOR,
            RecipeState.VERIFYING_DOOR_CLOSED,
            RecipeState.WAITING_FOR_WAFER_REMOVAL,
            RecipeState.CLOSING_DOOR_AFTER_RECIPE,
            RecipeState.VERIFYING_DOOR_CLOSED_AFTER_RECIPE,
            RecipeState.STOPPING_PROCESS, RecipeState.VENTING,
        ):
            if (name == "DOOR_OPEN" and active) or (name == "DOOR_CLOSE" and not active):
                self._fail("Se perdio la confirmacion de puerta cerrada durante la receta.")

    def digital_error(self, name, message):
        if not self.is_active:
            return
        if (name in ("DOOR_OPEN", "DOOR_CLOSE") and self._state in (
                RecipeState.WAITING_FOR_WAFER_REMOVAL,
                RecipeState.CLOSING_DOOR_AFTER_RECIPE,
                RecipeState.VERIFYING_DOOR_CLOSED_AFTER_RECIPE,
        )):
            self._finish(True, f"No se pudo confirmar el estado final de la puerta: {name}: {message}")
            return
        if name in ("DOOR_OPEN", "DOOR_CLOSE") and self._state not in (
            RecipeState.WAITING_FOR_WAFER, RecipeState.STOPPING_PROCESS,
        ):
            self._fail(f"No se pudo monitorear {name}: {message}")
        elif name == "ATM_SWITCH" and self._state == RecipeState.VENTING:
            if self._recipe_log is not None and not self._logging_failed:
                self._log_event(f"ERROR DE LECTURA DIGITAL: {name} | {message}")
            self.vent.stop()
            if self.is_active:
                self._finish(True, f"No se pudo monitorear ATM_SWITCH: {message}")

    def pressure_reached(self, _value):
        if self._state != RecipeState.CONTROLLING_PRESSURE:
            return
        if not self._set_state(RecipeState.CONTROLLING_TEMPERATURE):
            return
        if not self._perform_action(
            f"Activar control de temperatura a {self._recipe.process_temperature:g} C",
            lambda: self.temperature.start(self._recipe.process_temperature),
            outputs={"LAMP1_ON_CMD": True, "LAMP2_ON_CMD": True, "LAMP3_ON_CMD": True,
                     "temperatura_objetivo": f"{self._recipe.process_temperature:g} C"},
        ):
            return
        if not self.temperature.is_active:
            self._fail("No se pudo iniciar el control de temperatura.")

    def temperature_reached(self, _value):
        if self._state != RecipeState.CONTROLLING_TEMPERATURE:
            return
        if not self._perform_action("Activar RF/plasma", lambda: self.process.set_plasma(True),
                                    outputs={"RF_ON_CMD": True}):
            return
        if not self.process.plasma_active:
            self._fail("No se pudo encender el plasma.")
            return
        self._eop = None
        self._set_state(RecipeState.RUNNING_PLASMA)

    def stop(self):
        if self.is_active:
            if self._state == RecipeState.WAITING_FOR_WAFER_REMOVAL:
                self._finish(
                    self._failed,
                    self._completion_message + " Receta finalizada por el usuario; la puerta queda abierta.",
                )
                return
            if self._state in (
                RecipeState.CLOSING_DOOR_AFTER_RECIPE,
                RecipeState.VERIFYING_DOOR_CLOSED_AFTER_RECIPE,
            ):
                return
            if self._state == RecipeState.WAITING_FOR_WAFER:
                self._finish(False, "Inicio de receta cancelado.")
                return
            self._begin_shutdown("Receta detenida por el usuario.", failed=False)

    def controller_error(self, *_args):
        if not self.is_active:
            return
        message = str(_args[-1]) if _args else "Error en un controlador de proceso."
        if self._stopping:
            if self._state == RecipeState.VENTING:
                self._finish(True, self._completion_message + " Error durante el venteo: " + message)
            else:
                self._shutdown_errors.append(message)
            return
        self._fail(message)

    def process_state_changed(self, name, enabled):
        if self.is_active:
            signals = {
                "lamps13": {"LAMP1_ON_CMD": enabled, "LAMP3_ON_CMD": enabled},
                "lamp2": {"LAMP2_ON_CMD": enabled},
                "plasma": {"RF_ON_CMD": enabled},
            }
            self._log_event(
                f"Estado de módulo: {name} {'ACTIVADO' if enabled else 'DESACTIVADO'}",
                outputs=signals.get(name),
            )

    def module_state_changed(self, module, state):
        if self.is_active:
            value = state.value if hasattr(state, "value") else state
            self._log_event(f"Estado de módulo: {module}={value}")

    def module_action_confirmed(self, name, value):
        if self.is_active:
            self._log_event(f"Acción confirmada: {name}={value}")

    def interlock_lost(self, message):
        if self.is_active and not self._stopping:
            self._fail(message)

    def vent_completed(self):
        if self._state != RecipeState.VENTING:
            return
        if not self._perform_action("Abrir puerta después del venteo", self.door.open, safety=True,
                                    outputs={"DOOR_CLOSE_CMD": False, "DOOR_OPEN_CMD": True}):
            return
        if not self.is_active:
            return
        if self.door.state != DoorState.OPEN:
            self._finish(True, "Venteo completado. Verifique la apertura de puerta.")
            return
        if not self._set_state(RecipeState.WAITING_FOR_WAFER_REMOVAL):
            return
        self.wafer_removal_confirmation_requested.emit()

    def confirm_wafer_removed(self, confirmed):
        if self._state != RecipeState.WAITING_FOR_WAFER_REMOVAL:
            return
        if not confirmed:
            self._finish(
                self._failed,
                self._completion_message + " El usuario indicó que la oblea no fue retirada; la puerta queda abierta.",
            )
            return
        if not self._set_state(RecipeState.CLOSING_DOOR_AFTER_RECIPE):
            return
        if not self._perform_action(
            "Cerrar puerta después de retirar la oblea",
            self.door.close,
            safety=True,
            outputs={"DOOR_OPEN_CMD": False, "DOOR_CLOSE_CMD": True},
        ):
            return
        if self.door.state != DoorState.CLOSED:
            self._finish(True, "No se pudo ordenar el cierre de la puerta al finalizar la receta.")
            return
        if not self._set_state(RecipeState.VERIFYING_DOOR_CLOSED_AFTER_RECIPE):
            return
        self._try_finish_after_door_close()

    def _try_finish_after_door_close(self):
        if self._state != RecipeState.VERIFYING_DOOR_CLOSED_AFTER_RECIPE:
            return
        if (self._digital_state_getter("DOOR_OPEN") is not False
                or self._digital_state_getter("DOOR_CLOSE") is not True):
            return
        self._finish(self._failed, self._completion_message)

    def _start_gas_flow(self):
        if not self.is_active:
            return
        if not self._set_state(RecipeState.STARTING_GAS_FLOW):
            return
        if not self._perform_action(
            f"Configurar MFC1 O2 a {self._recipe.o2_flow:g} SLPM",
            lambda: self.mfc.set_flow("MFC1", self._recipe.o2_flow),
            outputs={"MFC1_SETPOINT": f"{MFCController.flow_to_voltage('MFC1', self._recipe.o2_flow):.3f} V ({self._recipe.o2_flow:g} SLPM)"},
        ):
            return
        if not self.is_active:
            return
        if not self._perform_action(
            f"Configurar MFC2 N2 a {self._recipe.n2_flow:g} SLPM",
            lambda: self.mfc.set_flow("MFC2", self._recipe.n2_flow),
            outputs={"MFC2_SETPOINT": f"{MFCController.flow_to_voltage('MFC2', self._recipe.n2_flow):.3f} V ({self._recipe.n2_flow:g} SLPM)"},
        ):
            return
        if not self.is_active:
            return
        if not self._perform_action("Abrir válvula MFC1", lambda: self.mfc.set_valve("MFC1", True),
                                    outputs={"MFC1_OPEN": True}):
            return
        if not self.is_active:
            return
        if not self._perform_action("Abrir válvula MFC2", lambda: self.mfc.set_valve("MFC2", True),
                                    outputs={"MFC2_OPEN": True}):
            return
        if not self.is_active:
            return
        if not self._set_state(RecipeState.CONTROLLING_PRESSURE):
            return
        if not self._perform_action(
            f"Activar control de presión a {self._recipe.process_pressure:g} Torr",
            lambda: self.pressure.start(self._recipe.process_pressure),
            outputs={"consigna_presion": f"{self._recipe.process_pressure:g} Torr",
                     "STEPPER_OUTPUT_ENABLE": True, "STEPPER_HALF_STEP": False,
                     "STEPPER_STEP": "pulsos repetitivos omitidos"},
        ):
            return
        if not self.pressure.is_active:
            self._fail("No se pudo iniciar el control de presión.")

    def _fail(self, message):
        if self._recipe_log is not None and not self._logging_failed:
            if not self._log_event(f"ERROR DE RECETA: {message}"):
                return
        self.error_raised.emit(message)
        self._begin_shutdown(message, failed=True)

    def _begin_shutdown(self, message, failed):
        if self._stopping or not self.is_active:
            return
        self._stopping = True
        self._completion_message = message
        self._failed = failed
        self._shutdown_errors = []
        self._set_state(RecipeState.STOPPING_PROCESS)
        errors = []
        for label, action, outputs in (
            ("Desactivar RF/plasma", lambda: self.process.set_plasma(False), {"RF_ON_CMD": False}),
            ("Detener control de temperatura y apagar lámparas", self.temperature.stop,
             {"LAMP1_ON_CMD": False, "LAMP2_ON_CMD": False, "LAMP3_ON_CMD": False}),
            ("Apagar MFC y llevar caudales a cero", self.mfc.shutdown,
             {"MFC1_OPEN": False, "MFC1_SETPOINT": "0 V", "MFC2_OPEN": False, "MFC2_SETPOINT": "0 V"}),
            ("Detener control de presión", lambda: self.pressure.stop(return_to_rest=False),
             {"STEPPER_STEP": False, "STEPPER_OUTPUT_ENABLE": False}),
            ("Confirmar lámparas y RF apagados", self.process.stop_all,
             {"LAMP1_ON_CMD": False, "LAMP2_ON_CMD": False, "LAMP3_ON_CMD": False, "RF_ON_CMD": False}),
        ):
            try:
                self._perform_action(label, action, safety=True, outputs=outputs)
            except Exception as error:
                errors.append(str(error))
        if self.main_vacuum.state == MainVacuumState.RUNNING:
            try:
                self._perform_action("Desactivar Main Vacuum", self.main_vacuum.stop, safety=True,
                                     outputs={"MAIN_VACUUM_CONTROL": False})
            except Exception as error:
                errors.append(str(error))
        if self.soft_vacuum.state == SoftVacuumState.RUNNING:
            try:
                self._perform_action("Desactivar Soft Vacuum", self.soft_vacuum.stop, safety=True,
                                     outputs={"SOFT_START_CONTROL": False})
            except Exception as error:
                errors.append(str(error))
        if (self.main_vacuum.state == MainVacuumState.IDLE
                and self.soft_vacuum.state == SoftVacuumState.IDLE
                and not self._vacuum_started):
            self._finish(self._failed, self._completion_message)
            return
        errors.extend(self._shutdown_errors)
        if errors:
            self._completion_message += " Error durante apagado seguro: " + "; ".join(errors)
            self._failed = True
        if self.main_vacuum.state != MainVacuumState.IDLE or self.soft_vacuum.state != SoftVacuumState.IDLE:
            self._finish(True, self._completion_message + " No se pudo detener el vacío; no se inicia venteo.")
            return
        if not self._set_state(RecipeState.VENTING):
            return
        if not self._perform_action("Iniciar venteo", self.vent.start, safety=True,
                                    outputs={"VENT_VALVE_CONTROL": True}):
            return
        if not self.is_active:
            return
        if self.vent.state != VentState.RUNNING:
            self._finish(True, self._completion_message + " No se pudo iniciar el venteo.")

    def _finish(self, failed, message):
        self._finalizing = True
        final_state = RecipeState.ERROR if failed else RecipeState.COMPLETED
        if self._recipe_log is not None and not self._logging_failed:
            if not self._log_event(
                f"Estado final de receta: {final_state.value} | "
                f"FIN DE RECETA | resultado={'ERROR' if failed else 'OK'} | {message}"
            ):
                failed = True
                message += " No se pudo completar el registro."
        if failed:
            final_state = RecipeState.ERROR
        if self._recipe_log is not None:
            self._recipe_log.close()
            self._log_saved = not self._logging_failed and self._recipe_log.error is None
            if not self._log_saved:
                failed = True
                if str(self._recipe_log.path) not in message:
                    message += f" El registro no pudo guardarse en {self._recipe_log.path}."
                final_state = RecipeState.ERROR
        if self._recipe_data_log is not None:
            self._recipe_data_log.close()
            self._data_log_saved = (
                not self._data_logging_failed and self._recipe_data_log.error is None
            )
            if not self._data_log_saved:
                failed = True
                if str(self._recipe_data_log.path) not in message:
                    message += f" Los datos de proceso no pudieron guardarse en {self._recipe_data_log.path}."
                final_state = RecipeState.ERROR
        self._state = final_state
        self.state_changed.emit(final_state)
        self.finished.emit(not failed, message)
        self._recipe = None
        self._stopping = False
        self._vacuum_started = False
        self._finalizing = False

    def _set_state(self, state):
        if self._recipe_log is not None and not self._logging_failed:
            if not self._log_event(f"Estado de receta: {state.value}"):
                if not self._stopping:
                    return False
        self._state = state
        self.state_changed.emit(state)
        return True

    def _log_event(self, event, outputs=None):
        if self._recipe_log is None or self._logging_failed:
            return False
        if self._recipe_log.record(event, self._analog_readings, outputs=outputs):
            return True
        self._logging_failed = True
        if self._stopping or self._finalizing:
            if self._stopping:
                self._shutdown_errors.append(f"Registro: {self._recipe_log.error}")
                self._failed = True
            return False
        self._handle_log_failure()
        return False

    def _perform_action(self, description, action, safety=False, outputs=None):
        if self._stopping and not safety:
            return False
        was_stopping = self._stopping
        if self._logging_failed:
            if not safety:
                return False
        elif not self._log_event(f"ACCION: {description}", outputs=outputs):
            if not was_stopping or not safety:
                return False
        action()
        return safety or not self._stopping

    def _handle_log_failure(self):
        if self._recipe_log is None:
            return
        self._logging_failed = True
        message = (
            f"No se pudo guardar el registro de receta en {self._recipe_log.path}: "
            f"{self._recipe_log.error or 'error de escritura'}"
        )
        if self.is_active:
            self._begin_shutdown(message, failed=True)
        else:
            self._finish(True, message)

    def _handle_data_log_failure(self):
        if self._recipe_data_log is None:
            return
        self._data_logging_failed = True
        message = (
            f"No se pudieron guardar los datos de presión y temperatura en "
            f"{self._recipe_data_log.path}: {self._recipe_data_log.error or 'error de escritura'}"
        )
        if self.is_active:
            self._begin_shutdown(message, failed=True)
        else:
            self._finish(True, message)
