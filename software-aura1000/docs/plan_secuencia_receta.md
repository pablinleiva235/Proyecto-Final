# Plan de inicio de receta

## Objetivo

Documentar el flujo previsto para el botón **Iniciar receta** y las definiciones que faltan antes de automatizarlo.

## Secuencia propuesta

1. Mostrar los parámetros de la receta activa y pedir al usuario que los confirme.
2. Abrir la puerta e indicar que inserte la oblea.
3. Esperar la confirmación del usuario de que la oblea fue insertada.
4. Cerrar la puerta.
5. Activar Soft Vacuum.
6. Esperar 5 segundos.
7. Activar Main Vacuum.
8. Al alcanzar la presión base de la receta, aplicar los caudales de O₂ y N₂ configurados en la receta, usando el control legacy de presión.
9. Al alcanzar la presión de cámara deseada, iniciar el control de lámparas/temperatura legacy.
10. Al alcanzar la temperatura deseada, encender el plasma (RF).
11. Cuando EOP alcance su condición de fin, apagar el plasma (RF).
12. Apagar los MFC y detener el flujo de gases.
13. Apagar Main Vacuum.
14. Iniciar el venteo de la cámara.
15. Al finalizar el venteo, abrir la puerta.

## Decisiones acordadas

- Las esperas de presión, temperatura y EOP no tienen timeout automático.
- La interfaz debe ofrecer un botón **Detener** durante la receta.
- Al detener, ejecutar el apagado seguro, ventear la cámara y abrir la puerta al llegar a presión atmosférica.
- El monitoreo digital debe permanecer activo durante la receta para actualizar las entradas de puerta y ATM y completar correctamente las secuencias.

## Estado actual del proyecto

- El botón **Iniciar receta** está deshabilitado y todavía no inicia un proceso.
- Ya existen secuencias/controladores reutilizables para puerta, Soft Vacuum, Main Vacuum, venteo, MFC, lámparas y RF.
- El código legacy actualmente localizado ofrece controles manuales de caudal y un pulso temporizado de lámparas 1 y 3; no se encontró allí un control automático por realimentación de presión y temperatura.

## Pendientes antes de implementar

- Localizar o recibir el código legacy de control automático de presión y temperatura que se debe integrar.
- Definir el umbral EOP en voltios que indica el fin del proceso y apaga RF.

La implementación del botón **Iniciar receta** queda pendiente hasta resolver estos dos puntos.
