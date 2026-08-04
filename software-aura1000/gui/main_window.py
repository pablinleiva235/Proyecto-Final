from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from gui.pyqt_gui import Ui_MainWindow
from services.system_state import systemState
from logic.timers_io import timersIOManager

import logic.pre_encendido as preEncendido
import logic.maintenance_process as maintenanceProcess
from logic.throttle_test import ThrottleController
from config.digital_signals import ACTIVE, INACTIVE

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hardware):
        super().__init__()
        
        self.hw = hardware
        self.offClose = 0
        self.startup_progress = 0  # Almacena el progreso de la barra

        # Crear interfaz autogenerada
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Estado de lamparas 1 y 3
        self.state_lamps13_pulsing = False

        # Control de ventanas emergentes de alarma/advertencia
        self.alarm_active = False
        self.warning_mag_shown = False

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
