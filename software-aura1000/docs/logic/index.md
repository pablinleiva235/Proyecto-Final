# Capa de Lógica Intermedia y Control Secuencial (`/logic`)

Aloja la inteligencia operacional, las rutinas de tiempo y los procesos algorítmicos secuenciales del sistema. Esta capa actúa como un puente intermedio de control: recibe la referencia de la interfaz de usuario (`MainWindow`) y de la capa de servicios (`Hardware`) para interactuar con los periféricos en tiempo real, aislando las tareas pesadas de pooling e hilos de ejecución del hilo principal de la GUI.

---

## Módulos Disponibles

* **[Administrador central de Timers y lazo de lectura de entradas (timers_io.py)](timers_io.md):** Funciona como el "corazón" síncrono del software. Centraliza la declaración de todos los temporizadores del sistema y ejecuta de manera continua el lazo periódico de 100 ms para la lectura de entradas digitales críticas. Filtra las acciones de hardware dependiendo del estado activo del equipo y notifica a la ventana las solicitudes de cambio de estado.

* **[Secuencia de Encendido (pre_encendido.py)](pre_encendido.md):** Implementa el algoritmo de control para el encendido del plasma asher. Gobierna de forma directa el enclavamiento eléctrico por software, inicializa la USB-2527, comuta el estado de las etiquetas en pantalla y manipula linealmente la barra de progreso de 10 segundos para garantizar la estabilización térmica y eléctrica del equipo antes de habilitar la operación.