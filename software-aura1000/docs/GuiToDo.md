# Pendientes — Plasma Asher GUI

Este archivo registra tareas pendientes de la branch `gui-development`.

La intención es mantener visibles los próximos pasos y evitar perder decisiones de diseño entre sesiones de trabajo.

## Idioma y configuración

- [ ] Crear `LanguageManager` como fuente única del idioma activo.
- [ ] Soportar inicialmente Español e Inglés.
- [ ] Permitir cambiar el idioma sin reiniciar la aplicación.
- [ ] Crear `SettingsDialog`.
- [ ] Agregar al `SettingsDialog` el selector de idioma.
- [ ] Conectar `TopBarWidget.settings_requested` con la apertura de `SettingsDialog`.
- [ ] Refactorizar `strings.py` para soportar textos por idioma en lugar de constantes estáticas.
- [ ] Agregar un método común de actualización de textos (`update_texts()` o equivalente) en las pantallas y widgets que contengan texto visible.
- [ ] Actualizar dinámicamente los textos de `TopBarWidget`.
- [ ] Actualizar dinámicamente los textos de `WelcomeScreen`.
- [ ] Actualizar dinámicamente los textos de `LoginDialog`.
- [ ] Actualizar dinámicamente los textos de `MaintainerScreen`.
- [ ] Actualizar dinámicamente los textos de `SignalWidget`.
- [ ] Actualizar dinámicamente los textos de `StartupScreen`.
- [ ] Mover el tooltip actualmente hardcodeado del botón de configuración al sistema de traducciones.
- [ ] Definir si el idioma seleccionado debe persistir entre ejecuciones de la aplicación.

## TopBarWidget

- [x] Verificar visualmente fecha y hora en resolución fullscreen del equipo.
- [x] Verificar la actualización correcta del reloj.
- [ ] Evaluar reemplazar el carácter `⚙` por un recurso gráfico/icono propio si presenta problemas de renderizado en Windows 10.

## Secuencia de inicio

- [ ] Realizar una prueba completa y repetible de `StartupScreen → MainWindow` con hardware real.
- [ ] Incorporar progresivamente las señales de fallo que deban supervisarse durante el pre-encendido.
- [ ] Definir el comportamiento visual y lógico ante un fallo durante `WAITING_POWER`.
- [ ] Definir el comportamiento visual y lógico ante un fallo durante `STARTING`.
- [ ] Definir si el usuario podrá reintentar la secuencia desde `StartupScreen` después de un error.
- [ ] Revisar qué acciones de hardware deben ejecutarse para dejar el equipo en estado seguro si `StartupSequence` falla.
- [ ] Validar que `POWER_ON`, `FILAMENT_ENABLE` e inicialización analógica mantengan la misma secuencia física que la implementación original.

## MaintainerScreen y señales

- [ ] Escalar `MAINTAINER_SIGNALS` desde las cuatro señales de prueba al conjunto completo requerido.
- [ ] Revisar la distribución visual de las señales cuando se incorporen aproximadamente 42 señales.
- [ ] Definir agrupación por subsistemas si una única grilla resulta difícil de operar.
- [ ] Incorporar señales analógicas a la pantalla de mantenimiento.
- [ ] Diseñar un widget adecuado para señales analógicas y valores numéricos.
- [ ] Definir cómo mostrar errores de lectura/escritura en la GUI en lugar de únicamente imprimirlos en consola.

## SignalController y hardware

- [ ] Evaluar el tiempo real de ejecución de `digital_read()` y `digital_set()`.
- [ ] Si las llamadas bloquean perceptiblemente la GUI, mover el acceso al hardware a un `QThread`/worker.
- [ ] Revisar si la lectura posterior de una salida representa el estado físico real o solamente el latch/comando escrito.
- [ ] Diferenciar, cuando corresponda, entre estado comandado y feedback físico.
- [ ] Sustituir los `print()` temporales de diagnóstico por `logging`.
- [ ] Definir niveles y formato de logging para GUI, controladores y hardware.

## Configuración y arquitectura de hardware

- [ ] Revisar la dependencia entre `digital_signals.py` y `dio_driver.py`.
- [ ] Evaluar separar las constantes pasivas del driver para que importar configuración no cargue innecesariamente la DLL.
- [ ] Mantener `digital_signals.py` como única fuente de verdad de puerto, bit, dirección y estado activo.
- [ ] Evitar duplicar información técnica de señales en archivos específicos de la GUI.

## Limpieza y mantenimiento

- [ ] Limpiar imports y código legado que ya no se utilicen después de validar completamente el nuevo flujo de startup.
- [ ] Eliminar código temporal de `MockHardware` de los caminos de producción, manteniéndolo disponible únicamente para pruebas.
- [ ] Revisar comentarios y documentación después de estabilizar el Hito 3 y la secuencia de startup.
- [ ] Mantener ADR-009 y ADR-011 como referencia al agregar nuevos componentes gráficos y nuevas selecciones de señales.

## Pruebas pendientes

- [ ] Repetir prueba física de `POWER_ON_SWITCH`.
- [ ] Repetir prueba física de `SYS_POWER`.
- [ ] Probar individualmente las salidas reales desde `MaintainerScreen` en condiciones seguras.
- [ ] Probar login de mantenimiento después de completar la secuencia de startup.
- [ ] Probar navegación completa después del startup.
- [ ] Probar salida de la aplicación desde distintas pantallas.
- [ ] Probar errores controlados de hardware sin que la GUI se cierre inesperadamente.
- [ ] Probar el flujo completo en Windows 10 con el entorno Python de 32 bits destinado al equipo.