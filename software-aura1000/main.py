"""
Punto de entrada principal de la aplicación.

Este módulo es responsable únicamente de:
- Crear QApplication.
- Aplicar el tema global.
- Crear las dependencias principales.
- Ensamblar los controladores y pantallas.
- Iniciar el ciclo de vida de la aplicación.

La lógica de hardware, navegación y secuencia de inicio pertenece a sus
respectivos controladores y servicios.
"""

import sys

from PyQt5.QtWidgets import QApplication

from config_gui.theme import APP_STYLE

from services.hardware import Hardware

from logic.pre_encendido import StartupSequence

from controllers.startup_controller import StartupController
from controllers.application_controller import ApplicationController

from gui.startup_screen import StartupScreen
from gui.main_window import MainWindow


def main():
    """Inicializa y ejecuta la aplicación."""

    # =========================================================================
    # Aplicación Qt
    # =========================================================================

    app = QApplication(sys.argv)

    app.setStyleSheet(APP_STYLE)

    # =========================================================================
    # Hardware
    # =========================================================================

    # Se crea una única instancia de Hardware para toda la aplicación.
    #
    # Esta misma instancia será utilizada durante:
    # - La secuencia de pre-encendido.
    # - La supervisión del arranque.
    # - El monitoreo y control desde MaintainerScreen.
    hardware = Hardware()

    # =========================================================================
    # Secuencia física de pre-encendido
    # =========================================================================

    startup_sequence = StartupSequence(
        hardware=hardware,
    )

    # =========================================================================
    # Controlador de arranque
    # =========================================================================

    startup_controller = StartupController(
        hardware=hardware,
        startup_sequence=startup_sequence,
    )

    # =========================================================================
    # Interfaces gráficas
    # =========================================================================

    startup_screen = StartupScreen()

    main_window = MainWindow(
        hardware=hardware,
    )

    # =========================================================================
    # Controlador general de la aplicación
    # =========================================================================

    application_controller = ApplicationController(
        startup_controller=startup_controller,
        startup_screen=startup_screen,
        main_window=main_window,
    )

    # =========================================================================
    # Inicio de la aplicación
    # =========================================================================

    application_controller.start()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

    
#main branch
'''
# Handler que lleva las señales a estado seguro ante alguna falla inesperada de la interfaz grafica
def global_exception_handler(exctype, value, traceback):
    """
    Captura cualquier excepción no manejada en el software para forzar
    el estado seguro del reactor AURA 1000 antes de cerrar la aplicación.
    """
    print(f"\n[CRITICAL] Error no manejado detectado: {exctype.__name__}: {value}")
    
    try:
        # Buscamos la instancia de hardware a través de la ventana principal
        if 'window' in globals() and hasattr(window, 'hw') and window.hw is not None:
            print("Ejecutando shutdown_state() de emergencia en hardware.py...")
            window.hw.shutdown_state()
        else:
            print("Alerta: No se encontró la instancia de hardware activa para el apagado seguro.")
    except Exception as hw_err:
        print(f"Error crítico al intentar forzar el estado seguro: {hw_err}")

    # Mostrar cartel de alerta al operario en el laboratorio
    try:
        error_msg = (
            f"Ocurrió un error inesperado en el sistema.\n\n"
            f"El hardware se ha llevado a ESTADO SEGURO automáticamente.\n\n"
            f"Detalle del error:\n{value}"
        )
        QtWidgets.QMessageBox.critical(None, "Falla Crítica de Sistema", error_msg)
    except Exception as gui_err:
        print(f"No se pudo mostrar el cuadro de diálogo de Qt: {gui_err}")

    # Llamamos al comportamiento por defecto de Python (imprime el traceback en consola)
    sys.__excepthook__(exctype, value, traceback)
    
    # Forzamos la salida inmediata del script para evitar bucles zombis en la GUI
    sys.exit(1)

if __name__ == "__main__":
    # app = QtWidgets.QApplication(sys.argv)
    # hw = Hardware()
    # #Inicializo solo placa digital al inicio ya que debo leer el boton de ON para encender
    # window = MainWindow(hw)
    # window.show()
    # sys.exit(app.exec_()) 
    main()

'''