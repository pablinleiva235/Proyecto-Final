# Capa de Drivers de Hardware (`/drivers`)

Contiene la lógica encargada de realizar llamadas dinámicas a la API de C de la *Universal Library* (`cbw32.dll`) utilizando `ctypes`. Convierte los tipos de datos de Python a estructuras de bajo nivel para interactuar con las placas **USB-2527** y **USBDIO96H**.

---

## Módulos Disponibles

* **[Analógico (analog_driver.py)](analogico.md):** Encargado de la comunicación con la placa **USB-2527**. Gestiona lecturas de canales analógicos, escrituras analógicas usando el DAC y lectura de termocupla.
* **[Digital (dio_driver.py)](digital.md):** Encargado de la comunicación con la placa **USBDIO96H**. Gestiona lecturas y escrituras de señales digitales.

---

## Interfaz con la DLL Nativa (`ctypes`)

Para poder utilizar las funciones de la librería de C (`cbw32.dll`) desde Python, se utiliza el módulo nativo `ctypes`. Esto requiere definir explícitamente el tipo de datos de los argumentos (`argtypes`) que espera cada función de la DLL para interactuar de forma segura con los registros del hardware.

???+ note "Ejemplo de mapeo de API (C a Python)"
    A continuación se muestra cómo se define la firma para la función de lectura digital de un bit (`cbDBitIn`), donde los parámetros enteros se mapean como `ctypes.c_int` y los retornos por referencia de memoria se configuran mediante punteros (`ctypes.POINTER`):

    ```python
    # ------------------ Lectura Digital ----------------------
    cbw.cbDBitIn.argtypes = [
        ctypes.c_int,                  # BoardNum (Número de placa)
        ctypes.c_int,                  # PortType (Tipo de puerto)
        ctypes.c_int,                  # BitNum (Número de bit)
        ctypes.POINTER(ctypes.c_short) # BitValue (Puntero al valor del bit)
    ]
    ```

