"""
Controlador general del ciclo de vida de la aplicación.

ApplicationController coordina las grandes etapas de la aplicación:

- Mostrar StartupScreen durante el pre-encendido.
- Conectar StartupController con StartupScreen.
- Mostrar MainWindow cuando la secuencia de arranque finaliza correctamente.

ApplicationController no:
- Ejecuta directamente operaciones de hardware.
- Controla la secuencia física de encendido.
- Navega entre las pantallas internas de MainWindow.
- Conoce los detalles del QStackedWidget.

La navegación interna de la aplicación continúa siendo responsabilidad de
NavigationController.
"""

from typing import Optional
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox

from controllers.startup_controller import StartupState

from config_gui.strings import (EXIT_CONFIRMATION_TITLE,EXIT_CONFIRMATION_MESSAGE)
from config_gui.strings import tr
from services.shutdown_log import SHUTDOWN_LOG_PATH

class ApplicationController(QObject):
    """Coordina el ciclo de vida general de la aplicación."""

    def __init__(
        self,
        startup_controller,
        power_controller,
        shutdown_controller,
        startup_screen,
        main_window,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self._startup_controller = startup_controller
        self._power_controller = power_controller
        self._shutdown_controller = shutdown_controller
        self._startup_screen = startup_screen
        self._main_window = main_window

        self.connect_signals()

    # =========================================================================
    # Conexiones
    # =========================================================================

    def connect_signals(self) -> None:
        #Conecta los eventos del arranque con la interfaz.
        self._power_controller.startup_requested.connect(
            self._handle_startup_requested
        )
        self._power_controller.shutdown_requested.connect(
            self._handle_shutdown_requested
        )

        self._startup_controller.state_changed.connect(
            self._handle_startup_state_changed
        )
        self._startup_controller.progress_changed.connect(
            self._startup_screen.set_progress
        )
        self._startup_controller.startup_error.connect(
            self._startup_screen.show_error
        )

        self._shutdown_controller.shutdown_completed.connect(
            self._handle_shutdown_completed
        )
        self._shutdown_controller.shutdown_error.connect(
            self._handle_shutdown_error
        )

        self._main_window.exit_requested.connect(
            self._handle_exit_requested
        )

    # =========================================================================
    # Interfaz pública
    # =========================================================================

    def start(self) -> None:
        """Inicia el ciclo de vida de la aplicación."""

        # MainWindow permanece oculto hasta completar el pre-encendido.
        self._main_window.hide()

        # Muestra la interfaz inicial de espera.
        self._startup_screen.show_waiting_for_power()
        self._startup_screen.showFullScreen()

        # Comienza a supervisar POWER_ON_SWITCH.
        self._power_controller.start_startup_monitoring()

    # =========================================================================
    # Gestión del arranque
    # =========================================================================
    def _handle_startup_requested(self):
        print(
            "[ApplicationController] "
            "Solicitud física de encendido."
        )
        self._startup_controller.start()

    def _handle_startup_state_changed(
        self,
        state: StartupState,
    ) -> None:
        """Actualiza StartupScreen según el estado del arranque."""

        if state == StartupState.IDLE:
            self._startup_screen.show_waiting_for_power()

        elif state == StartupState.STARTING:
            self._startup_screen.show_starting()

        elif state == StartupState.READY:
            # La transición a MainWindow se realiza mediante startup_ready.
            self._handle_startup_ready()
            pass

        elif state == StartupState.ERROR:
            # El mensaje concreto se recibe mediante startup_error.
            pass

    def _handle_startup_ready(self) -> None:
        #Realiza la transición de StartupScreen a MainWindow.
        # Oculta la pantalla de inicio.
        self._startup_screen.hide()
        # Muestra la aplicación principal.
        self._main_window.showFullScreen()
        # Comienza a supervisar la solicitud física de apagado.
        self._power_controller.start_shutdown_monitoring()

    def _handle_shutdown_requested(self) -> None:
        print(
            "[ApplicationController] "
            "Solicitud física de apagado."
        )

        self._shutdown_controller.start()

    def _handle_shutdown_completed(self) -> None:
        print(
            "[ApplicationController] "
            "Apagado completado correctamente."
        )
        self._main_window.close()


    def _handle_shutdown_error(
        self,
        message: str,
    ) -> None:
        print(
            "[ApplicationController] "
            f"Error durante el apagado: {message}"
        )

    def _handle_exit_requested(self) -> None:
        dialog = QMessageBox(self._main_window)
        dialog.setWindowTitle(tr(EXIT_CONFIRMATION_TITLE))
        dialog.setText(tr(EXIT_CONFIRMATION_MESSAGE))
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.button(QMessageBox.Yes).setText(tr("Sí"))
        dialog.button(QMessageBox.No).setText(tr("No"))
        dialog.setDefaultButton(QMessageBox.No)
        response = dialog.exec_()

        if response != QMessageBox.Yes:
            print(
                "[ApplicationController] "
                "Cancelado"
            )
            return

        self._power_controller.stop()
        self._shutdown_controller.start()


    def _handle_shutdown_requested(self) -> None:
        print(
            "[ApplicationController] "
            "Solicitud física de apagado."
        )

        self._power_controller.stop()
        self._shutdown_controller.start()

    def _handle_shutdown_completed(self) -> None:
        print(
            "[ApplicationController] "
            "Apagado completado correctamente."
        )

        self._main_window.close()

    def _handle_shutdown_error(self,message: str) -> None:
        print(
            "[ApplicationController] "
            f"Error durante el apagado: {message}"
        )
        QMessageBox.warning(
            self._main_window,
            tr("Errores durante el apagado"),
            tr("Se encontraron errores durante el apagado. Revise el registro:")
            + f"\n{SHUTDOWN_LOG_PATH}\n\n{message}",
        )
