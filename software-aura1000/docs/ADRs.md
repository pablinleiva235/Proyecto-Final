# Architecture Decision Records (ADR)

**Proyecto:** Revamping GUI – Plasma Asher AURA 1000

**Estado del documento:** Activo

Este documento registra las decisiones de arquitectura adoptadas durante el desarrollo del software. Cada ADR describe el contexto en el que se tomó una decisión, la decisión adoptada y sus consecuencias.

---

# ADR-001 – Arquitectura por Capas

## Estado

Aceptada.

## Contexto

La aplicación deberá controlar un Plasma Asher mediante una placa USB-DIO96H-50 utilizando las DLL proporcionadas por el fabricante.

El proyecto será desarrollado por dos personas:

* Un desarrollador será responsable de la interfaz gráfica.
* El otro desarrollador será responsable de la integración con el hardware.

Se requiere que ambos puedan trabajar de forma independiente sin generar dependencias innecesarias.

## Decisión

Se adopta una arquitectura por capas donde cada una posee una única responsabilidad.

La comunicación seguirá el siguiente flujo:

```text
GUI (PyQt5)
        │
        ▼
Machine Controller
        │
        ▼
Hardware Service
        │
        ▼
USB-DIO96H-50 Driver
        │
        ▼
DLL del fabricante (ctypes)
        │
        ▼
Hardware del Plasma Asher
```

## Responsabilidad de cada capa

### GUI

Responsable de la interacción con el usuario.

No conoce detalles del hardware.

Únicamente solicita acciones de alto nivel.

---

### Machine Controller

Interpreta las acciones solicitadas por la GUI.

Expone funciones relacionadas con el funcionamiento del equipo, por ejemplo:

* `set_power_on()`
* `set_main_vacuum_control()`
* `set_door_open_control()`

Esta capa traduce dichas acciones a operaciones del Hardware Service.

Además, en futuras versiones centralizará las reglas de seguridad (interlocks).

---

### Hardware Service

Expone funciones genéricas sobre señales digitales.

Ejemplos:

* `digital_set()`
* `digital_read()`
* `shutdown_state()`

No conoce la interfaz gráfica.

---

### Driver

Implementa la comunicación física con la placa USB-DIO96H-50 utilizando las DLL del fabricante mediante `ctypes`.

No conoce la lógica de negocio de la aplicación.

## Consecuencias

### Ventajas

* Bajo acoplamiento entre GUI y hardware.
* Posibilidad de desarrollar GUI y hardware en paralelo.
* Mayor facilidad para realizar pruebas.
* Cambios en el hardware no afectan a la GUI.

### Desventajas

* Se agrega una capa adicional (Machine Controller).
* Inicialmente existe una mayor cantidad de archivos.

Se considera que las ventajas superan ampliamente las desventajas.

---

# ADR-002 – Navegación mediante QStackedWidget

## Estado

Aceptada.

## Contexto

La aplicación funcionará como una HMI industrial ejecutándose en pantalla completa.

En el futuro contendrá múltiples pantallas:

* WelcomeScreen
* NormalOperationScreen
* MaintainerScreen
* StatisticsScreen
* Configuración
* Alarmas
* Recetas

Se desea evitar abrir y cerrar múltiples ventanas durante la ejecución.

## Decisión

La aplicación tendrá una única ventana principal denominada `MainWindow`.

Esta ventana permanecerá abierta durante toda la ejecución.

El contenido se administrará mediante un `QStackedWidget`.

La estructura será:

```text
MainWindow
      │
      ▼
QStackedWidget
      │
      ├── WelcomeScreen
      ├── MaintainerScreen
      ├── StatisticsScreen
      └── (Futuras pantallas)
```

Cada pantalla será un `QWidget` independiente.

La navegación consistirá únicamente en cambiar la página activa del `QStackedWidget`.

Las pantallas individuales no abrirán nuevas ventanas principales.

## Consecuencias

### Ventajas

