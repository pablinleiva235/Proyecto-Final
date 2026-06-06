# Capa de control de hardware de alto nivel (`/services`)

Contiene la capa que hace de intermediaria entre la GUI y las funciones de bajo nivel del hardware, y un archivo para enumerar los estados de la maquina de estados:


---

## Módulos Disponibles

* **[Class Hardware (hardware.py)](hardware.md):** Clase que inicializa las placas y contiene metodos de alto nivel que llaman a las funciones de bajo nivel de los drivers para que las pueda usar la GUI mediante un nivel de abstraccion
* **[Enumeracion de estados (system_state.py)](system_state.md):** Definición de la enumeración de estados (Enum)