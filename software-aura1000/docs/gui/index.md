# Capa de Interfaz Grafica (`/gui`)

Contiene todo lo relacionado con el entorno visual del operador. Aquí se encuentra el archivo `.ui` de diseño, el script generado por el compilador `pyuic5`, y fundamentalmente el **Orquestador Principal (`main_window.py`)**, encargado de correr el programa principal y administrar la máquina de estados mediante llamadas a funciones de alto nivel de la class Hardware de la carpeta services.

---

## Módulos Disponibles

* **[Codigo de interfaz grafica (pyqt_gui.py)](pyqt_gui.md):** Es el codigo en python generado desde el PyQt5Designer, contiene a la clase *Ui_MainWindow*, cada vez que se hagan modificaciones a la interfaz, este codigo debe pegarse en este archivo

* **[Ventana de arranque y ejecucion de programa (main_window.py)](main_window.md):** Contiene a la clase *MainWindow* que vincula la UI de PyQt5 *Ui_MainWindow* con el hardware, gestionando la maquina de estados, modulo de timers para lectura de entradas y cierre de la UI llevando equipo a estado seguro