* Experiencia de usuario continua.
* Mejor adaptación a una interfaz industrial.
* Navegación simple.
* Fácil incorporación de nuevas pantallas.
* Posibilidad de compartir elementos comunes (barra superior, estado del sistema, etc.).

### Desventajas

* La navegación deberá centralizarse en `MainWindow`.

Esta limitación es aceptable considerando los beneficios obtenidos.

---

# ADR-003 – Separación entre Acciones de Máquina y Señales de Hardware

## Estado

Aceptada.

## Contexto

El Hardware Service ya dispone de funciones genéricas como:

```python
digital_set(signal_name, state)
```

Sin embargo, permitir que la GUI invoque directamente estas funciones implica que conozca los nombres de las señales físicas del equipo.

Esto aumenta el acoplamiento entre la interfaz y el hardware.

## Decisión

Se adopta un enfoque híbrido.

La GUI únicamente invocará funciones del `MachineController`.

Ejemplo:

```python
machine_controller.set_power_on(True)
```

El `MachineController` será responsable de traducir esta acción a una o varias operaciones del Hardware Service.

Ejemplo:

```python
hardware.digital_set("POWER_ON", True)
```

En el futuro, si una acción requiere activar múltiples señales o seguir una secuencia determinada, únicamente será necesario modificar el Machine Controller.

La GUI permanecerá sin cambios.

## Consecuencias

### Ventajas

* La GUI no conoce nombres de señales.
* Mayor legibilidad del código.
* Facilita modificaciones futuras del hardware.
* Centraliza la lógica de funcionamiento de la máquina.

### Desventajas

* Incrementa ligeramente la cantidad de funciones del Machine Controller.

Se considera una decisión fundamental para mantener una arquitectura limpia y desacoplada.

---

# ADR-004 – Configuración Centralizada

## Estado

Aceptada.

## Contexto

La aplicación necesitará compartir configuraciones comunes entre múltiples módulos.

Ejemplos:

* Colores.
* Tipografías.
* Estilos.
* Constantes.
* Configuración general.
* Credenciales temporales.
* Definición de señales.

Duplicar esta información en distintos archivos dificultaría el mantenimiento.

## Decisión

Toda configuración global deberá centralizarse en el directorio `config/`.

La estructura inicial será:

```text
config/
│
├── settings.py
├── theme.py
├── signals.py
├── users.py
└── constants.py
```

Cada archivo será responsable de un único tipo de configuración.

## Consecuencias

### Ventajas

* Facilita el mantenimiento.
* Evita valores hardcodeados distribuidos por el proyecto.
* Permite modificar la apariencia completa de la aplicación desde un único lugar.
* Simplifica futuras ampliaciones, como múltiples temas visuales o distintos perfiles de usuario.

---

# ADR-005 – Una Responsabilidad por Archivo

## Estado

Aceptada.

## Contexto

El proyecto crecerá progresivamente incorporando nuevas pantallas y componentes.

Agrupar múltiples responsabilidades en un mismo archivo dificultaría su mantenimiento.

## Decisión

Cada archivo del proyecto deberá tener una única responsabilidad claramente definida.

Ejemplos:

* `welcome_window.py` → WelcomeScreen.
* `login_dialog.py` → LoginDialog.
* `maintainer_window.py` → MaintainerScreen.
* `module_widget.py` → Widget reutilizable de control.

No deberán coexistir múltiples ventanas principales dentro del mismo archivo.

## Consecuencias

### Ventajas

* Código más organizado.
* Archivos pequeños y fáciles de comprender.
* Menor probabilidad de conflictos al trabajar en equipo.
* Mayor facilidad para realizar pruebas unitarias y mantenimiento.

---

# ADR-006 – Comunicación mediante señales y slots

## Estado

Aceptada.

## Contexto

La aplicación utilizará una `MainWindow` que contendrá múltiples pantallas dentro de un `QStackedWidget`.

