# `system_state.py`

El módulo `system_state.py` define la estructura fundamental que gobierna el comportamiento secuencial del software mediante la clase `SystemState`, la cual hereda de la clase nativa `Enum` de Python. 

---

## <span style="color: #2196F3;">Definición de la Clase: `SystemState`</span>

Cada miembro de la enumeración representa un **estado operativo discreto** y tiene asignado un valor entero único que actúa como identificador interno.

???+ note "Código Fuente Completo"
    El archivo actúa como un escalable, diseñado para expandirse a medida que se integren las etapas físicas del ciclo de plasma:

    ```python
    # La idea es ir agregando estados acá
    class SystemState(Enum):
        PRE_ENCENDIDO = 0
        MAIN_MENU = 1
    ```

---

## <span style="color: #2196F3;">Descripción de los Estados Actuales</span>

* **`PRE_ENCENDIDO (0)`**: Fase Inicial: El software bloquea la interfaz de usuario general y activa un lazo de monitoreo cíclico a la espera del pulsador físico de marcha (`POWER_ON_SWITCH`). Al encender, genera la secuencia de enclavamiento eléctrico y la temporización de estabilización de 10 segundos antes de pasar a `MAIN_MENU`
* **`MAIN_MENU (1)`**: Menu Principal: Desde este estado, el operador tiene acceso a la pantalla principal de control de procesos del Asher y el software empieza a verificar las condiciones de interlock generales (como la señal de parada general `SYS_POWER`).

