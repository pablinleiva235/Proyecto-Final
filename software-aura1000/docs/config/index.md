# Capa de configuracion de señales (`/config`)

`config/` contiene los mapas técnicos consumidos por `Hardware`; la selección de señales que aparecen en Mantenimiento se deriva en `config_gui/maintainer_signals.py`.

Aloja diccionarios de Python que actúan como "tablas de verdad" o mapas físicos. Centraliza los nombres lógicos de las señales (como `PURGE_VALVE_CONTROL` o `BARATRON`) asociándolos a sus puertos y bits reales. Esto permite realizar cambios en el cableado eléctrico del equipo modificando un solo archivo, sin alterar el código fuente de los drivers o la GUI.

---

## Módulos Disponibles

* **[Digitales (digital_signals.py)](digital_signals.md):** Contiene un diccionario con el listado de todas la señales digitales definiendo su puerto, bit, direccion, estado activo y estado inicial
* **[Analogicas (analog_signals.py)](analog_signals.md):** Dividido en 3 diccionarios, uno para entradas analogicas especificando canal y rango de tension, otro para salidas analogicas especificando canal y rango de tension y un ultimo para la termocupla especificando el canal usado

La GUI monitorea un subconjunto analógico (`BARATRON`, `CHAMBER_TEMP`, `MFC1_FLOW`, `MFC2_FLOW`, `EOP`) aunque el mapa define además canales para MFC3/MFC4. En digital, la pantalla de mantenimiento deriva su listado de todas las señales configuradas. Ver [integración GUI](../gui/integracion.md).
