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
        self.throttle = ThrottleController(self)

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
        
        # Prueba de motor paso a paso
        #1. Habilitar / Deshabilitar Driver
        self.ui.MenuPrincipal_btn_toggle_enable.clicked.connect(self._on_enable_toggled)
        # 2. Configuración de Pasos (Full / Half)
        self.ui.MenuPrincipal_btn_toggle_step.clicked.connect(self._on_step_toggled)
        # 3. Sentido de Giro (Cierre / Apertura)
        self.ui.MenuPrincipal_btn_toggle_dir.clicked.connect(self._on_dir_toggled)
        # 4. Marcha / Parada del Tren de Pulsos
        self.ui.MenuPrincipal_btn_toggle_run.clicked.connect(self._on_run_toggled) 

    # ------------- Funciones del pulsado de los botones para prueba motor paso a paso --------------
    def _on_enable_toggled(self):
        # Leemos el texto actual para saber qué acción tomar
        if self.ui.MenuPrincipal_btn_toggle_enable.text() == "Habilitar Driver":
            self.throttle.set_enable(ACTIVE)
            self.ui.MenuPrincipal_btn_toggle_enable.setText("Deshabilitar Driver")
            # Podés sumarle color con StyleSheet si querés (Rojo para indicar peligro/potencia)
            self.ui.MenuPrincipal_btn_toggle_enable.setStyleSheet("background-color: #f44336; color: white;")
        else:
            self.throttle.set_enable(INACTIVE)
            self.ui.MenuPrincipal_btn_toggle_enable.setText("Habilitar Driver")
            self.ui.MenuPrincipal_btn_toggle_enable.setStyleSheet("")

    def _on_step_toggled(self):
        if "Full Step" in self.ui.MenuPrincipal_btn_toggle_step.text():
            self.throttle.set_half_step(ACTIVE) # Pasamos a Half
            self.ui.MenuPrincipal_btn_toggle_step.setText("Modo: Half Step")
        else:
            self.throttle.set_half_step(INACTIVE) # Volvemos a Full
            self.ui.MenuPrincipal_btn_toggle_step.setText("Modo: Full Step")

    def _on_dir_toggled(self):
        if "Apertura" in self.ui.MenuPrincipal_btn_toggle_dir.text():
            self.throttle.set_direction(ACTIVE) # DIR = 1 (Cierre)
            self.ui.MenuPrincipal_btn_toggle_dir.setText("Dirección: Cierre")
        else:
            self.throttle.set_direction(INACTIVE) # DIR = 0 (Apertura)
            self.ui.MenuPrincipal_btn_toggle_dir.setText("Dirección: Apertura")

    def _on_run_toggled(self):
        if self.ui.MenuPrincipal_btn_toggle_run.text() == "Girar Motor":
            # Iniciamos el movimiento lento (ej: 6ms por semiciclo)
            self.throttle.start_movement(speed_ms=6)
            self.ui.MenuPrincipal_btn_toggle_run.setText("Detener Motor")
            self.ui.MenuPrincipal_btn_toggle_run.setStyleSheet("background-color: #ff9800; color: black;")
        else:
            self.throttle.stop_movement()
            self.ui.MenuPrincipal_btn_toggle_run.setText("Girar Motor")
            self.ui.MenuPrincipal_btn_toggle_run.setStyleSheet("")   
    
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
