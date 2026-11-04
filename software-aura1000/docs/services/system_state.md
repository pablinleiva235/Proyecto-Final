# Estados de la aplicación

`services/system_state.py` define el enum legado `systemState` con `PRE_ENCENDIDO` y `MAIN_MENU`. La GUI actual no utiliza ese enum para gobernar el ciclo de vida: arranque y preparación se representan en `StartupState` (`controllers/startup_controller.py`) y la navegación se gestiona con nombres de pantalla en `config_gui/constants.py` y `NavigationController`.

El nombre `SystemState` y la descripción anterior de una transición interna de `MainWindow` estaban desactualizados. El archivo se conserva, pero no debe confundirse con el ciclo de estado real de aplicación. Ver [punto de entrada](../main.md) y [navegación GUI](../gui/main_window.md).
