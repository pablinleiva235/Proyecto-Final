# Mapa de Señales Digitales (`digital_signals.py`)

Este módulo centraliza la asignación física de pines de la placa de adquisición **USBDIO96H** asignada al control del equipo. Define los puertos, bits, direcciones de E/S y estados lógicos activo e inicial para cada señal

---

## <span style="color: #2196F3;">Variables de Estado Lógico</span>

Para independizar el código del hardware y evitar confusiones con la lógica invertida de los integrados, se estandarizan las siguientes constantes globales:

* **`ACTIVE = True`**
* **`INACTIVE = False`**

---

## <span style="color: #2196F3;">Estructura del Diccionario General (`DIGITALSIGNALS`)</span>

El diccionario indexa las señales mediante un identificador en formato `string` que apunta a un mapeo de cinco parámetros clave: `port` (registro físico), `bit` (pin 0-7), `dir` (`IN`/`OUT`), `active_state` (estado de disparo lógico) e `initial_state` (inicialización de reposo en el arranque del software).

A continuación, se muestra un fragmento del diccionario:

??? note "Ver fragmento del diccionario DIGITALSIGNALS"
    ```python
    from drivers import dio_driver as dio

    DIGITALSIGNALS = {
        # --------- SEÑALES SECONDPORTA: P1-1 a P1-8 / SALIDAS -------------
        "PURGE_VALVE_CONTROL":   {"port": dio.SECONDPORTA, "bit": 7, "dir": "OUT", "active_state": 1, "initial_state": 0},
        "VENT_VALVE_CONTROL":    {"port": dio.SECONDPORTA, "bit": 6, "dir": "OUT", "active_state": 1, "initial_state": 0},
        "MAIN_VACUUM_CONTROL":   {"port": dio.SECONDPORTA, "bit": 5, "dir": "OUT", "active_state": 1, "initial_state": 0},
        "ALARM_INDICATION":      {"port": dio.SECONDPORTA, "bit": 4, "dir": "OUT", "active_state": 1, "initial_state": 0},
        "MFC4_OPEN":             {"port": dio.SECONDPORTA, "bit": 3, "dir": "OUT", "active_state": 0, "initial_state": 1},
        "MFC1_OPEN":             {"port": dio.SECONDPORTA, "bit": 0, "dir": "OUT", "active_state": 0, "initial_state": 1},
    }
    ```