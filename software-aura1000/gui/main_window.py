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
from gui.pyqt_gui import Ui_MainWindow
from services.system_state import systemState
from logic.timers_io import timersIOManager

import logic.pre_encendido as preEncendido
import logic.maintenance_process as maintenanceProcess
from logic.throttle_test import ThrottleController
from config.digital_signals import ACTIVE, INACTIVE

from config_gui.strings import (
    APP_TITLE,
    EXIT_CONFIRMATION_TITLE,
    EXIT_CONFIRMATION_MESSAGE,
)
from config_gui.constants import (
    WELCOME_SCREEN,
    MAINTAINER_SCREEN,
    STATISTICS_SCREEN,
)
from controllers.navigation_controller import NavigationController
from gui.widgets.top_bar_widget import TopBarWidget
from gui.welcome_screen import WelcomeScreen
from gui.maintainer_screen import MaintainerScreen
from gui.statistics_screen import StatisticsScreen
from gui.login_dialog import LoginDialog


# gui-developement

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

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

    def _show_welcome_screen(self):
        # Muestra la pantalla de bienvenida
        self.navigation_controller.show_screen(
            WELCOME_SCREEN
        )

    def _show_maintainer_screen(self):
        # Muestra la pantalla de mantenimiento
        self.navigation_controller.show_screen(
            MAINTAINER_SCREEN
        )

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



# main 
'''
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hardware):
        super().__init__()
        
        self.hw = hardware
        self.offClose = 0
        self.startup_progress = 0  # Almacena el progreso de la barra

        # Crear interfaz autogenerada
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Estado de lamparas y plasma para deteccion de fallas, state_lamps13_pulsing tambien la usa para la habilitacion del boton de venteo
        self.state_lamps13_pulsing = False
        self.lamp2_on = False
        self.rf_on = False

        # Control de ventanas emergentes de alarma/advertencia
        self.alarm_active = False
        self.warning_mag_shown = False

        # Variable con tiempo desde que se pulsa el boton de plasma 
        self.rf_on_time = 0.0

        # =====================================================================
        # ADAPTACIÓN CON SCROLL FORZADO PARA MONITOR 1024x768
        # =====================================================================
        old_central = self.centralWidget()

        if old_central:
            # A. Le fijamos un alto mínimo real a la UI original para que NO se comprima.
            # 950px asegura que entre todo el contenido de Lámparas y Temperatura holgadamente.
            old_central.setMinimumSize(980, 950)

            # B. Creamos el QScrollArea y configuramos sus políticas
            scroll = QtWidgets.QScrollArea()
            scroll.setWidget(old_central)
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

            # C. Forzamos la barra de scroll vertical para que aparezca siempre
            scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Por si el ancho también se queda corto

            # D. Reemplazamos el widget central
            self.setCentralWidget(scroll)
        # =====================================================================
        
        # Instanciar el manager de timers pasándole 'self' (esta ventana)
        self.timer_manager = timersIOManager(self)
        self.timer_manager.start_all_core_timers()

        # Instanciamos el controlador de pruebas del motor
        # self.throttle = ThrottleController(self) # DESCOMENTAR CUANDO PROBEMOS LA THROTTLE YA MODIFICADO throttle.py

        # Iniciar la máquina de estados en PRE_ENCENDIDO
        self.current_state = systemState.PRE_ENCENDIDO
        self.change_state(systemState.PRE_ENCENDIDO)


    # =========================================================
    # MAQUINA DE ESTADOS PRINCIPAL
    # =========================================================
    def change_state(self, new_state):
        print(f"STATE: {self.current_state} -> {new_state}")
        self.current_state = new_state
        
        if new_state == systemState.PRE_ENCENDIDO:
            preEncendido.init(self)
        elif new_state == systemState.MAIN_MENU:
            self.MainMenu_init()

    # =========================================================
    # ACCIONES INVOCADAS POR LA LOGICA EXTERNA
    # =========================================================

    # ==================== DEL PRE-ENCENDIDO ====================
    def preEncendido_startup_sequence(self):
        # La lógica de timers detectó el botón ON y le ordena a la ventana ejecutar el startup
        preEncendido.startup(self)

    # ==================== DEL MAIN MENU ====================
    # ------- Fuerza el cierre seguro por pulsador físico OFF -----------
    def trigger_hardware_off(self):
        self.offClose = 1
        self.close() # Esto llama a closeEvent

    # =========================================================
    # METODOS DE INICIALIZACION DE LOS ESTADOS
    # =========================================================
    # ------------ Inicializa visualmente el menú principal ----------------
    def MainMenu_init(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.MenuPrincipal)
        #Inicia modo de prueba modular
        maintenanceProcess.init(self)

    # =========================================================
    # CONTROL DE CIERRE SEGURO DE VENTANA
    # =========================================================
    def closeEvent(self, event):
        # Frenamos todos los lazos de tiempo antes de abrir diálogos
        self.timer_manager.stop_all_timers()

        if self.offClose == 0:
            # --- CASO 1: Cierre por la "X" del software ---
            reply = QtWidgets.QMessageBox.question(
                self, 'Confirmar Salida', '¿Está seguro de que desea cerrar la aplicación?',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
            )
            if reply == QtWidgets.QMessageBox.Yes:
                self._safely_shutdown()
                event.accept()
            else:
                # Si cancela, reactivamos los timers de lectura
                self.timer_manager.start_all_core_timers()
                event.ignore()
        else:
            # --- CASO 2: Cierre por pulsador físico OFF ---
            QtWidgets.QMessageBox.information(
                self, 'Apagado del Sistema', 'El programa se cerrará dejando las placas en estado seguro.', QtWidgets.QMessageBox.Ok
            )
            self._safely_shutdown()
            event.accept()

    def _safely_shutdown(self):
        try:
            self.hw.shutdown_state()
            print("Hardware llevado a estado seguro correctamente.")
        except Exception as e:
            print(f"Error al intentar llevar el hardware a estado seguro: {e}")

'''