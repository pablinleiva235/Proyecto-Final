from config.digital_signals import ACTIVE, INACTIVE
from PyQt5 import QtCore, QtGui, QtWidgets
from gui.powerOnGUI import Ui_MainWindow
from services.system_state import SystemState

# Esta es la clase que se llama en Main y dentro de esta se llama a la UI generada en PyQt
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hardware):
        super().__init__()

        self.hw = hardware

        # Crear interfaz
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Paso al primer estado: PRE_ENCENDIDO
        self.change_state(SystemState.PRE_ENCENDIDO)


    # =========================================================
    # FUNCION DE CAMBIO DE ESTADO
    # =========================================================
    def change_state(self, new_state):
        print(f"STATE: {self.current_state} -> {new_state}")
        self.current_state = new_state
        if new_state == SystemState.PRE_ENCENDIDO:
            self.PreEncendido_init()
        elif new_state == SystemState.MAIN_MENU:
            self.MainMenu_init()

    # =========================================================
    # FUNCIONES DEL ESTADO 0: PRE-ENCENDIDO
    # =========================================================

    def PreEncendido_init(self):
        # Ocultar barra inicialmente
        self.ui.PreEncendido_progressBar.hide()
        # Variables startup
        self.startup_progress = 0
        # Timer startup
        self.startup_timer = QtCore.QTimer()
        self.startup_timer.timeout.connect(self.PreEncendido_update_progressbar)
        # Timer POWER_ON_SWITCH
        self.power_timer = QtCore.QTimer()
        self.power_timer.timeout.connect(self.PreEncendido_check_power_on)
        # Leer entrada cada 100 ms
        self.power_timer.start(100)

    # Chequeo de si se pulso ON al inicio cada 100ms
    def PreEncendido_check_power_on(self):
        if self.hw.digital_read("POWER_ON_SWITCH"):
            self.power_timer.stop()
            self.PreEncendido_startup_sequence()

    # Si se pulso ON, realiza esta secuencia:
    # Habilita señal POWER_ON, arranca timer de 10s, muestra barra de progreso, luego de ese tiempo inicializa placas y pasa a Main Menu
    def PreEncendido_startup_sequence(self):
        # Activar retención
        self.hw.digital_set("POWER_ON", ACTIVE)
        # Cambiar texto
        self.ui.PreEncendido_label2.setText("Iniciando, espere ...")
        # Mostrar barra
        self.ui.PreEncendido_progressBar.show()
        # Reset barra
        self.startup_progress = 0
        self.ui.PreEncendido_progressBar.setValue(0)
        # Inicializar placa analogica
        self.hw.initialize_AD()
        # Arrancar timer
        self.startup_timer.start(100)

    def PreEncendido_update_progressbar(self):
        self.startup_progress += 1
        self.ui.PreEncendido_progressBar.setValue(self.startup_progress)
        # 100 pasos x 100ms = 10 segundos
        if self.startup_progress >= 100:
            self.startup_timer.stop()
            # Paso a estado MAIN_MENU
            self.change_state(SystemState.MAIN_MENU)

    # =========================================================
    # FUNCIONES DEL ESTADO 1: MAIN_MENU
    # =========================================================
    def MainMenu_init(self):
        # Ir al menú principal --> cambio de pagina
        self.ui.stackedWidget.setCurrentIndex(1)

    def closeEvent(self, event):
        self.hw.close()
        event.accept()

