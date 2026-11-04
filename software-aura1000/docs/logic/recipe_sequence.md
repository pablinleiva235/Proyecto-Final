# Ejecución automática de recetas (`recipe_sequence.py`)

`RecipeSequence` coordina puerta, secuencias de vacío/venteo, MFC, throttle, controladores de presión/temperatura y proceso. No realiza el sondeo de hardware por sí misma: recibe muestras/eventos por métodos y coordina respuestas de forma asíncrona en el loop de Qt.

## Estados y eventos de interfaz

`RecipeState` representa espera/carga y retiro de oblea, cierre/verificación de puerta, inicio de vacíos, bombeo a presión base, posicionamiento de throttle, flujo de gas, control de presión y temperatura, plasma, parada, venteo, completada o error.

Emite `state_changed(object)`, solicitudes de confirmación de carga/retiro (`wafer_confirmation_requested`, `wafer_removal_confirmation_requested`), `error_raised(str)`, `rf_finished()` y `finished(bool, str)`. `NormalOperationScreen` presenta las confirmaciones y `MainWindow` conecta los eventos a los controladores.

## Recorrido normal

1. `start(recipe)` rechaza otra receta activa, puerta no cerrada, venteo/vacíos activos o entradas que no confirmen puerta cerrada (`DOOR_OPEN=False`, `DOOR_CLOSE=True`). Abre logs de eventos y datos, activa/verifica `DRIVER_ENABLE`, abre la puerta y solicita confirmar la oblea.
2. Tras confirmación, ordena cerrar la puerta y espera lecturas de cierre; inicia Soft Vacuum y Main Vacuum. Al confirmar vacío principal, apaga Soft Vacuum.
3. Lee `BARATRON` hasta alcanzar la presión base de receta. Lleva throttle a posición de reposo antes de configurar los gases.
4. Ajusta MFC1/O2 y MFC2/N2, abre `MFC1_OPEN`/`MFC2_OPEN` y comienza control de presión con la consigna de receta.
5. Al alcanzar la consigna de presión, continúa el control de temperatura y procesos térmicos/RF conforme a los controladores. Un timer limita el tiempo máximo de RF configurado en la receta.
6. Durante la receta recibe `EOP`; por debajo de 2 V mientras corre plasma detiene RF e inicia cierre normal. También cierra al vencer el tiempo máximo de RF.
7. Detiene RF, temperatura, lámparas, MFC y presión; solicita retorno seguro de throttle, detiene vacíos e inicia venteo. Al completar ATM, devuelve throttle a reposo si corresponde y abre puerta; pide confirmar retiro de oblea, vuelve a cerrar y verifica entradas de puerta antes de finalizar.

Las transiciones dependen de eventos de presión/temperatura alcanzadas, muestras analógicas, cambios digitales de puerta/ATM, señales de los controladores y confirmaciones del operador. Las magnitudes y tiempos efectivos deben cotejarse con configuración/controladores y validarse con equipo.

## Señales y registros

- Digitales: `DRIVER_ENABLE`, `DOOR_OPEN_CMD`, `DOOR_CLOSE_CMD`, entradas `DOOR_OPEN`/`DOOR_CLOSE`, `SOFT_START_CONTROL`, `MAIN_VACUUM_CONTROL`, `VENT_VALVE_CONTROL`, `MFC1_OPEN`, `MFC2_OPEN`, `RF_ON_CMD`, salidas de lámparas y pines del stepper/throttle.
- Analógicas: `BARATRON`, `CHAMBER_TEMP`, `MFC1_FLOW`, `MFC2_FLOW` y `EOP`; las salidas MFC son `MFC1_SETPOINT` y `MFC2_SETPOINT`.
- Registra eventos/acciones y salidas en log de receta, y una muestra por segundo de lecturas disponibles, posición throttle y plasma en log de proceso.

## Errores y cierre

Fallos de controlador, pérdida de interlock, lecturas críticas ausentes, errores de escritura o fallo de logging pueden hacer fallar la receta. El cierre intenta apagar RF/lámparas/MFC/presión, abrir throttle, detener vacíos y ventear; si falla el log de eventos o de datos, también aborta. Un fallo global de hardware puede cerrar el estado de receta sin emitir más comandos. `finished` informa éxito/error y mensaje; los indicadores `log_saved` y `data_log_saved` exponen resultado de persistencia.
