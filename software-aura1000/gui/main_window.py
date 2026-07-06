from PyQt5 import QtWidgets
from gui.pyqt_gui import Ui_MainWindow
from services.system_state import systemState
from logic.timers_io import timersIOManager
import logic.pre_encendido as preEncendido
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
    
    # ------------ Inicializa visualmente el menú principal ----------------
    def MainMenu_init(self):
        self.ui.stackedWidget.setCurrentWidget(self.ui.MenuPrincipal)
        
        # Habilitar / Deshabilitar Driver de la AURA 1000 DIO
        self.ui.MenuPrincipal_btn_enable_driver.clicked.connect(self._btn_enable_driver)
        # Abrir / Cerrar puerta de camara
        self.ui.MenuPrincipal_btn_open_door.clicked.connect(self._btn_open_door)

    # ------------- Funciones de habilitacion de driver y apertura cierra de puerta --------------
    def _btn_enable_driver(self):
        # Leemos el texto actual para saber qué acción tomar
        if self.ui.MenuPrincipal_btn_enable_driver.text() == "Habilitar Drivers":
            self.hw.digital_set("DRIVER_ENABLE",ACTIVE)
            self.ui.MenuPrincipal_btn_enable_driver.setText("Deshabilitar Drivers")
            # Podés sumarle color con StyleSheet si querés (Rojo para indicar peligro/potencia)
            self.ui.MenuPrincipal_btn_enable_driver.setStyleSheet("background-color: #f44336; color: white;")
        else:
            self.hw.digital_set("DRIVER_ENABLE",INACTIVE)
            self.ui.MenuPrincipal_btn_enable_driver.setText("Habilitar Drivers")
            self.ui.MenuPrincipal_btn_enable_driver.setStyleSheet("")

    def _btn_open_door(self):
        # Leemos el texto actual para saber qué acción tomar
        if self.ui.MenuPrincipal_btn_open_door.text() == "Abrir Puerta":
            self.hw.digital_set("DOOR_OPEN_CMD",ACTIVE)
            self.ui.MenuPrincipal_btn_open_door.setText("Cerrar Puerta")
            # Podés sumarle color con StyleSheet si querés (Rojo para indicar peligro/potencia)
            self.ui.MenuPrincipal_btn_open_door.setStyleSheet("background-color: #f44336; color: white;")
        else:
            self.hw.digital_set("DOOR_OPEN_CMD",INACTIVE)
            self.ui.MenuPrincipal_btn_open_door.setText("Abrir Puerta")
            self.ui.MenuPrincipal_btn_open_door.setStyleSheet("")
    
    # ------- Fuerza el cierre seguro por pulsador físico OFF -----------
    def trigger_hardware_off(self):
        self.offClose = 1
        self.close() # Esto llama a closeEvent

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
