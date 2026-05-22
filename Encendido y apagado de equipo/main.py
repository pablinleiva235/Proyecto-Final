import sys
from PyQt5 import QtWidgets

from services.hardware import Hardware
from gui.main_window import MainWindow


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    hw = Hardware()
    #Inicializo solo placa digital al inicio ya que debo leer el boton de ON para encender
    hw.initialize_DIO()
    window = MainWindow(hw)
    window.show()
    sys.exit(app.exec_())