Cada pantalla será un `QWidget` independiente.

## Decisión

La comunicación entre pantallas y `MainWindow` se realizará mediante el mecanismo de **señales y slots** de Qt.

Las pantallas emitirán señales para informar eventos.

Ejemplo:

```python
maintainer_requested = pyqtSignal()
statistics_requested = pyqtSignal()
back_requested = pyqtSignal()
```

`MainWindow` será responsable de conectar esas señales con los métodos de navegación correspondientes.

Ejemplo:

```python
welcome_screen.maintainer_requested.connect(self.show_maintainer_screen)
```

## Consecuencias

### Ventajas

* Las pantallas no necesitan conocer a `MainWindow`.
* Se reduce el acoplamiento entre componentes.
* El código queda alineado con la filosofía de Qt.
* Las pantallas son más fáciles de reutilizar y probar.
* La navegación queda centralizada en `MainWindow`.

---

# ADR-007 – Confirmación de cierre de la aplicación

## Estado

Aceptada.

## Contexto

La aplicación controlará un equipo industrial y se ejecutará en pantalla completa durante toda su operación.

El usuario deberá poder cerrar la aplicación desde cualquier pantalla mediante un botón de salida ubicado en la interfaz.

Cerrar la aplicación accidentalmente podría interrumpir una tarea o, en futuras versiones, dejar el equipo en un estado inseguro.

## Decisión

El cierre de la aplicación será una operación controlada.

Cuando el usuario solicite cerrar la aplicación, el sistema mostrará un cuadro de diálogo de confirmación antes de finalizar la ejecución.

El mensaje será:

```text
¿Está seguro que desea salir de la aplicación?
```

El cuadro de diálogo ofrecerá las opciones:

* **Sí**
* **No**

El comportamiento será el siguiente:

* Si el usuario selecciona **Sí**, la aplicación continuará con el procedimiento de cierre.
* Si el usuario selecciona **No**, el diálogo se cerrará y la aplicación continuará ejecutándose.

En esta primera etapa del proyecto, el procedimiento de cierre consistirá únicamente en finalizar la aplicación.

En futuras versiones, el procedimiento deberá ampliarse para:

1. Llevar el Plasma Asher a un estado seguro.
2. Desactivar las salidas que correspondan.
3. Liberar los recursos utilizados por el hardware.
4. Cerrar la comunicación con la USB-DIO96H-50.
5. Finalizar la aplicación.

## Consecuencias

### Ventajas

* Evita cierres accidentales.
* Proporciona un comportamiento consistente desde cualquier pantalla.
* Deja preparado el mecanismo para implementar un procedimiento de apagado seguro en futuras versiones.
* Centraliza la lógica de cierre de la aplicación.

---

# ADR-008 – Barra superior persistente (TopBarWidget)

## Estado

Aceptada.

## Contexto

La aplicación utilizará una única `MainWindow` durante toda su ejecución, administrando las diferentes pantallas mediante un `QStackedWidget`.

Existen elementos de la interfaz que no pertenecen a una pantalla específica, sino a toda la aplicación. Algunos ejemplos son:

* Nombre del equipo.
* Estado de conexión con el hardware.
* Usuario autenticado.
* Fecha y hora.
* Estado general del sistema.
* Botón de salida.

Duplicar estos elementos en cada pantalla incrementaría el mantenimiento y el acoplamiento entre componentes.

## Decisión

Se implementará un widget denominado `TopBarWidget`, cuya responsabilidad será representar todos los elementos globales de la aplicación.

`TopBarWidget` será creado por `MainWindow` y permanecerá visible durante toda la ejecución del programa.

La estructura general de la interfaz será:

```text
MainWindow
│
├── TopBarWidget
│
└── QStackedWidget
    ├── WelcomeScreen
    ├── MaintainerScreen
    ├── StatisticsScreen
    └── Futuras pantallas
```

