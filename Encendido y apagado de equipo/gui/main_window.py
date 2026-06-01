from config.digital_signals import ACTIVE, INACTIVE
from PyQt5 import QtCore, QtGui, QtWidgets
from gui.powerOnGUI import Ui_MainWindow
from services.system_state import SystemState

# Esta es la clase que se llama en Main y dentro de esta se llama a la UI generada en PyQt
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hardware):
        super().__init__()

        self.hw = hardware
        self.offClose = 0

        # Crear interfaz
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Inicio de timer general de lectura de entradas
        self.io_timer = QtCore.QTimer()
        self.io_timer.timeout.connect(self.update_inputs)
        self.io_timer.start(100)

        # Paso al primer estado: PRE_ENCENDIDO
        self.current_state = SystemState.PRE_ENCENDIDO
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
    # UPDATE GENERAL DE ENTRADAS
    # =========================================================
    def update_inputs(self):
        # Lectura de entradas del estado PRE_ENCENDIDO
        if self.current_state == SystemState.PRE_ENCENDIDO:
            self.PreEncendido_check_power_on()
        # Lectura de entradas del estado MAIN_MENU
        elif self.current_state == SystemState.MAIN_MENU:
            self.MainMenu_check_power_off()

    # =========================================================
    # FUNCIONES DEL ESTADO 0: PRE-ENCENDIDO
    # =========================================================

    def PreEncendido_init(self):
        #Inicio en pagina 1 de la GUI
        self.ui.stackedWidget.setCurrentWidget(self.ui.PreEncendido)
        # Ocultar barra inicialmente
        self.ui.PreEncendido_progressBar.hide()
        # Variables startup
        self.startup_progress = 0
        # Timer para update de progressbar
        self.startup_timer = QtCore.QTimer()
        self.startup_timer.timeout.connect(self.PreEncendido_update_progressbar)

    # Chequeo de si se pulso ON al inicio cada 100ms
    def PreEncendido_check_power_on(self):
        if self.hw.digital_read("POWER_ON_SWITCH"):
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
        # self.hw.initialize_AD() DESCOMENTAR ESTO EN NOTEBOOK DE SALA!!!!
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
        self.ui.stackedWidget.setCurrentWidget(self.ui.MenuPrincipal)

    # Chequeo si se pulso OFF
    def MainMenu_check_power_off(self):
        if self.hw.digital_read("SYS_POWER"):
            print("POWER OFF DETECTADO")
            self.offClose = 1
            self.close()


    # =========================================================
    # FUNCION DE CIERRE DE VENTANA
    # =========================================================
    def closeEvent(self, event):
            if self.offClose == 0:
                # --- CASO 1: Cierre por la "X" (Pregunta Confirmación) ---
                reply = QtWidgets.QMessageBox.question(
                    self, 
                    'Confirmar Salida',
                    '¿Está seguro de que desea cerrar la aplicación?',
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, 
                    QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    try:
                        # Llevamos el hardware a estado seguro y frenamos el lazo de I/O
                        self.hw.shutdown_state()
                        self.io_timer.stop()
                        print("Hardware llevado a estado seguro correctamente.")
                    except Exception as e:
                        print(f"Error al intentar llevar el hardware a estado seguro: {e}")
                    
                    event.accept()
                else:
                    event.ignore()
                    
            else:
                # --- CASO 2: Cierre por pulsador físico OFF (Aviso obligatorio) ---
                # Mostramos la ventana informativa que solo tiene el botón de Aceptar
                QtWidgets.QMessageBox.information(
                    self,
                    'Apagado del Sistema',
                    'El programa se cerrará dejando las placas en estado seguro.',
                    QtWidgets.QMessageBox.Ok
                )
                
                try:
                    # Forzamos de igual manera el estado seguro y apagamos el timer
                    self.hw.shutdown_state()
                    self.io_timer.stop()
                    print("Hardware llevado a estado seguro de forma automática por pulsador OFF.")
                except Exception as e:
                    print(f"Error al intentar llevar el hardware a estado seguro en apagado directo: {e}")
                
                # Aceptamos el cierre directamente sin más preguntas
                event.accept()

