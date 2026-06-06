# Capa de configuracion de señales (`/config`)

Aloja diccionarios de Python que actúan como "tablas de verdad" o mapas físicos. Centraliza los nombres lógicos de las señales (como `PURGE_VALVE_CONTROL` o `BARATRON`) asociándolos a sus puertos y bits reales. Esto permite realizar cambios en el cableado eléctrico del equipo modificando un solo archivo, sin alterar el código fuente de los drivers o la GUI.

---

## Módulos Disponibles

* **[Digitales (digital_signals.py)](digital_signals.md):** Contiene un diccionario con el listado de todas la señales digitales definiendo su puerto, bit, direccion, estado activo y estado inicial
* **[Analogicas (analog_signals.py)](analog_signals.md):** Dividido en 3 diccionarios, uno para entradas analogicas especificando canal y rango de tension, otro para salidas analogicas especificando canal y rango de tension y un ultimo para la termocupla especificando el canal usado