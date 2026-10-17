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


def main():
    """Inicializa y ejecuta la aplicación."""

    # =========================================================================
    # Aplicación Qt
    # =========================================================================

    app = QApplication(sys.argv)

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
