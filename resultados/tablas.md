# Tablas LAB-IA-01B — generadas por analisis_lab_ia_01b.py

Fuente: `resultados.csv` (90 consultas, 79 a la API real) y `verdad_terreno.csv`. Las consultas con modelo = manual (--respuesta) se excluyen de latencia y tokens.

## Tabla 6 — Exp. 1: semántica con partición (thinking = low)

| Relación | Aciertos D | Aciertos P | JSON inválidos | Latencia media ± σ (s) | Observación |
|---|---|---|---|---|---|
| Seguridad | 3 / 3 | 3 / 3 | 0 | 2.73 ± 0.64 |  |
| Pertenencia | 3 / 3 | 3 / 3 | 0 | 7.14 ± 9.00 |  |
| Estado | 3 / 3 | 3 / 3 | 0 | 2.78 ± 1.21 |  |
| Contencion | 3 / 3 | 3 / 3 | 0 | 7.77 ± 12.55 |  |
| Relacional (burger, prompt propio) | 2 / 3 | 3 / 3 | 0 | 3.51 ± 1.14 |  |
| Relacional (burger, prompt ingenuo) | 0 / 3 | 0 / 3 | 0 | 8.73 ± 10.28 |  |
| **Accuracy global (propio)** | D: 0.93 (N=15) | P: 1.00 (N=15) |  |  | Brecha D − P: -0.07 |

## Tabla 7 — Exp. 2: cajas delimitadoras

| Escena | Objeto | IoU medio ± σ con la verdad | σ coordenadas (px) | IoU medio entre repeticiones | N |
|---|---|---|---|---|---|
| burger | caja|recipiente|contenedor|box|tupper | 0.97 ± 0.00 | 1.0 | 0.99 | N=5 |
| burger | disco|drive|cargador|bateria|power|dispositivo|negro | 0.86 ± 0.00 | 0.6 | 0.99 | N=5 |
| burger | caja|recipiente|contenedor|box|tupper | 0.88 ± 0.00 | 0.9 | 0.99 | N=5 |
| burger | bandeja|router|caja de carton|tray | 0.98 ± 0.00 | 0.5 | 1.00 | N=5 |
| semantica1 | caja|recipiente|contenedor|box|tupper | 0.85 ± 0.01 | 1.1 | 0.99 | N=5 |
| semantica1 | caja|recipiente|contenedor|box|tupper | 0.90 ± 0.01 | 1.3 | 0.99 | N=5 |
| semantica1 | termo|vaso|botella|tapa|cup|mug|thermos | 0.88 ± 0.00 | 0.7 | 0.99 | N=5 |
| **Global** |  | mIoU: 0.90 |  |  | TP=28 FP=7 FN=7 · Precision 0.80 · Recall 0.80 |

## Tabla 8 — Exp. 3: exactitud 3D y ablación del registro

| Config. | Posición en la imagen | d_real (m) | d_est con registro (m) | e con registro (mm) | d_est sin registro (m) | e sin registro (mm) |
|---|---|---|---|---|---|---|
| dist1 | cinta: centro a centro (config 1) | 0.100 | 0.126 | 25.8 | 0.125 | 25.2 |
| dist2 | cinta: centro a centro (config 2) | 0.150 | 0.192 | 41.8 | 0.191 | 41.4 |
| dist3 | cinta: centro a centro (config 3) | 0.200 | 0.259 | 59.2 | 0.257 | 57.5 |
| dist4 | cinta: centro a centro (caja en el borde derecho) | 0.150 | 0.208 | 57.7 | 0.208 | 57.9 |
| dist5 | cinta: centro a centro (termo en la esquina superior derecha) | 0.200 | 0.231 | 30.5 | 0.230 | 30.0 |
| **MAE / RMSE** (N=10 / 10) |  |  |  | 43.0 / 45.1 |  | 42.4 / 44.5 |

Altura de un objeto sobre la mesa (termo): real 0.150 m · estimada (Z_mesa − Z_objeto) 0.002 m · error -148.0 mm.

