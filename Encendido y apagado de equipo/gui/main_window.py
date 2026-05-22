from config.digital_signals import ACTIVE, INACTIVE
from PyQt5 import QtCore, QtGui, QtWidgets

# Aca va el codigo de QtDesigner
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(957, 730)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.stackedWidget = QtWidgets.QStackedWidget(self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(48)
        self.stackedWidget.setFont(font)
        self.stackedWidget.setObjectName("stackedWidget")
        self.Pre_Encendido = QtWidgets.QWidget()
        self.Pre_Encendido.setObjectName("Pre_Encendido")
        self.labelMenuPrincipal = QtWidgets.QLabel(self.Pre_Encendido)
        self.labelMenuPrincipal.setGeometry(QtCore.QRect(0, 70, 941, 121))
        font = QtGui.QFont()
        font.setPointSize(48)
        font.setBold(True)
        font.setWeight(75)
        self.labelMenuPrincipal.setFont(font)
        self.labelMenuPrincipal.setAlignment(QtCore.Qt.AlignCenter)
        self.labelMenuPrincipal.setWordWrap(True)
        self.labelMenuPrincipal.setObjectName("labelMenuPrincipal")
        self.pushButton_OpenCloseDoor = QtWidgets.QPushButton(self.Pre_Encendido)
        self.pushButton_OpenCloseDoor.setGeometry(QtCore.QRect(250, 300, 171, 81))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.pushButton_OpenCloseDoor.setFont(font)
        self.pushButton_OpenCloseDoor.setObjectName("pushButton_OpenCloseDoor")
        self.pushButton_EnableDisableDrivers = QtWidgets.QPushButton(self.Pre_Encendido)
        self.pushButton_EnableDisableDrivers.setGeometry(QtCore.QRect(510, 300, 171, 81))
        font = QtGui.QFont()
        font.setPointSize(10)
        self.pushButton_EnableDisableDrivers.setFont(font)
        self.pushButton_EnableDisableDrivers.setObjectName("pushButton_EnableDisableDrivers")
        self.stackedWidget.addWidget(self.Pre_Encendido)
        self.Menu_Inicial = QtWidgets.QWidget()
        self.Menu_Inicial.setObjectName("Menu_Inicial")
        self.PreEncendido_label2 = QtWidgets.QLabel(self.Menu_Inicial)
        self.PreEncendido_label2.setGeometry(QtCore.QRect(0, 220, 941, 231))
        font = QtGui.QFont()
        font.setPointSize(26)
        self.PreEncendido_label2.setFont(font)
        self.PreEncendido_label2.setAlignment(QtCore.Qt.AlignCenter)
        self.PreEncendido_label2.setWordWrap(True)
        self.PreEncendido_label2.setObjectName("PreEncendido_label2")
        self.PreEncendido_label1 = QtWidgets.QLabel(self.Menu_Inicial)
        self.PreEncendido_label1.setGeometry(QtCore.QRect(220, 130, 511, 71))
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(51, 0, 153))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(51, 0, 153))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(51, 0, 153))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 0, 207, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(51, 0, 153))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(51, 0, 153))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(51, 0, 153))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(69, 0, 207, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.PlaceholderText, brush)
        brush = QtGui.QBrush(QtGui.QColor(51, 0, 153))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, brush)
        brush = QtGui.QBrush(QtGui.QColor(51, 0, 153))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Text, brush)
        brush = QtGui.QBrush(QtGui.QColor(51, 0, 153))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, brush)
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 128))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.PlaceholderText, brush)
        self.PreEncendido_label1.setPalette(palette)
        font = QtGui.QFont()
        font.setPointSize(48)
        font.setBold(True)
        font.setWeight(75)
        self.PreEncendido_label1.setFont(font)
        self.PreEncendido_label1.setStyleSheet("color: rgb(51, 0, 153);")
        self.PreEncendido_label1.setObjectName("PreEncendido_label1")
        self.PreEncendido_progressBar = QtWidgets.QProgressBar(self.Menu_Inicial)
        self.PreEncendido_progressBar.setGeometry(QtCore.QRect(280, 480, 401, 41))
        font = QtGui.QFont()
        font.setPointSize(24)
        self.PreEncendido_progressBar.setFont(font)
        self.PreEncendido_progressBar.setProperty("value", 0)
        self.PreEncendido_progressBar.setObjectName("PreEncendido_progressBar")
        self.stackedWidget.addWidget(self.Menu_Inicial)
        self.verticalLayout.addWidget(self.stackedWidget)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 957, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.stackedWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Aura 1000 Software"))
        self.labelMenuPrincipal.setText(_translate("MainWindow", "Menu Principal"))
        self.pushButton_OpenCloseDoor.setText(_translate("MainWindow", "Abrir Puerta"))
        self.pushButton_EnableDisableDrivers.setText(_translate("MainWindow", "Habilitar Drivers"))
        self.PreEncendido_label2.setText(_translate("MainWindow", "Para acceder al Menu Principal, encienda el equipo con el pulsador de ON"))
        self.PreEncendido_label1.setText(_translate("MainWindow", "¡Bienvenido!"))


# Esta es la clase que se llama en Main y dentro de esta se llama a la UI de arriba
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hardware):
        super().__init__()

        self.hw = hardware

        # crear UI
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

