from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
    QDialog,
)
from PyQt5.QtCore import pyqtSignal

from config_gui.strings import (APP_TITLE,EXIT_CONFIRMATION_TITLE,EXIT_CONFIRMATION_MESSAGE)
from config_gui.constants import (WELCOME_SCREEN,MAINTAINER_SCREEN,STATISTICS_SCREEN,NORMAL_OPERATION_SCREEN)
from config_gui.maintainer_signals import (MAINTAINER_SIGNALS,MAINTAINER_OUTPUT_SIGNALS)

from controllers.navigation_controller import NavigationController
from controllers.signal_controller import SignalController
from controllers.interlock_controller import InterlockController
from controllers.analog_signal_controller import AnalogSignalController
from controllers.mfc_controller import MFCController
from controllers.throttle_controller import ThrottleController
from controllers.pressure_controller import PressureController
from controllers.process_controller import ProcessController
from controllers.temperature_controller import TemperatureController
from PyQt5.QtCore import QTimer
from logic.door_sequence import DoorState

from gui.widgets.top_bar_widget import TopBarWidget
from gui.welcome_screen import WelcomeScreen
from gui.maintainer_screen import MaintainerScreen
from gui.statistics_screen import StatisticsScreen
from gui.normal_operation_screen import NormalOperationScreen
from gui.login_dialog import LoginDialog
from gui.settings_dialog import SettingsDialog
from gui.widgets.localization import translate_widget_tree
import config_gui.strings as strings

from logic.door_sequence import DoorSequence
from logic.soft_vacuum_sequence import (SoftVacuumSequence, SoftVacuumState)
from logic.main_vacuum_sequence import (MainVacuumSequence, MainVacuumState)
from logic.vent_sequence import (VentSequence, VentState)
from logic.recipe_sequence import RecipeSequence, RecipeState

