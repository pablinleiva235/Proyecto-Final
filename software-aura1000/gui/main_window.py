from PyQt5 import QtWidgets
from gui.pyqt_gui import Ui_MainWindow
from services.system_state import systemState
from logic.timers_io import timersIOManager

import logic.pre_encendido as preEncendido
import logic.maintenance_process as maintenanceProcess
from logic.throttle_test import ThrottleController
from config.digital_signals import ACTIVE, INACTIVE

BARATRON_FULL_SCALE = 10

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

    # =================================================================================
    # METODO PARA TOGGLEAR ESTADO VISUAL DE INDICADORES (ATM, Puerta, Lamparas, Plasma)
    # =================================================================================   
    def update_led_indicator(self, label_widget, state_active, text_active, text_inactive):
        """
        Actualiza dinámicamente el estilo de un QLabel para simular un indicador LED.
        """
        if state_active:
            label_widget.setText(text_active)
            label_widget.setStyleSheet("""
                background-color: #2ec4b6; color: black; font-weight: bold; 
                border: 1px solid #0f625a; border-radius: 4px; padding: 4px;
            """)
        else:
            label_widget.setText(text_inactive)
            label_widget.setStyleSheet("""
                background-color: #e0e0e0; color: #757575; font-weight: bold; 
                border: 1px solid #9e9e9e; border-radius: 4px; padding: 4px;
            """)

    # ===================================================================
    # METODO PARA MOSTRAR LA LECTURA DEL BARATRON Y ESTADO DEL ATM SWITCH
    # ===================================================================
    # Se llama constantemente cada 100ms desde el timer general de timers_io.py
    def update_pressure_display(self):
            """
            Lee el Baratron y el ATM_SWITCH, actualiza la GUI y retorna el estado de ATM.
            """
            try:
                voltage = self.hw.analog_read("BARATRON")
                pressure_torr = max(0.0, voltage * (BARATRON_FULL_SCALE / 10.0))
                self.ui.MenuPrincipal_chamber_pressure.display(f"{pressure_torr:.2f}")
                
                # Leemos una única vez el hardware
                atm_active = self.hw.digital_read("ATM_SWITCH")
                self.update_led_indicator(self.ui.MenuPrincipal_lbl_status_atm, atm_active, "PRESION ATM", "VACIO / CAMARA")
                
                # RETORNAMOS EL VALOR LEÍDO
                return atm_active

            except Exception as e:
                print(f"Error al actualizar la presión en el lazo de la GUI: {e}")
                return False

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
