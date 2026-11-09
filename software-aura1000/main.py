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

from config_gui.settings_manager import SettingsManager
from gui.startup_mode_dialog import StartupModeDialog


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


def _build_runtime(app, settings_manager, simulated):
    """Build the selected backend after the operator confirms the mode."""
    if simulated:
        from tests.mockScripts.mock_hardware import MockHardware
        from tests.mockScripts.controllers.simulation_controller import SimulationController

        hardware = MockHardware()
        simulation_controller = SimulationController(hardware=hardware)
        app.installEventFilter(simulation_controller)
    else:
        from services.hardware import Hardware

        hardware = Hardware()
        simulation_controller = None

    from logic.startup_sequence import StartupSequence
    from logic.door_sequence import DoorSequence
    from logic.soft_vacuum_sequence import SoftVacuumSequence
    from logic.main_vacuum_sequence import MainVacuumSequence
    from logic.vent_sequence import VentSequence
    from logic.shutdown_sequence import ShutdownSequence

    from controllers.power_controller import PowerController
    from controllers.startup_controller import StartupController
    from controllers.shutdown_controller import ShutdownController
    from gui.startup_screen import StartupScreen
    from gui.main_window import MainWindow

    startup_screen = StartupScreen()
    startup_screen.update_texts()
    settings_manager.language_changed.connect(startup_screen.update_texts)

    power_controller = PowerController(hardware=hardware)
    startup_sequence = StartupSequence(
        hardware=hardware,
        initialize_analog=not simulated,
        duration_ms=(
            StartupSequence.SIMULATED_STARTUP_DURATION_MS
            if simulated
            else StartupSequence.STARTUP_DURATION_MS
        ),
    )
    startup_controller = StartupController(startup_sequence=startup_sequence)
    door_sequence = DoorSequence(hardware=hardware)
    soft_vacuum_sequence = SoftVacuumSequence(hardware=hardware)
    main_vacuum_sequence = MainVacuumSequence(hardware=hardware)
    vent_sequence = VentSequence(hardware=hardware)
    shutdown_sequence = ShutdownSequence(
        hardware=hardware,
        soft_vacuum_sequence=soft_vacuum_sequence,
        main_vacuum_sequence=main_vacuum_sequence,
        vent_sequence=vent_sequence,
    )
    shutdown_controller = ShutdownController(shutdown_sequence=shutdown_sequence)
    main_window = MainWindow(
        hardware=hardware,
        door_sequence=door_sequence,
        soft_vacuum_sequence=soft_vacuum_sequence,
        main_vacuum_sequence=main_vacuum_sequence,
        vent_sequence=vent_sequence,
        settings_manager=settings_manager,
        use_mock_hardware=simulated,
    )

    from controllers.application_controller import ApplicationController

    application_controller = ApplicationController(
        startup_controller=startup_controller,
        power_controller=power_controller,
        shutdown_controller=shutdown_controller,
        startup_screen=startup_screen,
        main_window=main_window,
        simulated=simulated,
    )
    # Keep the event-filter wrapper alive for the lifetime of the application.
    application_controller._simulation_controller = simulation_controller
    return hardware, application_controller


def main():
    """Inicializa y ejecuta la aplicación."""

    # =========================================================================
    # Aplicación Qt
    # =========================================================================

    app = QApplication(sys.argv)

    settings_manager = SettingsManager(app)
    mode_dialog = StartupModeDialog()
    if mode_dialog.exec_() != StartupModeDialog.Accepted:
        return 0

    hardware_holder = {"value": None}
    sys.excepthook = _make_global_exception_handler(
        lambda: hardware_holder["value"]
    )

    simulated = mode_dialog.simulation_selected
    try:
        hardware, application_controller = _build_runtime(
            app,
            settings_manager,
            simulated=simulated,
        )
    except Exception as error:
        print(f"[CRITICAL] No se pudo inicializar el modo seleccionado: {error}")
        QMessageBox.critical(
            None,
            "Error de inicio",
            f"No se pudo inicializar el hardware del modo elegido.\n\n{error}",
        )
        return 1

    hardware_holder["value"] = hardware
    application_controller.start()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
