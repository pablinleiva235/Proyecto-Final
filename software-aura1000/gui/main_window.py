from PyQt5 import QtWidgets
from gui.pyqt_gui import Ui_MainWindow
from services.system_state import SystemState
from logic.timers_io import TimersIOManager
import logic.pre_encendido as pre_encendido_logic

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
        self.timer_manager = TimersIOManager(self)
        self.timer_manager.start_all_core_timers()

        # Iniciar la máquina de estados en PRE_ENCENDIDO
        self.current_state = SystemState.PRE_ENCENDIDO
        self.change_state(SystemState.PRE_ENCENDIDO)

    # =========================================================
    # MAQUINA DE ESTADOS PRINCIPAL
    # =========================================================
    def change_state(self, new_state):
        print(f"STATE: {self.current_state} -> {new_state}")
        self.current_state = new_state
        
        if new_state == SystemState.PRE_ENCENDIDO:
            pre_encendido_logic.iniciar_interfaz_pre_encendido(self)
        elif new_state == SystemState.MAIN_MENU:
            self.MainMenu_init()

    # =========================================================
    # ACCIONES INVOCADAS POR LA LOGICA EXTERNA
    # =========================================================

    # ------------- DEL PRE-ENCENDIDO --------------------------
    def PreEncendido_startup_sequence(self):
        """La lógica de timers detectó el botón ON y le ordena a la ventana ejecutar el startup"""
        pre_encendido_logic.ejecutar_secuencia_startup(self)

    # ----------------- DEL MAIN MENU --------------------------
    def MainMenu_init(self):
        """Inicializa visualmente el menú principal"""
        self.ui.stackedWidget.setCurrentWidget(self.ui.MenuPrincipal)
        # Próximamente llamarás acá a: logic.vacuum.init_menu(self)

    def trigger_hardware_off(self):
        """Fuerza el cierre seguro por pulsador físico OFF"""
        self.offClose = 1
        self.close()

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
