from config.digital_signals import ACTIVE, INACTIVE
from PyQt5 import QtCore, QtGui, QtWidgets
from gui.powerOnGUI import Ui_MainWindow

# Esta es la clase que se llama en Main y dentro de esta se llama a la UI generada en PyQt
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hardware):
        super().__init__()

        self.hw = hardware

        # crear interfaz
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Ocultar barra inicialmente
        self.ui.PreEncendido_progressBar.hide()
        # Variables startup
        self.startup_progress = 0
        # Timer startup
        self.startup_timer = QtCore.QTimer()
        # Cada timeout llama a update_startup()
        self.startup_timer.timeout.connect(self.update_startup)
        # Timer para leer POWER_ON_SWITCH
        self.power_timer = QtCore.QTimer()
        self.power_timer.timeout.connect(self.check_power_on)
        # Leer entrada cada 100 ms
        self.power_timer.start(100)

    # Chequeo de si se pulso ON al inicio cada 100ms
    def check_power_on(self):
        if self.hw.digital_read("POWER_ON_SWITCH"):
            self.power_timer.stop()
            self.startup_sequence()

    # Si se pulso ON, realiza esta secuencia:
    # Habilita señal POWER_ON, arranca timer de 10s, muestra barra de progreso, luego de ese tiempo inicializa placas y pasa a Main Menu
    def startup_sequence(self):
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

    def update_startup(self):
        self.startup_progress += 1
        self.ui.PreEncendido_progressBar.setValue(self.startup_progress)
        # 100 pasos x 100ms = 10 segundos
        if self.startup_progress >= 100:
            self.startup_timer.stop()
            # Ir al menú principal
            self.ui.stackedWidget.setCurrentIndex(1)
            # Arrancar lógica del menú principal
            #self.initialize_main_menu()

    #def initialize_main_menu(self):

    def closeEvent(self, event):
        self.hw.close()
        event.accept()

