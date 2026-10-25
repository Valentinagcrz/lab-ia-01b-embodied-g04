#!/usr/bin/env python3
"""nueva_sesion.py — Guarda la sesión anterior y deja todo listo para capturar de nuevo desde cero.

No borra nada: mueve capturas/, resultados/, mediciones.json y volumen_trabajo.json a
sesiones_anteriores/sesion_<fecha>/ y deja verdad_terreno.csv con las cajas en blanco
(hay que volver a marcarlas con las fotos nuevas).

    python3 nueva_sesion.py
"""
import csv
import shutil
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
destino = AQUI / "sesiones_anteriores" / f"sesion_{datetime.now():%Y%m%d_%H%M}"
destino.mkdir(parents=True, exist_ok=True)
for nombre in ("capturas", "resultados"):
    (destino / nombre).mkdir(exist_ok=True)
    for f in (AQUI / nombre).glob("*"):
        if f.is_file() and not f.name.startswith("sim_"):
            shutil.move(str(f), str(destino / nombre / f.name))
for nombre in ("mediciones.json", "volumen_trabajo.json"):
    if (AQUI / nombre).exists():
        shutil.move(str(AQUI / nombre), str(destino / nombre))
shutil.copy2(AQUI / "verdad_terreno.csv", destino / "verdad_terreno.csv")

# verdad_terreno.csv: se conservan escenas y descripciones, se vacían cajas y medidas
with open(AQUI / "verdad_terreno.csv", encoding="utf-8") as f:
    lector = csv.DictReader(f)
    campos, filas = lector.fieldnames, list(lector)
for r in filas:
    for k in ("u_min", "v_min", "u_max", "v_max", "d_real_m"):
        r[k] = ""
    r["nota"] = ""
with open(AQUI / "verdad_terreno.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    w.writerows(filas)
print(f"Sesión anterior guardada en {destino.relative_to(AQUI)}. Ahora: python3 sesion_captura.py")
