import sys
#from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

#from services.hardware import Hardware
from gui.main_window import MainWindow
from config.theme import APP_STYLE


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    window = MainWindow()
    window.showFullScreen()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

#if __name__ == "__main__":
#   app = QtWidgets.QApplication(sys.argv)
#   hw = Hardware()
#   #Inicializo solo placa digital al inicio ya que debo leer el boton de ON para encender
#   window = MainWindow(hw)
#   window.show()
#   sys.exit(app.exec_())