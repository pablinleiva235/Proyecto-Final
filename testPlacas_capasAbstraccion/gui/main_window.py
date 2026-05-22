from PyQt5 import QtCore, QtWidgets


# Aca va el codigo de QtDesigner
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(498, 169)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(40, 50, 131, 51))
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(30, 22, 151, 16))
        self.horizontalSlider = QtWidgets.QSlider(self.centralwidget)
        self.horizontalSlider.setGeometry(QtCore.QRect(260, 80, 160, 22))
        self.horizontalSlider.setMaximum(5)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(260, 50, 161, 16))
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(230, 20, 241, 21))
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Test Placas"))
        self.pushButton.setText(_translate("MainWindow", "Digital OUT"))
        self.label.setText(_translate("MainWindow", "Pulsa para activar salida digital"))
        self.label_2.setText(_translate("MainWindow", "0V     1V      2V      3V      4V      5V "))
        self.label_3.setText(_translate("MainWindow", "Mueve el slider para modificar la salida analogica"))


# Esta es la clase que se llama en Main y dentro de esta se llama a la UI de arriba
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, hardware):
        super().__init__()

        self.hw = hardware

        # crear UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # conexiones
        self.ui.pushButton.pressed.connect(self.hw.digital_on)
        self.ui.pushButton.released.connect(self.hw.digital_off)
        self.ui.horizontalSlider.valueChanged.connect(self.hw.set_voltage)

    def closeEvent(self, event):
        self.hw.close()
        event.accept()