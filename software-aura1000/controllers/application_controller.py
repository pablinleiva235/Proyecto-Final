"""Controla la transición entre arranque, operación y apagado seguro."""

from typing import Optional

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QApplication, QMessageBox

from config_gui.strings import EXIT_CONFIRMATION_TITLE, EXIT_CONFIRMATION_MESSAGE
from config_gui.strings import tr
from controllers.startup_controller import StartupState
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
        self._shutdown_in_progress = False
        self._shutdown_finalized = False
        self._shutdown_errors = []

        self.connect_signals()

    def connect_signals(self) -> None:
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
        self._startup_screen.close_requested.connect(
            self._handle_startup_close_requested
        )

    def start(self) -> None:
        """Muestra la pantalla de espera e inicia el monitoreo de encendido."""
        self._main_window.hide()
        self._startup_screen.show_waiting_for_power()
        self._startup_screen.showFullScreen()
        self._power_controller.start_startup_monitoring()

    def _handle_startup_requested(self) -> None:
        if self._shutdown_in_progress:
            return
        print("[ApplicationController] Solicitud física de encendido.")
        self._startup_controller.start()

    def _handle_startup_state_changed(self, state: StartupState) -> None:
        if state == StartupState.IDLE:
            self._startup_screen.show_waiting_for_power()
        elif state == StartupState.STARTING:
            self._startup_screen.show_starting()
        elif state == StartupState.READY:
            self._handle_startup_ready()

    def _handle_startup_ready(self) -> None:
        if self._shutdown_in_progress:
            return
        self._startup_screen.hide()
        self._main_window.start_module_monitoring()
        self._main_window.showFullScreen()
        self._power_controller.start_shutdown_monitoring()

    def _handle_shutdown_requested(self) -> None:
        print("[ApplicationController] Solicitud física de apagado.")
        self._begin_shutdown()

    def _handle_startup_close_requested(self) -> None:
        # Cerrar la pantalla de espera cancela el arranque y pide apagado seguro.
        self._begin_shutdown()

    def _handle_exit_requested(self) -> None:
        if self._shutdown_in_progress:
            return

        dialog = QMessageBox(self._main_window)
        dialog.setWindowTitle(tr(EXIT_CONFIRMATION_TITLE))
        dialog.setText(tr(EXIT_CONFIRMATION_MESSAGE))
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dialog.button(QMessageBox.Yes).setText(tr("Sí"))
        dialog.button(QMessageBox.No).setText(tr("No"))
        dialog.setDefaultButton(QMessageBox.No)
        try:
            response = dialog.exec_()
        finally:
            dialog.deleteLater()

        if response == QMessageBox.Yes:
            self._begin_shutdown()
        else:
            print("[ApplicationController] Cierre cancelado.")

    def _begin_shutdown(self) -> None:
        """Detiene tareas activas y ejecuta una única secuencia de estado seguro."""
        if self._shutdown_in_progress:
            return

        self._shutdown_in_progress = True
        self._power_controller.stop()
        self._startup_controller.stop()
        try:
            self._shutdown_errors.extend(
                self._main_window.prepare_for_shutdown() or []
            )
        except Exception as error:
            self._shutdown_errors.append(f"Detención de tareas: {error}")
        self._shutdown_controller.start()

    def _handle_shutdown_error(self, message: str) -> None:
        self._shutdown_errors.append(message)

    def _handle_shutdown_completed(self) -> None:
        if self._shutdown_finalized:
            return
        self._shutdown_finalized = True
        print("[ApplicationController] Apagado finalizado.")
        if self._shutdown_errors:
            parent = self._main_window if self._main_window.isVisible() else self._startup_screen
            QMessageBox.warning(
                parent,
                tr("Errores durante el apagado"),
                tr("Se encontraron errores durante el apagado. Revise el registro:")
                + f"\n{SHUTDOWN_LOG_PATH}\n\n"
                + " | ".join(self._shutdown_errors),
            )

        self._main_window.allow_close()
        self._main_window.close()
        self._startup_screen.allow_close()
        self._startup_screen.close()

        application = QApplication.instance()
        if application is not None:
            application.quit()
