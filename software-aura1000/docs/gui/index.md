# Capa de Interfaz Gráfica (`/gui`)

Contiene todo lo relacionado con el entorno visual del operador. En esta capa se aloja el archivo de diseño original de Qt Designer, el script generado por su compilador, y el **Coordinador de la Interfaz (`main_window.py`)**, encargado de gestionar la máquina de estados principal a alto nivel y de orquestar el flujo visual de la pantalla (páginas y solapas del operador) delegando la lógica pesada de tiempos e I/O a la capa de control correspondiente.

---

## Módulos Disponibles

* **[Código de interfaz gráfica (pyqt_gui.py)](pyqt_gui.md):** Es el código en Python generado automáticamente por el compilador `pyuic5` a partir del diseño de Qt Designer. Contiene la clase `Ui_MainWindow`. Cada vez que se realicen modificaciones visuales en la interfaz, el archivo compilado resultante debe reemplazar el contenido de este módulo. **No se debe escribir código manual aquí.**

* **[Coordinador de ventana y estados (main_window.py)](main_window.md):** El módulo `main_window.py` constituye el componente de interfaz gráfica de usuario (GUI) y el núcleo coordinador de estados del sistema. Implementa la clase `MainWindow`, la cual hereda de `QtWidgets.QMainWindow`. Vinculan la interfaz autogenerada de PyQt5 con el servicio de hardware y delegando la ejecución secuencial de los timers y la lógica I/O a los administradores externos de la carpeta `/logic`.
