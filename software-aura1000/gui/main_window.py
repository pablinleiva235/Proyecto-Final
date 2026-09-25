
#from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
    QDialog,
)
from PyQt5.QtCore import Qt
#from gui.pyqt_gui import Ui_MainWindow
#from services.system_state import systemState
#from logic.timers_io import timersIOManager

#import logic.pre_encendido as preEncendido
#import logic.maintenance_process as maintenanceProcess
#from logic.throttle_test import ThrottleController
from config.digital_signals import ACTIVE, INACTIVE

from config_gui.strings import (APP_TITLE,EXIT_CONFIRMATION_TITLE,EXIT_CONFIRMATION_MESSAGE)
from config_gui.constants import (WELCOME_SCREEN,MAINTAINER_SCREEN,STATISTICS_SCREEN)
from config_gui.maintainer_signals import (MAINTAINER_SIGNALS,MAINTAINER_OUTPUT_SIGNALS)

from controllers.navigation_controller import NavigationController
from controllers.signal_controller import SignalController
from controllers.interlock_controller import InterlockController

from gui.widgets.top_bar_widget import TopBarWidget
from gui.welcome_screen import WelcomeScreen
from gui.maintainer_screen import MaintainerScreen
from gui.statistics_screen import StatisticsScreen
from gui.login_dialog import LoginDialog

#from services.hardware import Hardware
#from tests.mockScripts.mock_hardware import MockHardware

from logic.door_sequence import (DoorSequence, DoorState)
from logic.soft_vacuum_sequence import (SoftVacuumSequence, SoftVacuumState)
from logic.main_vacuum_sequence import (MainVacuumSequence, MainVacuumState)
from logic.vent_sequence import (VentSequence, VentState)
from logic.vent_sequence import (VentSequence,VentState)