## Tabla 9 — Exp. 4: costo del razonamiento (semantica2p)

| thinking_level | Accuracy | Latencia media ± σ (s) | Decisiones/min | Tokens pensamiento | Tokens totales | ¿Aceptó el nivel? |
|---|---|---|---|---|---|---|
| low | 5 / 5 | 12.29 ± 19.16 | 4.9 | 218 | 1573 | sí |
| high | 5 / 5 | 4.47 ± 2.22 | 13.4 | 459 | 1813 | sí |
| minimal | — | — | — | — | — | no consultado |
| medium | — | — | — | — | — | no consultado |

## Tabla 10a — Matriz de confusión del agarre (positivo = insegura, el modelo se abstiene)

|  | Modelo se abstiene (lista vacía) | Modelo devuelve punto |
|---|---|---|
| Escena insegura | TP = 0 | FN = 3 |
| Escena segura | FP = 0 | TN = 3 |
| Precision / Recall / F1 | — / 0.00 / — |  |

## Tabla 10b — Espacio de trabajo y pre-agarre

| Escena | Punto de agarre (X, Y, Z) m | ¿Dentro del volumen? | ¿Sobre el objeto correcto? | p_pre (m) | Observación |
|---|---|---|---|---|---|
| agarre_s1 | (-0.005, 0.003, 0.697) | True | True | (-0.008, 0.005, 0.597) |  |
| agarre_s2 | (0.013, -0.026, 0.697) | True | True | (0.010, -0.024, 0.597) |  |
| agarre_s3 | (0.018, -0.024, 0.689) | True | True | (0.015, -0.022, 0.589) |  |

Volumen de trabajo: X [-0.184, 0.197] m · Y [-0.112, 0.103] m · Z_mesa = 0.704 m · h_max = 0.200 m · n = (-0.0304, 0.0184, -0.9994) · d_a = 0.1 m

## Tabla 10c — Plan y detección de éxito

| Prueba | Resultado del modelo | Resultado esperado | ¿Correcto? | Comentario |
|---|---|---|---|---|
| Plan: a) vocabulario permitido | OK |  | True |  |
| Plan: b) objetivos existentes | OK |  | True |  |
| Plan: c) puntos dentro del volumen | FALLA |  | False | ['bandeja'] |
| Plan: d) secuencia coherente | OK |  | True |  |
| Éxito: exito_antes1->exito_bien1 | exito: False | exito: true | False | el recipiente se colocó sobre la caja del router y no dentro de una bandeja |
| Éxito: exito_antes3->exito_bien2 | exito: False | exito: true | False | El recipiente de plástico está colocado encima de la caja de router, no dentro de ella. |
| Éxito: exito_antes2->exito_mal1 | exito: False | exito: false | True | El recipiente de plástico se colocó sobre la caja del router, no dentro de una bandeja. |
| Éxito: exito_antes4->exito_mal2 | exito: False | exito: false | True | El recipiente de plástico con tapa naranja sigue fuera y no se encuentra dentro de ningún otro objeto. |
| **Accuracy de detección de éxito** | 0.50 | N=4 |  |  |

## Tabla 11 — Resumen de métricas

| Métrica | Valor ± dispersión | N | Exp. | ¿Confirma la hipótesis de la Fase 1? |
|---|---|---|---|---|
| Accuracy semántica D / P | 0.93 / 1.00 | 15 / 15 | 1 |  |
| mIoU · Precision / Recall de detección | 0.90 · 0.80 / 0.80 | 35 | 2 |  |
| RMSE 3D con / sin registro (mm) | 45.1 / 44.5 | 10 / 10 | 3 |  |
| Latencia low / high (s) | 12.29 ± 19.16 / 4.47 ± 2.22 | 5 / 5 | 4 |  |
| P / R / F1 del rechazo de agarres inseguros | — / 0.00 / — | 6 | 5 |  |
| Accuracy de detección de éxito | 0.50 | 4 | 5 |  |
