# Qué hay en esta carpeta (LAB-IA-01B, Ruta A)

Es la **plantilla oficial** `plantilla_lab_ia_embodied/`, tomada del `upstream/main` del repositorio del curso (commit 6346b5b, 19/10/2026), con lo siguiente resuelto o agregado:

| Archivo | Cambio |
|---|---|
| `embodied_comun.py` | **TODO 1** (`PROMPTS["propio"]`, iteración 0), **TODO 2** `normalizado_a_pixel`, **TODO 3** `profundidad_robusta`, **TODO 4** `desproyectar`. |
| `embodied_sin_ros.py` | Dos extensiones pequeñas: (1) un JSON inválido se registra en el CSV con `label = JSON_INVALIDO`, porque cuenta como fallo en el Accuracy; (2) la imagen hecha sin registro se guarda como `*_sinreg_resultado.png` y no reemplaza a la de con registro (sirve para la E6). |
| `test_kinova_camera.py` | Copia de `scripts/` del repositorio, para que `capturar` funcione desde esta carpeta. |
| `espacio_trabajo.py` | **Nuevo (Fase 9):** volumen de trabajo, normal de la mesa, pre-agarre y las 4 reglas para validar el plan. |
| `analisis_lab_ia_01b.py` | **Nuevo (Fase 10):** arma las Tablas 6 a 11 a partir de `resultados/resultados.csv` y `verdad_terreno.csv`. |
| `simulacion_sin_robot.py` | **Nuevo:** ensayo de todo el pipeline con escenas sintéticas y `--respuesta`. Escribe en `resultados/simulacion.csv`. **No es evidencia experimental.** |
| `verdad_terreno.csv` | Plantilla de la verdad de terreno. Se llena **antes** de consultar a Gemini. |
| `COMANDOS_SESION.md` | Todos los comandos, fase por fase. |

Lo que falta y solo se puede hacer en el laboratorio: las capturas, la calibración con la hoja A4, las consultas reales a Gemini (con la clave de la API) y las mediciones con cinta.

Para la entrega, copien la carpeta a `~/ros2_ws/src/burger_delivery/education/guias_laboratorio/plantilla_lab_ia_embodied/` y hagan commit en el repositorio del equipo. Así el SHA queda en `burger-kinova-equipo-04`.
