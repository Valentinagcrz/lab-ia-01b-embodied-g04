#!/usr/bin/env python3
"""
espacio_trabajo.py — Fase 9 (RAE 1.2): volumen de trabajo, normal de la mesa, pre-agarre
y validación automática del plan que propone Gemini. Va FUERA de la plantilla, como pide la guía.

Uso:
  # 1) Pida (o escriba a mano) las esquinas de la zona útil de la mesa en la escena regla:
  python3 embodied_sin_ros.py consultar --escena regla --tarea puntos --grupo G04 \
      --objeto "las cuatro esquinas de la hoja blanca"
  # 2) Construya el volumen con la última consulta de esa escena:
  python3 espacio_trabajo.py volumen --escena regla --h-max 0.25 --d-a 0.10
  # 3) Valide un agarre o un plan ya consultado (lee resultados/resultados.csv):
  python3 espacio_trabajo.py agarre --escena agarre_s1
  python3 espacio_trabajo.py plan   --escena burger
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
CSV = AQUI / "resultados" / "resultados.csv"
VOLUMEN = AQUI / "volumen_trabajo.json"
VOCABULARIO = {"mover_sobre", "bajar", "cerrar_pinza", "subir", "abrir_pinza"}


# ---------------------------------------------------------------------------
def dentro_del_volumen(xyz, lim) -> bool:   # lim: dict con x_min, x_max, y_min, y_max, z_mesa, h_max
    if xyz is None:
        return False
    x, y, z = xyz
    return (lim["x_min"] <= x <= lim["x_max"] and lim["y_min"] <= y <= lim["y_max"]
            and lim["z_mesa"] - lim["h_max"] <= z <= lim["z_mesa"])


def pose_pre_agarre(xyz, n, d_a=0.10):      # n: normal unitaria de la mesa, orientada hacia la cámara
    return np.asarray(xyz, dtype=float) + d_a * np.asarray(n, dtype=float)


def normal_mesa(p1, p2, p3) -> np.ndarray:
    """n = (P2-P1)x(P3-P1)/||...||, orientada hacia la cámara (Z < 0 en el marco óptico)."""
    p1, p2, p3 = (np.asarray(p, dtype=float) for p in (p1, p2, p3))
    n = np.cross(p2 - p1, p3 - p1)
    if np.linalg.norm(n) < 1e-12:
        raise ValueError("Los tres puntos de la mesa son colineales")
    n /= np.linalg.norm(n)
    return -n if n[2] > 0 else n


def validar_plan(plan: dict, puntos: dict, lim: dict | None) -> "OrderedDict[str, tuple]":
    """Reglas (a) vocabulario, (b) objetivos existentes, (c) puntos en el volumen, (d) secuencia física."""
    pasos = plan.get("pasos", []) if isinstance(plan, dict) else []
    etiquetas = {o.get("label") for o in plan.get("objetos", [])} if isinstance(plan, dict) else set()
    r = OrderedDict()
    malas = [p.get("accion") for p in pasos if p.get("accion") not in VOCABULARIO]
    r["a) vocabulario permitido"] = (bool(pasos) and not malas, malas)
    faltan = [p.get("objetivo") for p in pasos if p.get("objetivo") not in (None, "", "null")
              and p.get("objetivo") not in etiquetas]
    r["b) objetivos existentes"] = (not faltan, faltan)
    if lim is None:
        r["c) puntos dentro del volumen"] = (None, "falta volumen_trabajo.json")
    else:
        fuera = [e for e in etiquetas if not dentro_del_volumen(puntos.get(e), lim)]
        r["c) puntos dentro del volumen"] = (not fuera, fuera)
    abajo, pinza, cargando, err = False, "abierta", False, []
    for i, p in enumerate(pasos, 1):
        a = p.get("accion")
        if a == "mover_sobre" and abajo:
            err.append(f"paso {i}: mover_sobre estando abajo")
        elif a == "bajar":
            if abajo:
                err.append(f"paso {i}: bajar dos veces")
            abajo = True
        elif a == "cerrar_pinza":
            if not abajo:
                err.append(f"paso {i}: cerrar_pinza antes de bajar")
            pinza, cargando = "cerrada", abajo
        elif a == "subir":
            if not abajo:
                err.append(f"paso {i}: subir sin haber bajado")
            elif pinza == "abierta" and pasos[i - 2].get("accion") == "bajar":
                err.append(f"paso {i}: subir con la pinza abierta sin haber agarrado ni soltado")
            abajo = False
        elif a == "abrir_pinza":
            pinza, cargando = "abierta", False
    if cargando:
        err.append("el plan termina sin soltar el objeto")
    r["d) secuencia coherente"] = (bool(pasos) and not err, err)
    return r


# ---------------------------------------------------------------------------
def leer_consultas(ruta=None):
    """Agrupa las filas del CSV (una por detección) en consultas."""
    ruta = CSV if ruta is None else ruta
    if not Path(ruta).exists():
        return []
    consultas = OrderedDict()
    with open(ruta, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            clave = (fila["fecha"], fila["escena"], fila["tarea"], fila["registro"], fila["respuesta"])
            c = consultas.setdefault(clave, {**fila, "detecciones": []})
            if fila.get("label") not in (None, "", "JSON_INVALIDO"):
                xyz = None
                if fila.get("x_m") not in ("", None) and fila.get("z_m") not in ("", None):
                    xyz = (float(fila["x_m"]), float(fila["y_m"]), float(fila["z_m"]))
                c["detecciones"].append({"label": fila["label"], "u": float(fila["u"]), "v": float(fila["v"]),
                                         "xyz": xyz})
    return list(consultas.values())


def cargar_volumen():
    return json.loads(VOLUMEN.read_text(encoding="utf-8")) if VOLUMEN.exists() else None


def cmd_volumen(a):
    cs = [c for c in leer_consultas() if c["escena"] == a.escena and c["tarea"] == "puntos"]
    if not cs:
        sys.exit(f"No hay consultas de puntos de la escena {a.escena} en {CSV}")
    P = [d["xyz"] for d in cs[-1]["detecciones"] if d["xyz"]]
    if len(P) < 3:
        sys.exit("Se necesitan al menos 3 puntos de la mesa con profundidad válida.")
    P = np.array(P)
    lim = {"x_min": float(P[:, 0].min() - a.margen), "x_max": float(P[:, 0].max() + a.margen),
           "y_min": float(P[:, 1].min() - a.margen), "y_max": float(P[:, 1].max() + a.margen),
           "z_mesa": float(np.median(P[:, 2])), "h_max": a.h_max, "d_a": a.d_a,
           "normal": [round(c, 4) for c in normal_mesa(P[0], P[1], P[2])],
           "puntos_mesa_m": P.round(4).tolist(), "consulta": cs[-1]["fecha"]}
    VOLUMEN.write_text(json.dumps(lim, indent=2), encoding="utf-8")
    print(json.dumps(lim, indent=2))


def cmd_agarre(a):
    lim = cargar_volumen()
    for c in [c for c in leer_consultas() if c["escena"] == a.escena and c["tarea"] == "agarre"]:
        if not c["detecciones"]:
            print(f"{c['fecha']}: el modelo se ABSTIENE (lista vacía)")
            continue
        p = c["detecciones"][0]["xyz"]
        if p is None:
            print(f"{c['fecha']}: punto sin profundidad válida -> RECHAZADO")
            continue
        dentro = dentro_del_volumen(p, lim) if lim else None
        pre = pose_pre_agarre(p, lim["normal"], lim["d_a"]) if lim else None
        print(f"{c['fecha']}: punto {np.round(p, 4).tolist()} m · dentro del volumen: {dentro} · "
              f"p_pre = {None if pre is None else np.round(pre, 4).tolist()} m")


def cmd_plan(a):
    lim = cargar_volumen()
    cs = [c for c in leer_consultas() if c["escena"] == a.escena and c["tarea"] == "plan"]
    if not cs:
        sys.exit("No hay consultas de plan para esa escena")
    c = cs[-1]
    import embodied_comun as ec
    plan = ec.extraer_json(c["respuesta"])
    puntos = {d["label"]: d["xyz"] for d in c["detecciones"]}
    for i, p in enumerate(plan.get("pasos", []), 1):
        print(f"  {i}. {p.get('accion')} -> {p.get('objetivo')}")
    for regla, (ok, det) in validar_plan(plan, puntos, lim).items():
        print(f"{regla}: {'OK' if ok else ('N/A' if ok is None else 'FALLA')} {det or ''}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    v = sp.add_parser("volumen"); v.add_argument("--escena", default="regla")
    v.add_argument("--h-max", type=float, required=True); v.add_argument("--d-a", type=float, default=0.10)
    v.add_argument("--margen", type=float, default=0.0); v.set_defaults(f=cmd_volumen)
    g = sp.add_parser("agarre"); g.add_argument("--escena", required=True); g.set_defaults(f=cmd_agarre)
    p = sp.add_parser("plan"); p.add_argument("--escena", required=True); p.set_defaults(f=cmd_plan)
    a = ap.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