# gui-developement
class MainWindow(QMainWindow):

    exit_requested = pyqtSignal()

    def __init__(
        self,
        hardware,
        door_sequence,
        soft_vacuum_sequence,
        main_vacuum_sequence,
        vent_sequence,
        settings_manager=None,
    ):
        super().__init__()

        self.hardware = hardware

        self.door_sequence = door_sequence
        self.soft_vacuum_sequence = soft_vacuum_sequence
        self.main_vacuum_sequence = main_vacuum_sequence
        self.vent_sequence = vent_sequence
        self.settings_manager = settings_manager


        self.create_widgets()
        self.setup_layout()
        self.connect_signals()
        self.update_texts()

        self._show_welcome_screen()


    def create_widgets(self):
        # Configura la ventana principal
        self.setWindowTitle(APP_TITLE)

        # Componentes principales de la aplicación
        self.central_widget = QWidget()
        self.top_bar = TopBarWidget()
        self.stack = QStackedWidget()

        # Pantallas
        self.welcome_screen = WelcomeScreen()
        self.maintainer_screen = MaintainerScreen()
        self.statistics_screen = StatisticsScreen()
        self.normal_operation_screen = NormalOperationScreen()

        # Controlador de navegación
        self.navigation_controller = NavigationController(self.stack)

        # Registra las pantallas con nombres lógicos
        self.navigation_controller.register_screen(
            WELCOME_SCREEN,
            self.welcome_screen,
        )
        self.navigation_controller.register_screen(
            MAINTAINER_SCREEN,
            self.maintainer_screen,
        )
        self.navigation_controller.register_screen(
            STATISTICS_SCREEN,
            self.statistics_screen,
        )
        self.navigation_controller.register_screen(
            NORMAL_OPERATION_SCREEN,
            self.normal_operation_screen,
        )

        # Inicializa la interfaz real con el hardware del Plasma Asher.
        # Controlador encargado del monitoreo y control de señales digitales.
        self.signal_controller = SignalController(
            hardware=self.hardware,
            monitored_signals=MAINTAINER_SIGNALS,
            output_signals=MAINTAINER_OUTPUT_SIGNALS,
            poll_interval_ms=100,
            can_toggle=self._can_toggle_manual_output,
        )

        # Controlador de interlocks - Determina el uso seguro de las secuencias según el estado del equipo
        self.interlock_controller = InterlockController(
            door_sequence=self.door_sequence,
            soft_vacuum_sequence=self.soft_vacuum_sequence,
            main_vacuum_sequence=self.main_vacuum_sequence,
            vent_sequence=self.vent_sequence,
        )

        self.analog_controller = AnalogSignalController(
            hardware=self.hardware,
            monitored_signals=(
                "BARATRON", "CHAMBER_TEMP", "MFC1_FLOW", "MFC2_FLOW",
                "MFC3_FLOW", "MFC4_FLOW", "EOP",
            ),
            poll_interval_ms=250,
            parent=self,
        )
        self.mfc_controller = MFCController(
            hardware=self.hardware,
            can_operate=self._can_control_process_modules,
            parent=self,
        )
        self.throttle_controller = ThrottleController(
            hardware=self.hardware,
            can_operate=self._can_control_process_modules,
            parent=self,
        )
        self.pressure_controller = PressureController(
            throttle_controller=self.throttle_controller,
            can_operate=self._can_control_process_modules,
            parent=self,
        )
        self.process_controller = ProcessController(
            hardware=self.hardware,
            can_operate=self._can_control_process_modules,
            parent=self,
        )
        self.temperature_controller = TemperatureController(
            process_controller=self.process_controller,
            can_operate=self._can_control_process_modules,
            parent=self,
        )
        self.recipe_sequence = RecipeSequence(
            door_sequence=self.door_sequence,
            soft_vacuum_sequence=self.soft_vacuum_sequence,
            main_vacuum_sequence=self.main_vacuum_sequence,
            vent_sequence=self.vent_sequence,
            mfc_controller=self.mfc_controller,
            pressure_controller=self.pressure_controller,
            temperature_controller=self.temperature_controller,
            process_controller=self.process_controller,
            digital_state_getter=self.signal_controller.get_last_state,
            parent=self,
        )
        self.module_monitor_timer = QTimer(self)
        self.module_monitor_timer.setInterval(100)
        self.module_monitor_timer.timeout.connect(self._monitor_migrated_modules)
        self._module_access = False

        self.door_sequence.set_can_open(
            self.interlock_controller.can_open_door
        )
        self.soft_vacuum_sequence.set_can_start(
            self.interlock_controller.can_start_soft_vacuum
        )
        self.main_vacuum_sequence.set_can_start(
            self.interlock_controller.can_start_main_vacuum
        )
        self.main_vacuum_sequence.set_can_stop(
            self.interlock_controller.can_stop_main_vacuum
        )
        self.vent_sequence.set_can_start(
            self.interlock_controller.can_start_vent
        )
        
    def setup_layout(self):
        # Organiza la barra superior y el contenido principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.top_bar)
        main_layout.addWidget(self.stack)

        self.central_widget.setLayout(main_layout)
        self.setCentralWidget(self.central_widget)

    def connect_signals(self):
        # Solicita autenticación para ingresar al modo Maintainer
        self.welcome_screen.maintainer_requested.connect(
            self._request_maintainer_access
        )

        self.welcome_screen.statistics_requested.connect(
            self._show_statistics_screen
        )
        self.welcome_screen.normal_operation_requested.connect(
            self._show_normal_operation_screen
        )

        # Navegación hacia la pantalla de bienvenida
        self.maintainer_screen.back_requested.connect(
            self._show_welcome_screen
        )
        self.statistics_screen.back_requested.connect(
            self._show_welcome_screen
        )
        self.normal_operation_screen.back_requested.connect(
            self._show_welcome_screen
        )
        self.normal_operation_screen.start_recipe_requested.connect(self._start_recipe)
        self.normal_operation_screen.stop_recipe_requested.connect(self.recipe_sequence.stop)
        self.recipe_sequence.state_changed.connect(self._handle_recipe_state)
        self.recipe_sequence.wafer_confirmation_requested.connect(self._confirm_recipe_wafer)
        self.recipe_sequence.error_raised.connect(self._handle_recipe_error)
        self.recipe_sequence.finished.connect(self._handle_recipe_finished)

        # Solicitud global de salida
        self.top_bar.exit_requested.connect(
            self.exit_requested.emit
        )
        self.top_bar.settings_requested.connect(self._open_settings_dialog)
        if self.settings_manager is not None:
            self.settings_manager.language_changed.connect(self.update_texts)


        # ===================================================================================
        # Conexión con SignalController - (control de señales digitales en mantainer_screen)
        # ===================================================================================
        # Solicitudes de cambio desde MaintainerScreen hacia SignalController.
        self.maintainer_screen.output_toggle_requested.connect(
            self.signal_controller.request_toggle
        )
        # Informa visualmente que una salida está siendo procesada.
        self.signal_controller.signal_processing.connect(
            self.maintainer_screen.set_signal_processing
        )
        # Actualiza el estado visual confirmado.
        self.signal_controller.signal_state_changed.connect(
            self.maintainer_screen.set_signal_active
        )
        # Informa a las secuencias sobre cambios
        # relevantes en las entradas digitales.
        self.signal_controller.signal_state_changed.connect(
            self._handle_digital_signal_changed
        )
        self.signal_controller.signal_state_changed.connect(
            self.recipe_sequence.digital_value
        )
        self.signal_controller.signal_sampled.connect(
            self._handle_digital_signal_sampled
        )
        # Manejo temporal de errores.
        self.signal_controller.signal_error.connect(
            self._handle_signal_error
        )
        self.signal_controller.signal_error.connect(
            self.recipe_sequence.digital_error
        )

        # ====================
        # Sequencias definidas
        # ====================
    # Puerta
        self.maintainer_screen.door_sequence_requested.connect(
           self.door_sequence.toggle
        )
        self.door_sequence.state_changed.connect(
            self._handle_door_state_changed
        )
        self.door_sequence.sequence_error.connect(
            self._handle_door_sequence_error
        )
        self.door_sequence.sequence_error.connect(self.recipe_sequence.controller_error)
    # Soft Vacuum
        self.maintainer_screen.soft_vacuum_sequence_requested.connect(
            self.soft_vacuum_sequence.toggle
        )
        self.soft_vacuum_sequence.state_changed.connect(
            self._handle_soft_vacuum_state_changed
        )
        self.soft_vacuum_sequence.sequence_error.connect(
            self._handle_soft_vacuum_sequence_error
        )
        self.soft_vacuum_sequence.sequence_error.connect(self.recipe_sequence.controller_error)
    # Main Vacuum
        self.maintainer_screen.main_vacuum_sequence_requested.connect(
            self.main_vacuum_sequence.toggle
        )
        self.main_vacuum_sequence.state_changed.connect(
            self._handle_main_vacuum_state_changed
        )
        self.main_vacuum_sequence.sequence_error.connect(
            self._handle_main_vacuum_sequence_error
        )
        self.main_vacuum_sequence.sequence_error.connect(self.recipe_sequence.controller_error)
    # Vent sequence
        self.maintainer_screen.vent_chamber_sequence_requested.connect(
            self.vent_sequence.toggle
        )
        self.vent_sequence.state_changed.connect(
            self._handle_vent_state_changed
        )
        self.door_sequence.state_changed.connect(
            lambda state: self.recipe_sequence.module_state_changed("Puerta", state)
        )
        self.soft_vacuum_sequence.state_changed.connect(
            lambda state: self.recipe_sequence.module_state_changed("Soft Vacuum", state)
        )
        self.main_vacuum_sequence.state_changed.connect(
            lambda state: self.recipe_sequence.module_state_changed("Main Vacuum", state)
        )
        self.vent_sequence.state_changed.connect(
            lambda state: self.recipe_sequence.module_state_changed("Venteo", state)
        )
        self.vent_sequence.vent_completed.connect(
            self._handle_vent_completed
        )
        self.vent_sequence.vent_completed.connect(self.recipe_sequence.vent_completed)
        self.vent_sequence.sequence_error.connect(
            self._handle_vent_sequence_error
        )
        self.vent_sequence.sequence_error.connect(self.recipe_sequence.controller_error)

        # Lecturas analógicas de mantenimiento.
        self.analog_controller.signal_value_changed.connect(
            self.maintainer_screen.set_analog_value
        )
        self.analog_controller.signal_value_changed.connect(
            self.normal_operation_screen.set_analog_value
        )
        self.analog_controller.signal_value_changed.connect(
            self.recipe_sequence.cache_analog
        )
        self.analog_controller.signal_value_changed.connect(
            self._handle_analog_value
        )
        self.analog_controller.signal_value_changed.connect(
            self.recipe_sequence.update_analog
        )
        self.analog_controller.signal_error.connect(
            self.maintainer_screen.set_analog_error
        )
        self.analog_controller.signal_error.connect(
            self.normal_operation_screen.set_analog_error
        )
        self.analog_controller.signal_error.connect(
            self.recipe_sequence.cache_analog_error
        )
        self.analog_controller.signal_error.connect(
            self._handle_analog_error
        )
        self.analog_controller.signal_error.connect(
            self.recipe_sequence.analog_error
        )

        # Controles de MFC, throttle, lámparas y plasma.
        self.maintainer_screen.mfc_flow_requested.connect(self.mfc_controller.set_flow)
        self.maintainer_screen.mfc_valve_requested.connect(self.mfc_controller.set_valve)
        self.mfc_controller.flow_applied.connect(self.maintainer_screen.set_mfc_flow)
        self.mfc_controller.valve_state_changed.connect(self.maintainer_screen.set_mfc_valve_state)
        self.mfc_controller.flow_applied.connect(
            lambda name, value: self.recipe_sequence.module_action_confirmed(
                f"{name} flow", f"{value:g} SLPM"
            )
        )
        self.mfc_controller.valve_state_changed.connect(
            lambda name, opened: self.recipe_sequence.module_action_confirmed(
                f"{name} valve", "open" if opened else "closed"
            )
        )
        self.mfc_controller.operation_error.connect(self._handle_module_error)
        self.mfc_controller.operation_error.connect(self.recipe_sequence.controller_error)
        self.maintainer_screen.throttle_move_requested.connect(self.throttle_controller.start)
        self.maintainer_screen.throttle_stop_requested.connect(self.throttle_controller.stop)
        self.throttle_controller.movement_changed.connect(self.maintainer_screen.set_throttle_moving)
        self.throttle_controller.movement_changed.connect(
            lambda moving, direction: self.recipe_sequence.module_action_confirmed(
                "Throttle", direction if moving else "stopped"
            )
        )
        self.throttle_controller.operation_error.connect(self._handle_throttle_error)
        self.throttle_controller.operation_error.connect(self.recipe_sequence.controller_error)
        self.maintainer_screen.pressure_start_requested.connect(
            self.pressure_controller.start
        )
        self.maintainer_screen.pressure_stop_requested.connect(
            self.pressure_controller.stop
        )
        self.pressure_controller.pressure_changed.connect(
            self.maintainer_screen.set_pressure_reading
        )
        self.pressure_controller.pressure_unavailable.connect(
            self.maintainer_screen.set_pressure_reading_unavailable
        )
        self.pressure_controller.state_changed.connect(
            self.maintainer_screen.set_pressure_control_state
        )
        self.pressure_controller.state_changed.connect(
            lambda state: self.recipe_sequence.module_state_changed("Control de presión", state)
        )
        self.pressure_controller.operation_error.connect(
            self._handle_pressure_error
        )
        self.pressure_controller.operation_error.connect(self.recipe_sequence.controller_error)
        self.pressure_controller.setpoint_reached.connect(self.recipe_sequence.pressure_reached)
        self.maintainer_screen.temperature_start_requested.connect(
            self.temperature_controller.start
        )
        self.maintainer_screen.temperature_stop_requested.connect(
            self.temperature_controller.stop
        )
        self.temperature_controller.temperature_changed.connect(
            self.maintainer_screen.set_temperature_reading
        )
        self.temperature_controller.temperature_unavailable.connect(
            self.maintainer_screen.set_temperature_reading_unavailable
        )
        self.temperature_controller.state_changed.connect(
            self.maintainer_screen.set_temperature_control_state
        )
        self.temperature_controller.state_changed.connect(
            lambda state: self.recipe_sequence.module_state_changed("Control de temperatura", state)
        )
        self.temperature_controller.operation_error.connect(
            self._handle_temperature_error
        )
        self.temperature_controller.operation_error.connect(self.recipe_sequence.controller_error)
        self.temperature_controller.setpoint_reached.connect(self.recipe_sequence.temperature_reached)
        self.maintainer_screen.lamps13_requested.connect(self.process_controller.start_lamps13)
        self.maintainer_screen.lamp2_requested.connect(self.process_controller.set_lamp2)
        self.maintainer_screen.plasma_requested.connect(self.process_controller.set_plasma)
        self.process_controller.state_changed.connect(self.maintainer_screen.set_process_state)
        self.process_controller.state_changed.connect(self.recipe_sequence.process_state_changed)
        self.process_controller.operation_error.connect(self._handle_module_error)
        self.process_controller.operation_error.connect(self.recipe_sequence.controller_error)
        self.process_controller.alarm_raised.connect(self._handle_process_alarm)
        self.process_controller.alarm_raised.connect(self.recipe_sequence.interlock_lost)
        self.process_controller.warning_raised.connect(self._handle_process_warning)
        self.module_monitor_timer.start()
        self.maintainer_screen.set_module_controls_enabled(False)

        # =========================================================
        # Estado inicial de las secuencias
        # =========================================================
        self.maintainer_screen.set_door_state( self.door_sequence.state )
        self.maintainer_screen.set_soft_vacuum_state( self.soft_vacuum_sequence.state )
        self.maintainer_screen.set_main_vacuum_state(self.main_vacuum_sequence.state )
        self.maintainer_screen.set_vent_state(self.vent_sequence.state )
        self._update_sequence_permissions()

    def _open_settings_dialog(self):
        if self.settings_manager is None:
            return
        dialog = SettingsDialog(self.settings_manager, self)
        dialog.exec_()

    def update_texts(self, *_):
        translate_widget_tree(self)
        self.setWindowTitle(strings.tr(APP_TITLE))



    def _show_welcome_screen(self):
        if self.recipe_sequence.is_active:
            return
    # Muestra la pantalla de bienvenida
        if not self.pressure_controller.is_active and not self.temperature_controller.is_active:
            self.signal_controller.stop_monitoring()
            self.analog_controller.stop_monitoring()
        self.navigation_controller.show_screen(
            WELCOME_SCREEN
        )

    def _show_maintainer_screen(self):
        if self.recipe_sequence.is_active:
            return
    # Muestra la pantalla de mantenimiento e inicia el monitoreo de señales
        self.navigation_controller.show_screen(
            MAINTAINER_SCREEN
        )
        self.signal_controller.start_monitoring()
        self.analog_controller.start_monitoring()
        self._sync_module_permissions()

    def _show_statistics_screen(self):
        if self.recipe_sequence.is_active:
            return
    # Muestra la pantalla de estadísticas
        self.navigation_controller.show_screen(
            STATISTICS_SCREEN
        )
        self.statistics_screen.refresh_data()
        if not self.pressure_controller.is_active and not self.temperature_controller.is_active:
            self.analog_controller.stop_monitoring()

    def _show_normal_operation_screen(self):
        """Muestra operación normal e inicia el monitoreo analógico."""
        self.navigation_controller.show_screen(
            NORMAL_OPERATION_SCREEN
        )
        self.signal_controller.start_monitoring()
        self.analog_controller.start_monitoring()

    def _start_recipe(self, recipe):
        self.signal_controller.start_monitoring()
        self.analog_controller.start_monitoring()
        self.signal_controller.refresh_signals()
        self.recipe_sequence.start(recipe)

    def _confirm_recipe_wafer(self):
        self.recipe_sequence.confirm_wafer_loaded(
            self.normal_operation_screen.confirm_wafer_loaded()
        )

    def _handle_recipe_state(self, state):
        label = strings.RECIPE_STATE_LABELS.get(state.value, state.value)
        self.normal_operation_screen.set_recipe_status(label)
        running = self.recipe_sequence.is_active
        can_stop = state not in (RecipeState.STOPPING_PROCESS, RecipeState.VENTING)
        self.normal_operation_screen.set_recipe_running(running, can_stop=can_stop)
        self.maintainer_screen.set_manual_controls_locked(running)

    def _handle_recipe_error(self, message):
        self.normal_operation_screen.set_recipe_status(message)
        QMessageBox.warning(
            self, strings.tr(strings.RECIPE_INVALID_TITLE), strings.tr(message)
        )

    def _handle_recipe_finished(self, success, message):
        self.normal_operation_screen.set_recipe_status(
            strings.RECIPE_STATE_LABELS["completed" if success else "error"]
        )
        self.normal_operation_screen.set_recipe_running(False)
        self.maintainer_screen.set_manual_controls_locked(False)
        self._sync_module_permissions()
        if self.recipe_sequence.log_saved:
            message += "\n\n" + strings.tr(strings.RECIPE_LOG_SAVED_MESSAGE).format(
                path=self.recipe_sequence.log_path
            )
        else:
            message += "\n\n" + strings.tr(strings.RECIPE_LOG_FAILED_MESSAGE).format(
                path=self.recipe_sequence.log_path
            )
        if self.recipe_sequence.data_log_saved:
            message += "\n\n" + strings.tr(strings.RECIPE_DATA_SAVED_MESSAGE).format(
                path=self.recipe_sequence.data_log_path
            )
        else:
            message += "\n\n" + strings.tr(strings.RECIPE_DATA_FAILED_MESSAGE).format(
                path=self.recipe_sequence.data_log_path
            )
        all_logs_saved = self.recipe_sequence.log_saved and self.recipe_sequence.data_log_saved
        dialog = QMessageBox.information if success and all_logs_saved else QMessageBox.warning
        dialog(self, strings.tr(strings.START_RECIPE_BUTTON), strings.tr(message))

    def start_recipe_pressure_control(self, recipe):
        """Punto de entrada para la etapa de presión del coordinador de recetas."""
        self.pressure_controller.start(recipe.process_pressure)

    def stop_recipe_pressure_control(self):
        """Detiene el lazo si la secuencia de receta aborta o cambia de etapa."""
        self.pressure_controller.stop()

    def _request_maintainer_access(self):
        if self.recipe_sequence.is_active:
            return
    # Solicita autenticación antes de ingresar al modo de mantenimiento
        login_dialog = LoginDialog(self)
        login_dialog.update_texts()

        result = login_dialog.exec_()

        if result == QDialog.Accepted:
            self._show_maintainer_screen()

    def _handle_signal_error(
        self,
        signal_name: str,
        message: str,
    ) -> None:
        """Muestra el error en la señal y lo registra en consola."""

        self.maintainer_screen.set_signal_error(signal_name, message)

        print(
            f"[SignalController] ERROR {signal_name}: {message}"
        )

    def _can_toggle_manual_output(self, signal_name, requested_state):
        """Aplica los permisos existentes a las salidas manuales asociadas."""
        if self.recipe_sequence.is_active:
            raise RuntimeError("Los controles manuales estÃ¡n bloqueados durante una receta.")
        if (
            signal_name in ("MFC3_OPEN", "MFC4_OPEN")
            and requested_state
            and not self._can_control_process_modules()
        ):
            raise RuntimeError(strings.tr(strings.MFC_VALVE_INTERLOCK_ERROR))
        return True

    def _handle_digital_signal_changed(
        self,
        signal_name,
        active,
    ):
        if signal_name in ("DOOR_OPEN", "DOOR_CLOSE"):
            self._sync_module_permissions()

    def _handle_digital_signal_sampled(self, signal_name, active):
        if signal_name == "ATM_SWITCH":
            self.vent_sequence.update_atmospheric_state(active)
    """
    def _confirm_exit(self):
    # Confirma con el usuario antes de cerrar la aplicación
        response = QMessageBox.question(
        self,
        strings.tr(EXIT_CONFIRMATION_TITLE),
        strings.tr(EXIT_CONFIRMATION_MESSAGE),
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
        )
        print(
            "[topBar] "
            "Cierre del programa."
        )
        if response == QMessageBox.No:
            print(
                "[topBar] "
                "Cancelado"
            )
            return
        self.shutdown_controller.start()
    """
    def _update_sequence_permissions(self):
        """
        Actualiza visualmente los permisos de las
        secuencias según los interlocks actuales.
        """
        permissions = (
            self.interlock_controller.get_permissions()
        )

        for sequence_name, enabled in permissions.items():
            self.maintainer_screen.set_sequence_enabled(
                sequence_name,
                enabled,
            )


    # ============================================================
    # Secuencias funcionales - Manejo de eventos
    # ============================================================