Las pantallas contenidas en el `QStackedWidget` no conocerán la existencia de la barra superior ni deberán interactuar directamente con ella.

Toda comunicación entre la barra superior, las pantallas y el resto de la aplicación se realizará mediante señales y slots administrados por `MainWindow`.

## Implementación inicial

En el Hito 1, `TopBarWidget` contendrá únicamente:

* Nombre de la aplicación.
* Botón **Exit**.

En versiones posteriores se incorporarán progresivamente nuevos elementos, entre ellos:

* Usuario autenticado.
* Estado de conexión con el hardware.
* Fecha y hora.
* Indicadores de estado del equipo.
* Alarmas activas.
* Otros elementos de información global.

## Consecuencias

### Ventajas

* Centraliza los elementos comunes de la interfaz.
* Evita duplicación de código entre pantallas.
* Mantiene una apariencia consistente durante toda la ejecución.
* Facilita la incorporación de nuevas funcionalidades sin modificar las pantallas existentes.
* Sigue el principio de responsabilidad única, separando claramente la navegación, el contenido y los elementos globales de la aplicación.

---

# ADR-009 – Estructura estándar para las clases de la interfaz gráfica

## Estado

Aceptada.

## Contexto

El proyecto estará compuesto por múltiples clases de PyQt5, entre ellas:

* MainWindow
* TopBarWidget
* WelcomeScreen
* LoginDialog
* MaintainerScreen
* ModuleWidget
* Futuras pantallas y widgets personalizados

A medida que el proyecto crezca, será importante que todas las clases compartan una estructura similar para facilitar su lectura, mantenimiento y evolución.

## Decisión

Todas las clases que representen componentes gráficos de la aplicación deberán seguir una estructura común basada en tres etapas claramente diferenciadas:

1. Creación de los componentes gráficos.
2. Construcción del layout.
3. Conexión de señales y slots.

El constructor (`__init__`) deberá contener únicamente las llamadas necesarias para inicializar estas etapas.

La estructura general será la siguiente:

```python
class ExampleWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.create_widgets()
        self.setup_layout()
        self.connect_signals()
```

Cada método tendrá una única responsabilidad.

### `create_widgets()`

Será responsable de crear e inicializar todos los widgets pertenecientes a la clase.

Ejemplos:

* `QLabel`
* `QPushButton`
* `QLineEdit`
* `QStackedWidget`
* Widgets personalizados

En este método no deberán realizarse conexiones de señales ni construirse el layout principal.

### `setup_layout()`

Será responsable de organizar los widgets dentro de la interfaz.

Aquí se crearán y configurarán los layouts necesarios.

No deberán realizarse conexiones entre señales y slots.

### `connect_signals()`

Será responsable de conectar todas las señales y slots del componente.

Toda la lógica relacionada con eventos deberá concentrarse en este método.

Esto incluye:

* Conexión de botones.
* Conexión entre widgets.
* Conexión con `MainWindow`.
* Conexión con controladores.

## Uso de métodos con nombre

Siempre que una acción tenga significado dentro de la aplicación, se preferirá utilizar un método con nombre en lugar de una función anónima creada mediante `lambda`.

Ejemplo recomendado:

```python
self.welcome_screen.maintainer_requested.connect(
    self.show_maintainer_screen
)
```

```python
def show_maintainer_screen(self):
    self.navigation_controller.show_screen(
        MAINTAINER_SCREEN
    )
```

Ejemplo que deberá evitarse cuando exista una alternativa clara:

```python
self.welcome_screen.maintainer_requested.connect(
    lambda: self.navigation_controller.show_screen(
        MAINTAINER_SCREEN
    )
)
```

Los métodos con nombre deberán utilizarse especialmente cuando:

* La acción represente una operación relevante de la aplicación.
* La lógica pueda crecer en el futuro.
* Sea útil para debugging.
* Mejore la legibilidad del código.
* La misma acción pueda reutilizarse desde más de una señal.

