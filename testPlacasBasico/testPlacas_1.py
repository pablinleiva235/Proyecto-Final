import sys
import ctypes
from PyQt5 import QtCore, QtWidgets

# ---------------- DLLs ----------------
daq = ctypes.windll.LoadLibrary(r"C:\Program Files (x86)\DaqX\Drivers\USB\DaqX.dll")
cbw = ctypes.windll.LoadLibrary(r"C:\Program Files (x86)\Measurement Computing\DAQ\cbw32.dll")

# ---------------- DAQX config ----------------
daq.daqOpen.restype = ctypes.c_int
daq.daqOpen.argtypes = [ctypes.c_char_p]

daq.daqDacSetOutputMode.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_ulong, ctypes.c_int]
daq.daqDacWt.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_ulong, ctypes.c_ushort]
daq.daqClose.argtypes = [ctypes.c_int]

DddtLocal = 0
DdomVoltage = 0

# ---------------- CBW config ----------------
cbw.cbDConfigPort.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
cbw.cbDBitOut.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]

FIRSTPORTA = 10
DIGITALOUT = 1


# ---------------- UI ----------------
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(498, 169)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(40, 50, 131, 51))
        self.pushButton.setObjectName("pushButton")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(30, 22, 151, 16))
        self.label.setObjectName("label")
        self.horizontalSlider = QtWidgets.QSlider(self.centralwidget)
        self.horizontalSlider.setGeometry(QtCore.QRect(260, 80, 160, 22))
        self.horizontalSlider.setMaximum(5)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(260, 50, 161, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(230, 20, 241, 21))
        self.label_3.setObjectName("label_3")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 498, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Test Placas"))
        self.pushButton.setText(_translate("MainWindow", "Digital OUT"))
        self.label.setText(_translate("MainWindow", "Pulsa para activar salida digital"))
        self.label_2.setText(_translate("MainWindow", "0V     1V      2V      3V      4V      5V "))
        self.label_3.setText(_translate("MainWindow", "Mueve el slider para modificar la salida analogica"))


# ---------------- APP ----------------
class MainApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Inicializar hardware
        self.init_daq()
        self.init_dio()

        # Conectar UI
        self.ui.pushButton.pressed.connect(self.digital_on)
        self.ui.pushButton.released.connect(self.digital_off)
        self.ui.horizontalSlider.valueChanged.connect(self.update_dac)

    # -------- DAQ --------
    def init_daq(self):
        device = b"DaqBoard3001USB"
        self.handle = daq.daqOpen(device)

        if self.handle == -1:
            print("Error abriendo DAQ")
            return

        daq.daqDacSetOutputMode(self.handle, DddtLocal, 0, DdomVoltage)
        print("DAQ OK")

    # -------- DIO --------
    def init_dio(self):
        self.BoardNum = 0
        self.PortNum = FIRSTPORTA
        self.BitNum = 0

        err = cbw.cbDConfigPort(self.BoardNum, self.PortNum, DIGITALOUT)

        if err != 0:
            print("Error configurando DIO")
        else:
            print("DIO OK")

    # -------- BOTON --------
    def digital_on(self):
        cbw.cbDBitOut(self.BoardNum, self.PortNum, self.BitNum, 1)
        print("Digital ON")

    def digital_off(self):
        cbw.cbDBitOut(self.BoardNum, self.PortNum, self.BitNum, 0)
        print("Digital OFF")

    # -------- SLIDER --------
    def update_dac(self, value):
        # value = 0 a 5 V

        # Ajuste típico ±5V (0V ≈ 32768)
        dac_value = int(32768 + (value/2) * (65535 / 10))

        daq.daqDacWt(self.handle, DddtLocal, 0, dac_value)

        print(f"DAC = {value} V")

    # -------- CIERRE --------
    def closeEvent(self, event):
        if hasattr(self, "handle"):
            daq.daqDacWt(self.handle, DddtLocal, 0, 32768)
            daq.daqClose(self.handle)
        event.accept()


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