# Puerta
    def _handle_door_state_changed(
        self,
        state,
    ):
        print(
            f"[DoorSequence] Estado: {state.value}"
        )
        self.maintainer_screen.set_door_state(
            state
        )
        self._sync_module_permissions()
        self._update_sequence_permissions()

    def _handle_door_sequence_error(self, message):
        print(
            f"[DoorSequence] ERROR: {message}"
        )

# Soft Vacumm
    def _handle_soft_vacuum_state_changed(self,state):
        print(
            "[SoftVacuumSequence] "
            f"Estado: {state.value}"
        )
        self.maintainer_screen.set_soft_vacuum_state(state)
        if state == SoftVacuumState.RUNNING:
            self.interlock_controller.vacuum_started()
        self._update_sequence_permissions()

    def _handle_soft_vacuum_sequence_error(self,message):
        print(
            "[SoftVacuumSequence] "
            f"ERROR: {message}"
        )

# Main Vacuum
    def _handle_main_vacuum_state_changed(self,state):
        print(
            "[MainVacuumSequence] "
            f"Estado: {state.value}"
        )
        self.maintainer_screen.set_main_vacuum_state(state)
        self._sync_module_permissions()
        if state == MainVacuumState.RUNNING:
            self.interlock_controller.vacuum_started()
            self._handle_main_vacuum_started()
        self._update_sequence_permissions()

    def _handle_main_vacuum_started(self):
        #Coordina las acciones necesarias después del arranque de Main Vacuum.
        if (self.soft_vacuum_sequence.state == SoftVacuumState.RUNNING):
            if self.recipe_sequence.is_active:
                self.recipe_sequence.main_vacuum_started()
            else:
                self.soft_vacuum_sequence.stop()

    def _handle_main_vacuum_sequence_error(self,message):
        print(
            "[MainVacuumSequence] "
            f"ERROR: {message}"
        )

    def _handle_vent_state_changed(self,state):
        print(
            "[VentSequence] "
            f"Estado: {state.value}"
        )
        self.maintainer_screen.set_vent_state(state)
        self._sync_module_permissions()
        self._update_sequence_permissions()