El uso de `lambda` no queda prohibido. Podrá utilizarse cuando la operación sea trivial, breve y no justifique la creación de un método adicional.

## Métodos privados

Los métodos utilizados únicamente dentro de una clase podrán identificarse mediante un guion bajo inicial.

Ejemplo:

```python
def _show_maintainer_screen(self):
    pass
```

Esta convención indicará que el método forma parte de la implementación interna de la clase.

## Responsabilidades del constructor

El método `__init__()` deberá permanecer lo más simple posible.

Su función será únicamente inicializar el objeto y coordinar las distintas etapas de construcción.

Siempre que sea posible, deberá evitar contener:

* Lógica de negocio.
* Conexiones directas extensas.
* Configuraciones visuales complejas.
* Operaciones de navegación.
* Acceso al hardware.

## Consecuencias

### Ventajas

* Todas las clases tendrán una estructura uniforme.
* Reduce el tiempo necesario para comprender un archivo nuevo.
* Facilita el mantenimiento del proyecto.
* Simplifica la incorporación de nuevos desarrolladores.
* Favorece el principio de responsabilidad única.
* Mantiene los constructores pequeños.
* Mejora la legibilidad de las conexiones entre señales y slots.
* Facilita el debugging mediante métodos con nombres descriptivos.
* Reduce la cantidad de funciones anónimas distribuidas por el proyecto.

### Desventajas

* Incrementa ligeramente la cantidad de métodos en cada clase.
* Algunas operaciones simples requerirán un método adicional.

Estas desventajas se consideran menores frente a la mejora obtenida en organización, claridad y mantenibilidad.

## Observaciones

Esta convención deberá aplicarse a todas las clases gráficas desarrolladas para el proyecto.

En caso de que una clase no requiera alguno de los métodos definidos, como `connect_signals()`, el método podrá mantenerse vacío para conservar una estructura homogénea.

De esta forma, cualquier clase de la GUI compartirá la misma organización interna independientemente de su complejidad.

---

# ADR-010 – Navegación centralizada mediante NavigationController

## Estado

Aceptada.

## Contexto

La aplicación utiliza una `MainWindow` con un `QStackedWidget` para mostrar distintas pantallas.

Inicialmente existen pocas pantallas:

* WelcomeScreen
* MaintainerScreen
* StatisticsScreen

Sin embargo, en futuras versiones se agregarán nuevas pantallas, como:

* LoginScreen o LoginDialog
* NormalOperationScreen
* AlarmScreen
* RecipeScreen
* SettingsScreen
* CalibrationScreen

Si `MainWindow` administra directamente todos los cambios de pantalla, esta clase puede crecer demasiado y mezclar responsabilidades.

## Decisión

Se implementará una clase `NavigationController`.

Su responsabilidad será administrar la navegación entre pantallas.

`MainWindow` seguirá siendo responsable de ensamblar los componentes principales de la aplicación, pero no deberá manipular directamente los índices del `QStackedWidget`.

La estructura será:

```text
MainWindow
   │
   ├── TopBarWidget
   │
   ├── NavigationController
   │        │
   │        ▼
   │   QStackedWidget
   │        ├── WelcomeScreen
   │        ├── MaintainerScreen
   │        └── StatisticsScreen
```

El `NavigationController` deberá:

* Registrar pantallas.
* Asociar cada pantalla con un nombre lógico.
* Cambiar la pantalla visible.
* Ocultar los índices internos del `QStackedWidget`.

Ejemplo conceptual:

```python
navigation_controller.show_screen("welcome")
navigation_controller.show_screen("maintainer")
navigation_controller.show_screen("statistics")
```

## Consecuencias

### Ventajas

* Reduce la responsabilidad de `MainWindow`.
* Centraliza la navegación.
* Evita depender de índices numéricos del `QStackedWidget`.
* Facilita agregar nuevas pantallas.
* Mejora la legibilidad del código.
* Permite incorporar navegación hacia atrás en el futuro.

---