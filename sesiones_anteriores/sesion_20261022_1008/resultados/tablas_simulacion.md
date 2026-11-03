# Tablas LAB-IA-01B — generadas por analisis_lab_ia_01b.py

Fuente: `simulacion.csv` (9 consultas, 0 a la API real) y `verdad_simulacion.csv`. Las consultas con modelo = manual (--respuesta) se excluyen de latencia y tokens.

## Tabla 6 — Exp. 1: semántica con partición (thinking = low)

| Relación | Aciertos D | Aciertos P | JSON inválidos | Latencia media ± σ (s) | Observación |
|---|---|---|---|---|---|
| Seguridad | 0 / 0 | 0 / 0 | 0 | — |  |
| Pertenencia | 0 / 0 | 0 / 0 | 0 | — |  |
| Estado | 0 / 0 | 0 / 0 | 0 | — |  |
| Contencion | 0 / 0 | 0 / 0 | 0 | — |  |
| Relacional (burger, prompt propio) | 0 / 0 | 0 / 0 | 0 | — |  |
| Relacional (burger, prompt ingenuo) | 0 / 0 | 0 / 0 | 0 | — |  |
| **Accuracy global (propio)** | D: — (N=0) | P: — (N=0) |  |  | Brecha D − P: — |

## Tabla 7 — Exp. 2: cajas delimitadoras

| Escena | Objeto | IoU medio ± σ con la verdad | σ coordenadas (px) | IoU medio entre repeticiones | N |
|---|---|---|---|---|---|
| **Global** |  | mIoU: — |  |  | TP=0 FP=0 FN=0 · Precision — · Recall — |

## Tabla 8 — Exp. 3: exactitud 3D y ablación del registro

| Config. | Posición en la imagen | d_real (m) | d_est con registro (m) | e con registro (mm) | d_est sin registro (m) | e sin registro (mm) |
|---|---|---|---|---|---|---|
| sim_dist | centro (simulado) | 0.166 | 0.166 | 0.0 | 0.286 | 120.0 |
| sim_dist_borde | borde de la caja (simulado) | 0.121 | 0.121 | 0.0 | 0.159 | 37.8 |
| **MAE / RMSE** (N=2 / 2) |  |  |  | 0.0 / 0.0 |  | 78.9 / 89.0 |

## Tabla 9 — Exp. 4: costo del razonamiento (semantica2p)

| thinking_level | Accuracy | Latencia media ± σ (s) | Decisiones/min | Tokens pensamiento | Tokens totales | ¿Aceptó el nivel? |
|---|---|---|---|---|---|---|
| low | — | — | — | — | — | no consultado |
| high | — | — | — | — | — | no consultado |
| minimal | — | — | — | — | — | no consultado |
| medium | — | — | — | — | — | no consultado |

## Tabla 10a — Matriz de confusión del agarre (positivo = insegura, el modelo se abstiene)

|  | Modelo se abstiene (lista vacía) | Modelo devuelve punto |
|---|---|---|
| Escena insegura | TP = 1 | FN = 0 |
| Escena segura | FP = 0 | TN = 1 |
| Precision / Recall / F1 | 1.00 / 1.00 / 1.00 |  |

## Tabla 10b — Espacio de trabajo y pre-agarre

| Escena | Punto de agarre (X, Y, Z) m | ¿Dentro del volumen? | ¿Sobre el objeto correcto? | p_pre (m) | Observación |
|---|---|---|---|---|---|
| sim_agarre_s1 | (0.050, 0.030, 0.600) | True | True | (0.050, 0.030, 0.500) |  |

Volumen de trabajo: X [-0.250, 0.250] m · Y [-0.180, 0.180] m · Z_mesa = 0.800 m · h_max = 0.300 m · n = (-0.0, -0.0, -1.0) · d_a = 0.1 m

## Tabla 10c — Plan y detección de éxito

| Prueba | Resultado del modelo | Resultado esperado | ¿Correcto? | Comentario |
|---|---|---|---|---|
| Plan: a) vocabulario permitido | OK |  | True |  |
| Plan: b) objetivos existentes | OK |  | True |  |
| Plan: c) puntos dentro del volumen | OK |  | True |  |
| Plan: d) secuencia coherente | OK |  | True |  |
| Éxito: sim_dist->sim_exito_bien1 | exito: True | exito: true | True | respuesta escrita a mano |
| **Accuracy de detección de éxito** | 1.00 | N=1 |  |  |

## Tabla 11 — Resumen de métricas

| Métrica | Valor ± dispersión | N | Exp. | ¿Confirma la hipótesis de la Fase 1? |
|---|---|---|---|---|
| Accuracy semántica D / P | — / — | 0 / 0 | 1 |  |
| mIoU · Precision / Recall de detección | — · — / — | 0 | 2 |  |
| RMSE 3D con / sin registro (mm) | 0.0 / 89.0 | 2 / 2 | 3 |  |
| Latencia low / high (s) | — / — | 0 / 0 | 4 |  |
| P / R / F1 del rechazo de agarres inseguros | 1.00 / 1.00 / 1.00 | 2 | 5 |  |
| Accuracy de detección de éxito | 1.00 | 1 | 5 |  |
