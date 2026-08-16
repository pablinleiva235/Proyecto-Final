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

from controllers.startup_controller import StartupState


class ApplicationController(QObject):
    """Coordina el ciclo de vida general de la aplicación."""

    def __init__(
        self,
        startup_controller,
        startup_screen,
        main_window,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)

        self._startup_controller = startup_controller
        self._startup_screen = startup_screen
        self._main_window = main_window

        self.connect_signals()

    # =========================================================================
    # Conexiones
    # =========================================================================

    def connect_signals(self) -> None:
        """Conecta los eventos del arranque con la interfaz."""

        self._startup_controller.state_changed.connect(
            self._handle_startup_state_changed
        )

        self._startup_controller.progress_changed.connect(
            self._startup_screen.set_progress
        )

        self._startup_controller.startup_error.connect(
            self._startup_screen.show_error
        )

        self._startup_controller.startup_ready.connect(
            self._handle_startup_ready
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
        self._startup_controller.start()

    # =========================================================================
    # Gestión del arranque
    # =========================================================================

    def _handle_startup_state_changed(
        self,
        state: StartupState,
    ) -> None:
        """Actualiza StartupScreen según el estado del arranque."""

        if state == StartupState.WAITING_POWER:
            self._startup_screen.show_waiting_for_power()

        elif state == StartupState.STARTING:
            self._startup_screen.show_starting()

        elif state == StartupState.READY:
            # La transición a MainWindow se realiza mediante startup_ready.
            pass

        elif state == StartupState.ERROR:
            # El mensaje concreto se recibe mediante startup_error.
            pass

    def _handle_startup_ready(self) -> None:
        """Realiza la transición de StartupScreen a MainWindow."""

        # Ya no se necesita continuar supervisando el arranque.
        self._startup_controller.stop()

        # Oculta la pantalla de inicio.
        self._startup_screen.hide()

        # Muestra la aplicación principal.
        self._main_window.showFullScreen()