# gui-developement
class MainWindow(QMainWindow):

    def __init__(self, hardware):
        super().__init__()

        self.hardware = hardware

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()

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

        # Inicializa la interfaz real con el hardware del Plasma Asher.
        # Controlador encargado del monitoreo y control de señales digitales.
        self.signal_controller = SignalController(
            hardware=self.hardware,
            monitored_signals=MAINTAINER_SIGNALS,
            output_signals=MAINTAINER_OUTPUT_SIGNALS,
            poll_interval_ms=100,
        )

        #Secuencias funcionales
        self.door_sequence = DoorSequence(
            hardware=self.hardware,
        )
        self.soft_vacuum_sequence = SoftVacuumSequence(
            hardware=self.hardware,
        )      
        self.main_vacuum_sequence = MainVacuumSequence(
            hardware=self.hardware,
        )
        self.vent_sequence = VentSequence(
            hardware=self.hardware,
        )

        # Controlador de interlocks - Determina el uso seguro de las secuencias según el estado del equipo
        self.interlock_controller = InterlockController(
            door_sequence=self.door_sequence,
            soft_vacuum_sequence=self.soft_vacuum_sequence,
            main_vacuum_sequence=self.main_vacuum_sequence,
            vent_sequence=self.vent_sequence,   
        )

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

        # Navegación hacia la pantalla de bienvenida
        self.maintainer_screen.back_requested.connect(
            self._show_welcome_screen
        )
        self.statistics_screen.back_requested.connect(
            self._show_welcome_screen
        )

        # Solicitud global de salida
        self.top_bar.exit_requested.connect(
            self._confirm_exit
        )

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
        # Manejo temporal de errores.
        self.signal_controller.signal_error.connect(
            self._handle_signal_error
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

    # Vent sequence
        self.maintainer_screen.vent_chamber_sequence_requested.connect(
            self.vent_sequence.toggle
        )
        self.vent_sequence.state_changed.connect(
            self._handle_vent_state_changed
        )
        self.vent_sequence.vent_completed.connect(
            self._handle_vent_completed
        )
        self.vent_sequence.sequence_error.connect(
            self._handle_vent_sequence_error
        )

        # =========================================================
        # Estado inicial de las secuencias
        # =========================================================
        self.maintainer_screen.set_door_state( self.door_sequence.state )
        self.maintainer_screen.set_soft_vacuum_state( self.soft_vacuum_sequence.state )
        self.maintainer_screen.set_main_vacuum_state(self.main_vacuum_sequence.state )
        self.maintainer_screen.set_vent_state(self.vent_sequence.state )
        self._update_sequence_permissions()

        # ====================
        # TEST sequencias borrar
        # ====================
        self.maintainer_screen.soft_vacuum_sequence_requested.connect(
            lambda: print("[Maintainer] Soft Vacuum")
        )

        self.maintainer_screen.main_vacuum_sequence_requested.connect(
            lambda: print("[Maintainer] Main Vacuum")
        )

        self.maintainer_screen.vent_chamber_sequence_requested.connect(
            lambda: print("[Maintainer] Vanteo de Cámara")
        )        
        # ====================
        # Fin TEST sequencias
        # ====================


    def _show_welcome_screen(self):
    # Muestra la pantalla de bienvenida
        self.signal_controller.stop_monitoring()
        self.navigation_controller.show_screen(
            WELCOME_SCREEN
        )

    def _show_maintainer_screen(self):
    # Muestra la pantalla de mantenimiento e inicia el monitoreo de señales
        self.navigation_controller.show_screen(
            MAINTAINER_SCREEN
        )
        self.signal_controller.start_monitoring()

    def _show_statistics_screen(self):
    # Muestra la pantalla de estadísticas
        self.navigation_controller.show_screen(
            STATISTICS_SCREEN
        )

    def _request_maintainer_access(self):
    # Solicita autenticación antes de ingresar al modo de mantenimiento
        login_dialog = LoginDialog(self)

        result = login_dialog.exec_()

        if result == QDialog.Accepted:
            self._show_maintainer_screen()

    def _handle_signal_error(
        self,
        signal_name: str,
        message: str,
    ) -> None:
        """Muestra temporalmente errores del controlador en consola."""

        print(
            f"[SignalController] ERROR {signal_name}: {message}"
        )


    def _handle_digital_signal_changed(
        self,
        signal_name,
        active,
    ):
        if signal_name == "ATM_SWITCH":
            self.vent_sequence.update_atmospheric_state(
                active
            )
            
    def _confirm_exit(self):
    # Confirma con el usuario antes de cerrar la aplicación
        response = QMessageBox.question(
        self,
        EXIT_CONFIRMATION_TITLE,
        EXIT_CONFIRMATION_MESSAGE,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )

        if response == QMessageBox.Yes:
            self.close()

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
        self._update_sequence_permissions()

    def _handle_door_sequence_error(self, message):
        print(
            f"[DoorSequence] ERROR: {message}"
        )

    def _can_open_door(self):
        #La puerta solo puede abrirse si las valvulas de vacio estan detenidas.
        return (
            self.soft_vacuum_sequence.state
            == SoftVacuumState.IDLE
        )

# Soft Vacumm
    def _can_start_soft_vacuum(self):
        #Soft Vacuum solo puede iniciarse con la puerta cerrada.
        return ( self.door_sequence.state == DoorState.CLOSED )

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
        if state == MainVacuumState.RUNNING:
            self.interlock_controller.vacuum_started()
            self._handle_main_vacuum_started()
        self._update_sequence_permissions()

    def _handle_main_vacuum_started(self):
        #Coordina las acciones necesarias después del arranque de Main Vacuum.
        if (self.soft_vacuum_sequence.state == SoftVacuumState.RUNNING):
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
        if state == VentState.RUNNING:
            atm_active = (
                self.signal_controller.get_last_state("ATM_SWITCH")
            )
            if atm_active is not None:
                self.vent_sequence.update_atmospheric_state(atm_active)
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