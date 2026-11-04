# Servicios (`services/`)

Los servicios aíslan operaciones compartidas que no pertenecen a un widget concreto.

- [`hardware.py`](hardware.md): abstracción de lecturas/escrituras y estado seguro de las placas.
- `system_state.py`: enum legado, actualmente no utilizado para navegar ni arrancar la GUI ([nota de estado](system_state.md)).
- `recipe_service.py`: acceso y validación de recetas.
- `recipe_log.py`: persistencia de datos de proceso de recetas.
- `maintenance_data_log.py`: almacenamiento de muestras de mantenimiento.
- `shutdown_log.py`: registro de resultados del apagado.

Controladores y secuencias consumen estos servicios; las definiciones de hardware están en [configuración](../config/index.md) y [drivers](../drivers/index.md).
