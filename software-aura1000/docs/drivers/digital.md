# `dio_driver.py`

Este módulo implementa la abstracción de bajo nivel para la placa de adquisición digital **USBDIO96H**, utilizando `ctypes` para interactuar con las funciones nativas de la biblioteca de comunicación `cbw32.dll`.

!!! info "Carga de librería cbw32.dll"
    ```python
    cbw = ctypes.windll.LoadLibrary(r"C:\Program Files (x86)\Measurement Computing\DAQ\cbw32.dll")
    ```

---

## <span style="color: #2196F3;">Puertos y Constantes de Configuración</span>

La placa **USBDIO96H** dispone de múltiples puertos mapeados bajo las constantes nativas de la *Universal Library*. Estos identificadores son utilizados para direccionar la lógica de las electroválvulas y sensores del equipo:

* **Dirección de E/S:** `DIGITALOUT` (1) y `DIGITALIN` (2).
* **Bloques de Puertos:** 
    * **First:** `FIRSTPORTA` (10), `FIRSTPORTB` (11), `FIRSTPORTCL` (12), `FIRSTPORTCH` (13).
    * **Second:** `SECONDPORTA` (14), `SECONDPORTB` (15), `SECONDPORTCL` (16), `SECONDPORTCH` (17).
    * **Third:** `THIRDPORTA` (18), `THIRDPORTB` (19), `THIRDPORTCL` (20), `THIRDPORTCH` (21).
    * **Fourth:** `FOURTHPORTA` (22), `FOURTHPORTB` (23), `FOURTHPORTCL` (24), `FOURTHPORTCH` (25).

---

## <span style="color: #2196F3;">Funciones de Control API (Python)</span>

Estas funciones exponen una interfaz limpia en Python para configurar la dirección de los registros y conmutar o leer bits individuales en el hardware de control del Asher.

??? note "Configuración de Puerto: `config_port(board, port, direction)`"
    Establece si un bloque de puertos específico de la placa operará como entrada o salida digital utilizando el comando nativo `cbDConfigPort`.

    ```python
    def config_port(board, port, direction):  
        return cbw.cbDConfigPort(board, port, direction)
    ```

??? note "Escritura de Bit Individual: `write_bit(board, port, bit, value)`"
    Modifica de manera directa el estado lógico (`0` o `1`) de un pin específico mediante `cbDBitOut`. Se utiliza principalmente para activar/desactivar relays, controladores de flujo y válvulas de vacío o purga.

    ```python
    def write_bit(board, port, bit, value):
        cbw.cbDBitOut(board, port, bit, value)
    ```

??? note "Lectura de Bit Individual: `read_bit(board, port_base, bit_offset)`"
    Consulta el estado lógico actual de una entrada digital mediante `cbDBitIn`. Pasa una variable de tipo `c_short` por referencia mediante `ctypes.byref()` para almacenar el valor binario del bit leído del sensor (ej. sensores de cámara o estado de vacío).

    ```python
    def read_bit(board, port_base, bit_offset):
        value = ctypes.c_short(0)  
        cbw.cbDBitIn(board, port_base, bit_offset, ctypes.byref(value))
        return value.value
    ```