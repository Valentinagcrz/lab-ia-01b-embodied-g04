#!/usr/bin/env python3
"""
correr_experimentos.py — Ejecuta en orden las Fases 3, 5, 6, 7, 8, 9 y 10 sobre las escenas
ya capturadas, con reintentos ante errores de red/cuota. Bitácora en resultados/corrida.log.

    python3 correr_experimentos.py            # todo
    python3 correr_experimentos.py --desde 7  # retomar desde una fase

Requiere GEMINI_API_KEY en el entorno y verdad_terreno.csv lleno ANTES de correrlo.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "resultados" / "resultados.csv"
DEV = AQUI / "resultados" / "desarrollo.csv"
LOG = AQUI / "resultados" / "corrida.log"
G = os.environ.get("GRUPO", "G04")

# Calibración rápida (Fase 3): la hoja quedó irreconocible contra la mesa blanca, así que se usa la
# zona cuadriculada: 50 cuadros de 5 mm = 0.250 m, entre u = 417 y u = 1673 px (fila central de regla),
# con Z = 0.51 m medido con cinta (mediana del sensor: 0.515 m).
CAL = dict(u1=417, u2=1673, ancho=0.250, z=0.51)

OBJ = {
    "semantica1": "la caja de hamburguesa libre y segura para tomar desde arriba",
    "semantica2": "el celular que pertenece a la persona que dejó sus llaves al lado",
    "semantica3": "el cuaderno que está abierto",
    "semantica4": "el esfero que está dentro del estuche",
    "burger": "la caja de hamburguesa libre del carrito que se puede llevar a la bandeja",
}
O_DIST = "el centro de la tapa del termo y el centro de la tapa de la caja"


def log(msg):
    linea = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(linea, flush=True)
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def run(args, reintentos=4, script="embodied_sin_ros.py"):
    cmd = [sys.executable, str(AQUI / script), *args]
    for intento in range(1, reintentos + 1):
        r = subprocess.run(cmd, cwd=AQUI, capture_output=True, text=True)
        salida = r.stdout + r.stderr
        with open(LOG, "a", encoding="utf-8") as f:
            f.write("$ " + " ".join(args) + "\n" + r.stdout[-3000:] + ("\n" + r.stderr[-1500:] if r.returncode else "") + "\n")
        if r.returncode == 0 or "no es JSON válido" in salida:
            for l in r.stdout.splitlines():
                if l.startswith(("[INFO] Respuesta", "  - ", "[INFO] Distancia", "[OK] Campo")):
                    log("   " + l.strip())
            return r.returncode == 0
        espera = 20 * intento
        log(f"   ⚠️ intento {intento} falló ({salida.strip().splitlines()[-1][:160] if salida.strip() else 'sin salida'}); reintento en {espera}s")
        time.sleep(espera)
    log("   ❌ se omitió tras varios intentos")
    return False


def ultima_respuesta():
    with open(CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))[-1]["respuesta"]


def git_commit(msg):
    r = subprocess.run(["git", "add", "-A"], cwd=AQUI, capture_output=True, text=True)
    r = subprocess.run(["git", "commit", "-qm", msg], cwd=AQUI, capture_output=True, text=True)
    sha = subprocess.run(["git", "log", "--oneline", "-1"], cwd=AQUI, capture_output=True, text=True).stdout.strip()
    log(f"   git: {sha}")


def fase3():
    log("FASE 3 · calibración rápida y verificación")
    run(["calibrar", "--escena", "regla", "--u1", str(CAL["u1"]), "--u2", str(CAL["u2"]),
         "--ancho-real-m", str(CAL["ancho"]), "--distancia-m", str(CAL["z"])], 1)
    run(["consultar", "--escena", "regla", "--tarea", "puntos", "--grupo", G, "--objeto",
         "el borde izquierdo y el borde derecho de la zona cuadriculada de la hoja, sobre la línea horizontal "
         "que pasa por el centro de la imagen"])


def fase5():
    log("FASE 5 · Exp. 1 — desarrollo (iteración 0, solo escenas D) → desarrollo.csv")
    for e, o in OBJ.items():
        run(["consultar", "--escena", e, "--tarea", "propio", "--thinking", "low", "--grupo", G, "--objeto", o,
             "--csv", str(DEV)])
    git_commit("prompt congelado")
    log("FASE 5 · Exp. 1 — prueba: escenas D y P, prompt congelado, thinking low, 3 repeticiones")
    for i in range(1, 4):
        for e, o in OBJ.items():
            for s in ("", "p"):
                log(f" rep {i} · {e}{s}")
                run(["consultar", "--escena", e + s, "--tarea", "propio", "--thinking", "low", "--grupo", G, "--objeto", o])
        for s in ("", "p"):
            log(f" rep {i} · burger{s} (ingenuo)")
            run(["consultar", "--escena", "burger" + s, "--tarea", "puntos", "--thinking", "low", "--grupo", G,
                 "--objeto", "la caja"])


def fase6():
    log("FASE 6 · Exp. 2 — cajas delimitadoras, 5 repeticiones")
    for e in ("semantica1", "burger"):
        for i in range(1, 6):
            log(f" {e} rep {i}")
            run(["consultar", "--escena", e, "--tarea", "cajas", "--objeto", "", "--grupo", G])


def fase7():
    log("FASE 7 · Exp. 3 — distancia 3D con y sin registro (misma respuesta)")
    for k in range(1, 6):
        for i in range(1, 3):
            log(f" dist{k} rep {i}")
            if run(["consultar", "--escena", f"dist{k}", "--tarea", "puntos", "--grupo", G, "--objeto", O_DIST]):
                run(["consultar", "--escena", f"dist{k}", "--tarea", "puntos", "--grupo", G, "--objeto", O_DIST,
                     "--sin-registro", "--respuesta", ultima_respuesta()], 1)
    log(" altura del termo")
    run(["consultar", "--escena", "dist1", "--tarea", "puntos", "--grupo", G, "--objeto",
         "el centro de la tapa del termo y la mesa justo al lado del termo"])


def fase8():
    log("FASE 8 · Exp. 4 — thinking low/high intercalado, 5 repeticiones, semantica2p")
    for i in range(1, 6):
        for nivel in ("low", "high"):
            log(f" rep {i} · {nivel}")
            run(["consultar", "--escena", "semantica2p", "--tarea", "propio", "--thinking", nivel, "--grupo", G,
                 "--objeto", OBJ["semantica2"]])


def fase9():
    log("FASE 9 · Exp. 5 — volumen, agarre, plan y éxito")
    esquinas = [{"point": [120, 150], "label": "mesa_sup_izq"}, {"point": [120, 880], "label": "mesa_sup_der"},
                {"point": [850, 150], "label": "mesa_inf_izq"}, {"point": [850, 880], "label": "mesa_inf_der"}]
    run(["consultar", "--escena", "regla", "--tarea", "puntos", "--grupo", G, "--objeto",
         "esquinas de la zona útil de la mesa (definidas por el equipo)", "--respuesta", json.dumps(esquinas)], 1)
    med = json.loads((AQUI / "mediciones.json").read_text(encoding="utf-8")) if (AQUI / "mediciones.json").exists() else {}
    hmax = med.get("general", {}).get("h_max_m", 0.305)
    run(["volumen", "--escena", "regla", "--h-max", str(hmax), "--d-a", "0.10"], 1, script="espacio_trabajo.py")
    for e in ("agarre_s1", "agarre_s2", "agarre_s3", "agarre_i1", "agarre_i2", "agarre_i3"):
        log(f" {e}")
        run(["consultar", "--escena", e, "--tarea", "agarre", "--grupo", G, "--objeto", "la caja de hamburguesa"])
    log(" plan")
    run(["consultar", "--escena", "burger", "--tarea", "plan", "--grupo", G, "--objeto", "llevar la caja libre a la bandeja"])
    run(["plan", "--escena", "burger"], 1, script="espacio_trabajo.py")
    for a, d in (("exito_antes1", "exito_bien1"), ("exito_antes2", "exito_mal1"),
                 ("exito_antes3", "exito_bien2"), ("exito_antes4", "exito_mal2")):
        log(f" éxito {a} -> {d}")
        run(["exito", "--antes", a, "--despues", d, "--grupo", G, "--objeto", "la caja quedó dentro de la bandeja"])


def fase10():
    log("FASE 10 · análisis")
    r = subprocess.run([sys.executable, str(AQUI / "analisis_lab_ia_01b.py")], cwd=AQUI, capture_output=True, text=True)
    LOG.open("a", encoding="utf-8").write(r.stdout + r.stderr)
    log("   resultados/tablas.md escrito" if r.returncode == 0 else "   ❌ análisis falló (ver log)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", type=int, default=3)
    a = ap.parse_args()
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("Falta: export GEMINI_API_KEY=\"...\"")
    t0 = time.time()
    for n, f in ((3, fase3), (5, fase5), (6, fase6), (7, fase7), (8, fase8), (9, fase9), (10, fase10)):
        if n >= a.desde:
            f()
    log(f"✅ TERMINADO en {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