#Venteo
    def _handle_vent_completed(self):
        print(
            "[VentSequence] Venteo completado."
        )
        self.interlock_controller.vent_completed()
        self._update_sequence_permissions()

    def _handle_vent_sequence_error(self,message):
        print(
            "[VentSequence] "
            f"ERROR: {message}"
        )

    def _can_control_process_modules(self):
        door_is_closed = (
            self.door_sequence.state == DoorState.CLOSED
            and self.signal_controller.get_last_state("DOOR_CLOSE") is True
            and self.signal_controller.get_last_state("DOOR_OPEN") is False
        )
        return (
            self.main_vacuum_sequence.state == MainVacuumState.RUNNING
            and door_is_closed
            and self.vent_sequence.state == VentState.IDLE
        )

    def _sync_module_permissions(self):
        allowed = self._can_control_process_modules()
        self.maintainer_screen.set_module_controls_enabled(allowed)
        if allowed == self._module_access:
            return
        self._module_access = allowed
        if not allowed:
            if self.recipe_sequence.state in (
                RecipeState.STOPPING_PROCESS,
                RecipeState.VENTING,
            ):
                return
            if self.pressure_controller.is_active:
                self.pressure_controller.abort(
                    "Se perdió el vacío principal, la confirmación de puerta cerrada o el interlock de venteo."
                )
            if self.temperature_controller.is_active:
                self.temperature_controller.abort(
                    "Se perdió el vacío principal, la confirmación de puerta cerrada o el interlock de venteo."
                )
            self.throttle_controller.stop()
            self.mfc_controller.shutdown()
            try:
                self.process_controller.stop_all()
            except Exception as error:
                self._handle_module_error("Apagado seguro", str(error))

    def _monitor_migrated_modules(self):
        self.throttle_controller.stop_if_limit_reached()
        self.process_controller.check_faults()

    def _handle_module_error(self, module_name, message):
        if module_name in ("lamp2", "plasma"):
            self.maintainer_screen.set_process_state(module_name, False)
        self.maintainer_screen.set_operation_message(
            f"{module_name}: {message}", is_error=True
        )

    def _handle_throttle_error(self, message):
        self.maintainer_screen.set_throttle_moving(False, "detenido")
        self._handle_module_error("Throttle", message)

    def _handle_analog_value(self, signal_name, value):
        if signal_name == "BARATRON":
            self.pressure_controller.set_pressure_reading(value)
        elif signal_name == "CHAMBER_TEMP":
            self.temperature_controller.set_temperature_reading(value)

    def _handle_analog_error(self, signal_name, message):
        if signal_name == "BARATRON":
            self.pressure_controller.invalidate_pressure(message)
            self.maintainer_screen.set_pressure_reading_unavailable(message)
        elif signal_name == "CHAMBER_TEMP":
            self.temperature_controller.invalidate_temperature(message)

    def _handle_pressure_error(self, message):
        self.maintainer_screen.set_pressure_control_error(message)
        self._handle_module_error("Presión", message)

    def _handle_temperature_error(self, message):
        self.maintainer_screen.set_temperature_control_error(message)
        self._handle_module_error("Temperatura", message)

    def _handle_process_alarm(self, message):
        if self.temperature_controller.is_active:
            self.temperature_controller.abort("Se abortó el control térmico por una alarma de proceso.")
        QMessageBox.warning(
            self,
            strings.tr("Alarma de seguridad"),
            strings.tr("Se detuvieron lámparas y plasma por una falla:\n\n" + message),
            QMessageBox.Ok,
        )

    def _handle_process_warning(self, message):
        QMessageBox.warning(
            self,
            strings.tr("Advertencia del magnetrón"),
            strings.tr(message),
            QMessageBox.Ok,
        )

