# Tablas LAB-IA-01B — generadas por analisis_lab_ia_01b.py

Fuente: `resultados.csv` (90 consultas, 79 a la API real) y `verdad_terreno.csv`. Las consultas con modelo = manual (--respuesta) se excluyen de latencia y tokens.

## Tabla 6 — Exp. 1: semántica con partición (thinking = low)

| Relación | Aciertos D | Aciertos P | JSON inválidos | Latencia media ± σ (s) | Observación |
|---|---|---|---|---|---|
| Seguridad | 0 / 3 | 3 / 3 | 0 | 3.05 ± 1.18 |  |
| Pertenencia | 3 / 3 | 3 / 3 | 0 | 3.01 ± 0.33 |  |
| Estado | 3 / 3 | 3 / 3 | 0 | 2.65 ± 0.34 |  |
| Contencion | 3 / 3 | 3 / 3 | 0 | 2.79 ± 0.40 |  |
| Relacional (burger, prompt propio) | 2 / 3 | 3 / 3 | 0 | 2.99 ± 0.47 |  |
| Relacional (burger, prompt ingenuo) | 0 / 3 | 3 / 3 | 0 | 2.51 ± 0.17 |  |
| **Accuracy global (propio)** | D: 0.73 (N=15) | P: 1.00 (N=15) |  |  | Brecha D − P: -0.27 |

## Tabla 7 — Exp. 2: cajas delimitadoras

| Escena | Objeto | IoU medio ± σ con la verdad | σ coordenadas (px) | IoU medio entre repeticiones | N |
|---|---|---|---|---|---|
| burger | caja|recipiente|contenedor|box | 0.91 ± 0.00 | 1.2 | 0.99 | N=5 |
| burger | disco|drive|cargador|bateria|dispositivo | 0.84 ± 0.01 | 2.1 | 0.98 | N=5 |
| burger | caja|recipiente|contenedor|box | 0.59 ± 0.00 | 0.9 | 1.00 | N=5 |
| semantica1 | caja|recipiente|contenedor|box | 0.91 ± 0.00 | 0.2 | 1.00 | N=5 |
| semantica1 | caja|recipiente|contenedor|box | 0.68 ± 0.00 | 1.0 | 0.99 | N=5 |
| semantica1 | termo|botella|bottle|coca | 0.95 ± 0.00 | 0.7 | 0.99 | N=5 |
| semantica1 | hoja|papel|cuadricula|paper | 0.00 ± 0.00 | — | — | N=5 |
| **Global** |  | mIoU: 0.82 |  |  | TP=20 FP=10 FN=15 · Precision 0.67 · Recall 0.57 |

## Tabla 8 — Exp. 3: exactitud 3D y ablación del registro

| Config. | Posición en la imagen | d_real (m) | d_est con registro (m) | e con registro (mm) | d_est sin registro (m) | e sin registro (mm) |
|---|---|---|---|---|---|---|
| dist1 | cinta: centro a centro (config 1) | 0.200 | 0.208 | 8.5 | 0.210 | 9.8 |
| dist2 | cinta: centro a centro (config 2) | 0.300 | 0.298 | -1.6 | — | — |
| dist3 | cinta: centro a centro (config 3) | 0.400 | — | — | — | — |
| dist4 | cinta: centro a centro (borde) | 0.450 | — | — | — | — |
| dist5 | cinta: centro a centro (borde) | 0.250 | — | — | — | — |
| **MAE / RMSE** (N=3 / 2) |  |  |  | 6.2 / 7.1 |  | 9.8 / 10.0 |

Altura de un objeto sobre la mesa (termo): real 0.215 m · estimada (Z_mesa − Z_objeto) 0.006 m · error -209.0 mm.

## Tabla 9 — Exp. 4: costo del razonamiento (semantica2p)

| thinking_level | Accuracy | Latencia media ± σ (s) | Decisiones/min | Tokens pensamiento | Tokens totales | ¿Aceptó el nivel? |
|---|---|---|---|---|---|---|
| low | 5 / 5 | 3.27 ± 1.33 | 18.4 | 203 | 1556 | sí |
| high | 5 / 5 | 3.53 ± 0.30 | 17.0 | 438 | 1789 | sí |
| minimal | — | — | — | — | — | no consultado |
| medium | — | — | — | — | — | no consultado |

## Tabla 10a — Matriz de confusión del agarre (positivo = insegura, el modelo se abstiene)

|  | Modelo se abstiene (lista vacía) | Modelo devuelve punto |
|---|---|---|
| Escena insegura | TP = 2 | FN = 1 |
| Escena segura | FP = 0 | TN = 3 |
| Precision / Recall / F1 | 1.00 / 0.67 / 0.80 |  |

## Tabla 10b — Espacio de trabajo y pre-agarre

| Escena | Punto de agarre (X, Y, Z) m | ¿Dentro del volumen? | ¿Sobre el objeto correcto? | p_pre (m) | Observación |
|---|---|---|---|---|---|
| agarre_s1 | (0.021, -0.029, 0.463) | True | True | (0.018, -0.037, 0.363) |  |
| agarre_s2 | (0.034, -0.048, 0.463) | True | True | (0.031, -0.056, 0.363) |  |
| agarre_s3 | (0.022, -0.080, 0.529) | False | True | (0.019, -0.088, 0.429) |  |

Volumen de trabajo: X [-0.138, 0.148] m · Y [-0.085, 0.076] m · Z_mesa = 0.517 m · h_max = 0.305 m · n = (-0.0293, -0.0771, -0.9966) · d_a = 0.1 m

## Tabla 10c — Plan y detección de éxito

| Prueba | Resultado del modelo | Resultado esperado | ¿Correcto? | Comentario |
|---|---|---|---|---|
| Plan: a) vocabulario permitido | OK |  | True |  |
| Plan: b) objetivos existentes | OK |  | True |  |
| Plan: c) puntos dentro del volumen | OK |  | True |  |
| Plan: d) secuencia coherente | OK |  | True |  |
| Éxito: exito_antes1->exito_bien1 | exito: True | exito: true | True | La caja transparente se encuentra colocada sobre la superficie negra en la segunda imagen. |
| Éxito: exito_antes3->exito_bien2 | exito: False | exito: true | False | La caja transparente fue retirada de la escena. |
| Éxito: exito_antes2->exito_mal1 | exito: True | exito: false | False | La caja de plástico transparente ha sido colocada de forma más centrada sobre la superficie blanca. |
| Éxito: exito_antes4->exito_mal2 | exito: False | exito: false | True | La caja sigue en la misma posición fuera de la bandeja negra. |
| **Accuracy de detección de éxito** | 0.50 | N=4 |  |  |

## Tabla 11 — Resumen de métricas

| Métrica | Valor ± dispersión | N | Exp. | ¿Confirma la hipótesis de la Fase 1? |
|---|---|---|---|---|
| Accuracy semántica D / P | 0.73 / 1.00 | 15 / 15 | 1 |  |
| mIoU · Precision / Recall de detección | 0.82 · 0.67 / 0.57 | 35 | 2 |  |
| RMSE 3D con / sin registro (mm) | 7.1 / 10.0 | 3 / 2 | 3 |  |
| Latencia low / high (s) | 3.27 ± 1.33 / 3.53 ± 0.30 | 5 / 5 | 4 |  |
| P / R / F1 del rechazo de agarres inseguros | 1.00 / 0.67 / 0.80 | 6 | 5 |  |
| Accuracy de detección de éxito | 0.50 | 4 | 5 |  |
