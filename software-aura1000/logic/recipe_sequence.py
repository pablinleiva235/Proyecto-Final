"""Coordinación del ciclo automático de una receta."""

from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal

from logic.door_sequence import DoorState
from logic.main_vacuum_sequence import MainVacuumState
from logic.soft_vacuum_sequence import SoftVacuumState
from logic.vent_sequence import VentState


class RecipeState(Enum):
    IDLE = "idle"
    WAITING_FOR_WAFER = "waiting_for_wafer"
    CLOSING_DOOR = "closing_door"
    VERIFYING_DOOR_CLOSED = "verifying_door_closed"
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
    error_raised = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(
        self, door_sequence, soft_vacuum_sequence, main_vacuum_sequence,
        vent_sequence, mfc_controller, pressure_controller,
        temperature_controller, process_controller, digital_state_getter=None,
        parent=None,
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
        self._digital_state_getter = digital_state_getter or (lambda _name: True)
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

    def start(self, recipe):
        if self.is_active:
            self.error_raised.emit("Ya hay una receta en ejecución.")
            return False
        self._recipe = recipe
        self._stopping = False
        self._eop = None
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
        self.door.open()
        if self.door.state != DoorState.OPEN:
            self._fail("No se pudo abrir la puerta para cargar la oblea.")
            return False
        self._set_state(RecipeState.WAITING_FOR_WAFER)
        self.wafer_confirmation_requested.emit()
        return True

    def confirm_wafer_loaded(self, confirmed):
        if self._state != RecipeState.WAITING_FOR_WAFER:
            return
        if not confirmed:
            self._finish(False, "Inicio cancelado por el usuario.")
            return
        self._set_state(RecipeState.CLOSING_DOOR)
        self.door.close()
        if self.door.state != DoorState.CLOSED:
            self._fail("No se pudo confirmar el cierre de la puerta.")
            return
        self._set_state(RecipeState.VERIFYING_DOOR_CLOSED)
        self._try_start_vacuum()

    def _try_start_vacuum(self):
        if self._state != RecipeState.VERIFYING_DOOR_CLOSED:
            return
        if (self._digital_state_getter("DOOR_OPEN") is not False
                or self._digital_state_getter("DOOR_CLOSE") is not True):
            return
        self._set_state(RecipeState.STARTING_SOFT_VACUUM)
        self.soft_vacuum.start()
        if self.soft_vacuum.state != SoftVacuumState.RUNNING:
            self._fail("No se pudo iniciar Soft Vacuum.")
            return
        self._vacuum_started = True
        self._set_state(RecipeState.STARTING_MAIN_VACUUM)
        self.main_vacuum.start()
        if self.main_vacuum.state != MainVacuumState.RUNNING:
            self._fail("No se pudo iniciar Main Vacuum.")
            return
        self._set_state(RecipeState.PUMPING_TO_BASE)

    def update_analog(self, name, value):
        if not self.is_active:
            return
        if name == "BARATRON" and self._state == RecipeState.PUMPING_TO_BASE:
            if value <= self._recipe.base_pressure:
                self._start_gas_flow()
        elif name == "EOP":
            self._eop = value
            if self._state == RecipeState.RUNNING_PLASMA and value < 2.0:
                self._begin_shutdown("Receta finalizada: EOP inferior a 2 V.", failed=False)

    def analog_error(self, name, message):
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

    def digital_value(self, name, active):
        if not self.is_active:
            return
        if self._state == RecipeState.VERIFYING_DOOR_CLOSED:
            self._try_start_vacuum()
            return
        if name in ("DOOR_OPEN", "DOOR_CLOSE") and self._state not in (
            RecipeState.WAITING_FOR_WAFER, RecipeState.CLOSING_DOOR,
            RecipeState.VERIFYING_DOOR_CLOSED,
            RecipeState.STOPPING_PROCESS, RecipeState.VENTING,
        ):
            if (name == "DOOR_OPEN" and active) or (name == "DOOR_CLOSE" and not active):
                self._fail("Se perdio la confirmacion de puerta cerrada durante la receta.")

    def digital_error(self, name, message):
        if not self.is_active:
            return
        if name in ("DOOR_OPEN", "DOOR_CLOSE") and self._state not in (
            RecipeState.WAITING_FOR_WAFER, RecipeState.STOPPING_PROCESS,
        ):
            self._fail(f"No se pudo monitorear {name}: {message}")
        elif name == "ATM_SWITCH" and self._state == RecipeState.VENTING:
            self.vent.stop()
            if self.is_active:
                self._finish(True, f"No se pudo monitorear ATM_SWITCH: {message}")

    def pressure_reached(self, _value):
        if self._state != RecipeState.CONTROLLING_PRESSURE:
            return
        self._set_state(RecipeState.CONTROLLING_TEMPERATURE)
        self.temperature.start(self._recipe.process_temperature)
        if not self.temperature.is_active:
            self._fail("No se pudo iniciar el control de temperatura.")

    def temperature_reached(self, _value):
        if self._state != RecipeState.CONTROLLING_TEMPERATURE:
            return
        self.process.set_plasma(True)
        if not self.process.plasma_active:
            self._fail("No se pudo encender el plasma.")
            return
        self._eop = None
        self._set_state(RecipeState.RUNNING_PLASMA)

    def stop(self):
        if self.is_active:
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

    def interlock_lost(self, message):
        if self.is_active and not self._stopping:
            self._fail(message)

    def vent_completed(self):
        if self._state != RecipeState.VENTING:
            return
        self.door.open()
        if not self.is_active:
            return
        if self.door.state != DoorState.OPEN:
            self._finish(True, "Venteo completado. Verifique la apertura de puerta.")
            return
        self._finish(self._failed, self._completion_message)

    def _start_gas_flow(self):
        if not self.is_active:
            return
        self._set_state(RecipeState.STARTING_GAS_FLOW)
        self.mfc.set_flow("MFC1", self._recipe.o2_flow)
        if not self.is_active:
            return
        self.mfc.set_flow("MFC2", self._recipe.n2_flow)
        if not self.is_active:
            return
        self.mfc.set_valve("MFC1", True)
        if not self.is_active:
            return
        self.mfc.set_valve("MFC2", True)
        if not self.is_active:
            return
        self._set_state(RecipeState.CONTROLLING_PRESSURE)
        self.pressure.start(self._recipe.process_pressure)
        if not self.pressure.is_active:
            self._fail("No se pudo iniciar el control de presión.")

    def _fail(self, message):
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
        for action in (
            lambda: self.process.set_plasma(False),
            self.temperature.stop,
            self.mfc.shutdown,
            self.pressure.stop,
            self.process.stop_all,
        ):
            try:
                action()
            except Exception as error:
                errors.append(str(error))
        if self.main_vacuum.state == MainVacuumState.RUNNING:
            try:
                self.main_vacuum.stop()
            except Exception as error:
                errors.append(str(error))
        if self.soft_vacuum.state == SoftVacuumState.RUNNING:
            try:
                self.soft_vacuum.stop()
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
        self._set_state(RecipeState.VENTING)
        self.vent.start()
        if not self.is_active:
            return
        if self.vent.state != VentState.RUNNING:
            self._finish(True, self._completion_message + " No se pudo iniciar el venteo.")

    def _finish(self, failed, message):
        self._set_state(RecipeState.ERROR if failed else RecipeState.COMPLETED)
        self.finished.emit(not failed, message)
        self._recipe = None
        self._stopping = False
        self._vacuum_started = False

    def _set_state(self, state):
        self._state = state
        self.state_changed.emit(state)
