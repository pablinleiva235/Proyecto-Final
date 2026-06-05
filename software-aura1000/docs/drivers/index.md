# Capa de Drivers de Hardware (`/drivers`)

Esta sección agrupa los módulos encargados de interactuar directamente con las placas de adquisición de datos mediante llamadas de bajo nivel a funciones de la Universal Library cbw32.dll.

## Módulos Disponibles

* **[Analógico (analog_driver.py)](analogico.md):** Encargado de la comunicación con la placa **USB-2527**. Gestiona lecturas de canales analogicos, escrituras analogicas usando el DAC y lectura de termocupla
* **[Digital (dio_driver.py)](digital.md):** Encargado de la comunicación con la placa **USBDIO96H**. Gestiona lecturas y escrituras de señales digitales

