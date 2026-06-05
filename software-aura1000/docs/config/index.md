# Capa de configuracion de señales (`/config`)

En esta sección se listan en diccionarios las señales digitales y analogicas usadas para controlar el Asher, especificando caracteristicas de cada una de ellas, para luego manejarlas facilmente simplemente con sus nombres y sus caracteristicas y abstraernos del bajo nivel de las mismas

## Módulos Disponibles

* **[Digitales (digital_signals.py)](digital_signals.md):** Contiene un diccionario con el listado de todas la señales digitales definiendo su puerto, bit, direccion, estado activo y estado inicial
* **[Analogicas (analog_signals.py)](analog_signals.md):** Dividido en 3 diccionarios, uno para entradas analogicas especificando canal y rango de tension, otro para salidas analogicas especificando canal y rango de tension y un ultimo para la termocupla especificando el canal usado