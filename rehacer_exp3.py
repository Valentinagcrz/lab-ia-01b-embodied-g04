#!/usr/bin/env python3
"""rehacer_exp3.py — Repite solo el Exp. 3 (Fase 7) con las escenas dist1..dist5 RECAPTURADAS.

Las filas de la primera captura (objetos fuera del campo de visión) no se borran: se mueven a
resultados/descartado_dist_v1.csv para que quede la trazabilidad. Luego corre la Fase 7 y el análisis.

    export GEMINI_API_KEYS="clave1,clave2"
    python3 rehacer_exp3.py
"""
import csv

import correr_experimentos as ce

ARCHIVO = ce.CSV.parent / "descartado_dist_v1.csv"

with open(ce.CSV, encoding="utf-8") as f:
    lector = csv.DictReader(f)
    campos, filas = lector.fieldnames, list(lector)
viejas = [r for r in filas if r["escena"].startswith("dist")]
if viejas:
    nuevo = not ARCHIVO.exists()
    with open(ARCHIVO, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        if nuevo:
            w.writeheader()
        w.writerows(viejas)
    with open(ce.CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows([r for r in filas if not r["escena"].startswith("dist")])
    ce.log(f"Exp. 3: {len(viejas)} filas de la captura anterior movidas a {ARCHIVO.name}")
try:
    ce.fase7()
except ce.SinCuota:
    ce.log("⛔ Sin cuota diaria en las claves disponibles.")
ce.fase10()
ce.log("✅ Exp. 3 rehecho")
