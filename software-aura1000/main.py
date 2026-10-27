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

from PyQt5.QtWidgets import QApplication, QMessageBox

from config_gui.app_config import USE_MOCK_HARDWARE
from config_gui.settings_manager import SettingsManager

if USE_MOCK_HARDWARE:
    from tests.mockScripts.mock_hardware import MockHardware
    from tests.mockScripts.controllers.simulation_controller import SimulationController
else:
    from services.hardware import Hardware


from logic.startup_sequence import StartupSequence
from logic.door_sequence import DoorSequence
from logic.soft_vacuum_sequence import SoftVacuumSequence
from logic.main_vacuum_sequence import MainVacuumSequence
from logic.vent_sequence import VentSequence
from logic.shutdown_sequence import ShutdownSequence

from controllers.power_controller import PowerController
from controllers.startup_controller import StartupController
from controllers.shutdown_controller import ShutdownController
from controllers.application_controller import ApplicationController

from gui.startup_screen import StartupScreen
from gui.main_window import MainWindow


def _make_global_exception_handler(hardware_getter):
    """Build an exception hook that attempts an emergency hardware shutdown."""
    handling_exception = False

    def global_exception_handler(exctype, value, traceback):
        nonlocal handling_exception
        if handling_exception:
            try:
                sys.__excepthook__(exctype, value, traceback)
            finally:
                raise SystemExit(1)

        handling_exception = True
        print(
            f"\n[CRITICAL] Error no manejado detectado: "
            f"{exctype.__name__}: {value}"
        )

        safe_state_message = (
            "No se pudo ejecutar el apagado seguro porque "
            "la instancia de hardware no está disponible."
        )
        try:
            hardware = hardware_getter()
            if hardware is not None:
                errors = hardware.shutdown_state() or []
                if errors:
                    safe_state_message = (
                        "El apagado seguro terminó con errores:\n"
                        + "\n".join(str(error) for error in errors)
                    )
                else:
                    safe_state_message = (
                        "Se solicitó el estado seguro del hardware correctamente."
                    )
        except Exception as hardware_error:
            safe_state_message = (
                "No se pudo completar el apagado seguro del hardware:\n"
                f"{hardware_error}"
            )
            print(f"[CRITICAL] {safe_state_message}")

        try:
            error_message = (
                "Ocurrió un error inesperado en el sistema.\n\n"
                f"{safe_state_message}\n\n"
                f"Detalle del error:\n{exctype.__name__}: {value}"
            )
            QMessageBox.critical(
                None,
                "Falla Crítica de Sistema",
                error_message,
            )
        except Exception as gui_error:
            print(
                "[CRITICAL] No se pudo mostrar el cuadro de diálogo de Qt: "
                f"{gui_error}"
            )

        try:
            sys.__excepthook__(exctype, value, traceback)
        finally:
            raise SystemExit(1)

    return global_exception_handler


def main():
    """Inicializa y ejecuta la aplicación."""

    # =========================================================================
    # Aplicación Qt
    # =========================================================================

    app = QApplication(sys.argv)

    hardware = None
    sys.excepthook = _make_global_exception_handler(lambda: hardware)

    settings_manager = SettingsManager(app)

    # =========================================================================
    # Hardware
    # =========================================================================
    # Se crea una única instancia de Hardware para toda la aplicación.
    # Esta misma instancia será utilizada por:
    # - PowerController para monitorear las señales físicas de alimentación.
    # - StartupSequence para ejecutar el pre-encendido.
    # - MainWindow y sus controladores/secuencias durante la operación.
    if USE_MOCK_HARDWARE:
        hardware = MockHardware()
    else:
        hardware = Hardware()

    if USE_MOCK_HARDWARE:
        simulation_controller = SimulationController(
            hardware=hardware,
        )

        app.installEventFilter(
            simulation_controller
        )

    # =========================================================================
    # Control de alimentación
    # =========================================================================

    power_controller = PowerController(
        hardware=hardware,
    )

    # =========================================================================
    # Secuencia de pre-encendido
    # =========================================================================

    startup_sequence = StartupSequence(
        hardware=hardware,
        initialize_analog=not USE_MOCK_HARDWARE,
    )

    # =========================================================================
    # Controlador de arranque
    # =========================================================================

    startup_controller = StartupController(
        startup_sequence=startup_sequence,
    )

    # =========================================================================
    # Secuencias funcionales
    # =========================================================================

    door_sequence = DoorSequence(
        hardware=hardware,
    )

    soft_vacuum_sequence = SoftVacuumSequence(
        hardware=hardware,
    )

    main_vacuum_sequence = MainVacuumSequence(
        hardware=hardware,
    )

    vent_sequence = VentSequence(
        hardware=hardware,
    )

    # =========================================================================
    # Secuencia de apagado seguro
    # =========================================================================

    shutdown_sequence = ShutdownSequence(
        hardware=hardware,
        soft_vacuum_sequence=soft_vacuum_sequence,
        main_vacuum_sequence=main_vacuum_sequence,
        vent_sequence=vent_sequence,
    )

    shutdown_controller = ShutdownController(
        shutdown_sequence=shutdown_sequence,
    )

    # =========================================================================
    # Interfaces gráficas
    # =========================================================================

    startup_screen = StartupScreen()
    startup_screen.update_texts()
    settings_manager.language_changed.connect(startup_screen.update_texts)

    main_window = MainWindow(
        hardware=hardware,
        door_sequence=door_sequence,
        soft_vacuum_sequence=soft_vacuum_sequence,
        main_vacuum_sequence=main_vacuum_sequence,
        vent_sequence=vent_sequence,
        settings_manager=settings_manager,
    )

    # =========================================================================
    # Controlador general de la aplicación
    # =========================================================================

    application_controller = ApplicationController(
        startup_controller=startup_controller,
        power_controller=power_controller,
        shutdown_controller=shutdown_controller,
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
