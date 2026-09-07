# Capa de Lógica Intermedia y Control Secuencial (`/logic`)

Aloja la inteligencia operacional, las rutinas de tiempo y los procesos algorítmicos secuenciales del sistema. Esta capa actúa como un puente intermedio de control: recibe la referencia de la interfaz de usuario (`MainWindow`) y de la capa de servicios (`Hardware`) para interactuar con los periféricos en tiempo real, aislando las tareas pesadas de pooling e hilos de ejecución del hilo principal de la GUI.

---

## Módulos Disponibles

* **[Secuencia de Encendido (pre_encendido.py)](pre_encendido.md):** Implementa el algoritmo de control para el encendido del plasma asher. Gobierna de forma directa el enclavamiento eléctrico por software, inicializa la USB-2527, comuta el estado de las etiquetas en pantalla y manipula linealmente la barra de progreso de 10 segundos para garantizar la estabilización térmica y eléctrica del equipo antes de habilitar la operación.

* **[Proceso en modo mantenimiento (maintenance_process.py)](maintenance_process.md):** Este modulo agrupa metodos para poder ir probando mediante la interfaz, de manera secuencial, los distintos modulos que utiliza el proceso. La idea es que quede en el modo mantenimiento para poder hacer un proceso de forma no automatica y probar que los modulos esten funcionando correctamente

* **[Control de valvula throttle (throttle_test.py)](throttle_test.md):** Este modulo tiene la clase ThrottleController con metodos integrados en el Menu Throttle de la UI para poder controlar la misma de forma manual, girando el motor paso a paso continuamente, en full o half step, en ambas direcciones, moverlo de a cantidad de pasos deseados y ajustar el setpoint de presion mediante el sistema de control

* **[Administrador central de Timers y lazo de lectura de entradas (timers_io.py)](timers_io.md):** Funciona como el "corazón" síncrono del software. Centraliza la declaración de todos los temporizadores del sistema y ejecuta de manera continua el lazo periódico de 100 ms para la lectura de entradas digitales críticas. Filtra las acciones de hardware dependiendo del estado activo del equipo y notifica a la ventana las solicitudes de cambio de estado.

* **[Actualizacion de lecturas analogicas (analog_update.py)](analog_update.md):** Este modulo tiene los metodos llamados en el timer general cada 100ms de lectura de señales analogicas (presion, temperatura, flujo de MFCs y señal del EOP) y actualizacion de los displays de la interfaz

* **[Chequeo de fallas de lampara y plasma (process_faults.py)](process_faults.md):** Este modulo tiene el metodo llamado en el timer general cada 100ms para leer las señales de falla de lamparas, magnetron y plasma, dando aviso al usuario si ocurrio alguna, encendiendo el indicador de alarma y apagando estos modulos de potencia


