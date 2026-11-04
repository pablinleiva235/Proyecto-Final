# Pendientes de GUI y validación

Este listado se contrastó con el código del repositorio. “Implementado en código” no significa probado con hardware real. Las tareas de banco requieren verificación del operador y registro de resultados.

## Implementado en código (no implica validación física)

- [x] Diálogo de ajustes con selección de idioma y tema; propagación de cambios a componentes conectados.
- [x] `TopBarWidget` con reloj, botón de ajustes y solicitud de salida.
- [x] Pantallas de bienvenida, mantenimiento, estadísticas y operación normal.
- [x] Acceso al modo mantenimiento con `LoginDialog`.
- [x] Listado digital de mantenimiento derivado de `DIGITALSIGNALS`, con distinción entre controles manuales y salidas controladas por secuencia.
- [x] Readouts analógicos de mantenimiento y operación normal.
- [x] Presentación de errores de lectura y estados de proceso.
- [x] Simulación seleccionable mediante `USE_MOCK_HARDWARE`.

## Pendiente de validación con hardware

- [ ] Ensayar encendido físico (`POWER_ON_SWITCH`, `POWER_ON`, `FILAMENT_ENABLE`) y confirmar el tiempo de precalentamiento requerido. El valor actual configurado es 3 s; los comentarios históricos mencionan otros tiempos.
- [ ] Ensayar apagado físico (`SYS_POWER`), cierre normal y emergencia; revisar los resultados del estado seguro y el registro generado.
- [ ] Confirmar lecturas digitales y analógicas contra instrumentos y cableado, incluyendo polaridades, unidades, escalas y realimentación de salidas.
- [ ] Validar secuencias de puerta, vacío, venteo, throttle, MFC, lámparas, plasma, presión y temperatura en condiciones de operación aprobadas.
- [ ] Validar login, navegación, idioma/tema, recetas, confirmaciones y gráficos a resolución de pantalla final.
- [ ] Ejecutar las pruebas automatizadas en el entorno objetivo Python/PyQt/Universal Library.

## Mejoras de desarrollo por priorizar

- [ ] Sustituir `print()` de diagnóstico por logging con niveles y rotación consistentes.
- [ ] Evaluar la latencia de llamadas de hardware en el loop Qt; mover I/O a worker/thread solo si la medición muestra bloqueo relevante.
- [ ] Aclarar en la UI cuándo una lectura de salida es lectura de pin/latch y cuándo hay feedback físico independiente.
- [ ] Revisar el alcance de los controles de mantenimiento y agrupar señales por subsistema si la grilla completa dificulta su uso.
- [ ] Decidir si los artefactos `pyqt_gui.py` y `pyqt_gui.ui` se conservarán como legado o se eliminarán en una limpieza futura.

Las casillas verificables por código se marcaron completadas; los ensayos de hardware permanecen abiertos porque no pueden inferirse del código ni de las pruebas simuladas.
