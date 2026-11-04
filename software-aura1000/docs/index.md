# Revamping del Gasonics Aura 1000

Documentación técnica del software de control del Plasma Asher Aura 1000. Describe la estructura y el comportamiento implementado en el repositorio; la validación de cableado, tiempos de proceso y funcionamiento físico requiere ensayos con el equipo.

## Navegación

- [Arquitectura y estructura](arquitectura/carpetas.md)
- [Punto de entrada y ciclo de vida](main.md)
- [Configuración de señales](config/index.md)
- [Drivers de adquisición](drivers/index.md)
- [Interfaz gráfica](gui/index.md)
- [Controladores y secuencias](logic/index.md)
- [Servicios de hardware](services/index.md)
- [Decisiones arquitectónicas (registro histórico)](ADRs.md)
- [Pendientes de desarrollo y validación](GuiToDo.md)

## Capas principales

La aplicación usa Python y PyQt5. `main.py` construye la aplicación y sus dependencias; la carpeta `gui/` contiene pantallas y componentes; `controllers/` conecta eventos de interfaz con reglas de operación; `logic/` implementa secuencias asíncronas; `services/` abstrae hardware y registros; `config/` y `config_gui/` contienen mapas técnicos y configuración visual; `drivers/` envuelve la Universal Library.

La GUI no se comunica únicamente con un controlador genérico: `MainWindow` coordina diversos controladores de dominio y recibe una instancia de `Hardware`. Ver [flujo de aplicación](main.md) y [arquitectura de GUI](gui/index.md).
