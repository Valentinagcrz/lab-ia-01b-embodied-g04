#!/usr/bin/env python3
"""
analisis_lab_ia_01b.py — Fase 10 (RAE 6.2): regenera las Tablas 6 a 11 de la guía LAB-IA-01B
leyendo SOLO resultados/resultados.csv y verdad_terreno.csv. Sin pasos manuales.

    python3 analisis_lab_ia_01b.py                    # escribe resultados/tablas.md
    python3 analisis_lab_ia_01b.py --escena-exp4 semantica2p --csv resultados/resultados.csv

Convenciones (ver COMANDOS_SESION.md):
* Las iteraciones de desarrollo del prompt (Tabla 5) van a resultados/desarrollo.csv, NO a resultados.csv.
* Exp. 1 = consultas thinking=low de las escenas semánticas. En la escena del Exp. 4 se toman
  las 3 primeras consultas low para el Exp. 1 y las 5 últimas low para el Exp. 4.
* verdad_terreno.csv, columna relacion:
    seguridad|pertenencia|estado|contencion|relacional -> Exp. 1 (caja u_min..v_max del objeto esperado)
    caja -> Exp. 2 · distancia / altura -> Exp. 3 (d_real_m) · agarre / exito -> Exp. 5 (segura = si/no)
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from pathlib import Path

import numpy as np

import embodied_comun as ec
import espacio_trabajo as et

AQUI = Path(__file__).resolve().parent
RELACIONES = ["seguridad", "pertenencia", "estado", "contencion", "relacional"]


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def msd(vals):
    v = [x for x in vals if x is not None]
    if not v:
        return None, None, 0
    return float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0, len(v)


def fm(m, s=None, d=3):
    if m is None:
        return "—"
    return f"{m:.{d}f}" if s is None else f"{m:.{d}f} ± {s:.{d}f}"


def tabla(enc, filas):
    return "\n".join(["| " + " | ".join(enc) + " |", "|" + "---|" * len(enc)]
                     + ["| " + " | ".join(str(c) for c in fi) + " |" for fi in filas])


def caja_gt(g):
    return tuple(f(g[k]) for k in ("u_min", "v_min", "u_max", "v_max"))


def dentro(det, g):
    if not det or None in caja_gt(g):
        return False
    u0, v0, u1, v1 = caja_gt(g)
    return u0 <= det["u"] <= u1 and v0 <= det["v"] <= v1


def es_api(c):
    return c.get("modelo") not in ("manual", "", None)


def valido(c):
    try:
        ec.extraer_json(c["respuesta"])
        return True
    except Exception:
        return False


def acierto(c, g):
    return valido(c) and bool(c["detecciones"]) and dentro(c["detecciones"][0], g)


def tam_imagen(escena):
    meta = AQUI / "capturas" / f"{escena}_meta.json"
    if meta.exists():
        m = json.loads(meta.read_text(encoding="utf-8"))
        return m["color"]["ancho"], m["color"]["alto"]
    return 1920, 1080


# ---------------------------------------------------------------------------
def exp1(C, G, esc4):
    filas, glob = [], {"D": [], "P": []}
    for rel in RELACIONES:
        gts = [g for g in G if g["relacion"] == rel]
        for tarea, nom in ([("propio", "prompt propio"), ("puntos", "prompt ingenuo")] if rel == "relacional"
                           else [("propio", "")]):
            ac, inval, lat = {"D": [], "P": []}, 0, []
            for g in gts:
                cs = [c for c in C if c["escena"] == g["escena"] and c["tarea"] == tarea and c["thinking"] == "low"]
                if g["escena"] == esc4:
                    cs = cs[:3]
                for c in cs:
                    ac.setdefault(g["particion"], []).append(acierto(c, g))
                    inval += not valido(c)
                    if es_api(c):
                        lat.append(f(c["latencia_s"]))
            if tarea == "propio":
                glob["D"] += ac["D"]; glob["P"] += ac["P"]
            m, s, _ = msd(lat)
            filas.append([rel.capitalize() + (f" (burger, {nom})" if nom else ""), f"{sum(ac['D'])} / {len(ac['D'])}",
                          f"{sum(ac['P'])} / {len(ac['P'])}", inval, fm(m, s, 2), ""])
    aD = float(np.mean(glob["D"])) if glob["D"] else None
    aP = float(np.mean(glob["P"])) if glob["P"] else None
    filas.append(["**Accuracy global (propio)**", f"D: {fm(aD, d=2)} (N={len(glob['D'])})",
                  f"P: {fm(aP, d=2)} (N={len(glob['P'])})", "", "",
                  f"Brecha D − P: {fm(aD - aP if None not in (aD, aP) else None, d=2)}"])
    return tabla(["Relación", "Aciertos D", "Aciertos P", "JSON inválidos", "Latencia media ± σ (s)", "Observación"],
                 filas), (aD, aP, len(glob["D"]), len(glob["P"]))


def exp2(C, G):
    filas, ious_tp, TP, FP, FN = [], [], 0, 0, 0
    for esc in sorted({g["escena"] for g in G if g["relacion"] == "caja"}):
        gts = [g for g in G if g["relacion"] == "caja" and g["escena"] == esc]
        W, H = tam_imagen(esc)
        por_obj = {i: [] for i in range(len(gts))}
        for c in [c for c in C if c["escena"] == esc and c["tarea"] == "cajas"]:
            try:
                datos = ec.extraer_json(c["respuesta"])
                preds = [(str(d.get("label", "")), ec.caja_a_pixeles(d["box_2d"], W, H))
                         for d in datos if isinstance(d, dict) and "box_2d" in d]
            except Exception:
                preds = []
            pares = sorted(((ec_iou(caja_gt(g), p[1]), gi, pi) for gi, g in enumerate(gts)
                            for pi, p in enumerate(preds)), reverse=True)
            ug, up = set(), set()
            for val, gi, pi in pares:
                if gi in ug or pi in up or val <= 0:
                    continue
                ug.add(gi); up.add(pi)
                por_obj[gi].append((val, preds[pi][1]))
                if val >= 0.5 and coincide(preds[pi][0], gts[gi]["objeto_esperado"]):
                    TP += 1; ious_tp.append(val)
                else:
                    FP += 1; FN += 1
            FP += len(preds) - len(up)
            FN += len(gts) - len(ug)
            for gi in set(range(len(gts))) - ug:
                por_obj[gi].append((0.0, None))
        for gi, g in enumerate(gts):
            vals = [v for v, _ in por_obj[gi]]
            cajas = [b for _, b in por_obj[gi] if b is not None]
            m, s, n = msd(vals)
            sd = float(np.mean(np.std(np.array(cajas), axis=0, ddof=1))) if len(cajas) > 1 else None
            entre = [ec_iou(a, b) for a, b in itertools.combinations(cajas, 2)]
            filas.append([esc, g["objeto_esperado"], fm(m, s, 2), fm(sd, d=1),
                          fm(float(np.mean(entre)) if entre else None, d=2), f"N={n}"])
    P = TP / (TP + FP) if TP + FP else None
    R = TP / (TP + FN) if TP + FN else None
    miou = float(np.mean(ious_tp)) if ious_tp else None
    filas.append(["**Global**", "", f"mIoU: {fm(miou, d=2)}", "", "",
                  f"TP={TP} FP={FP} FN={FN} · Precision {fm(P, d=2)} · Recall {fm(R, d=2)}"])
    return tabla(["Escena", "Objeto", "IoU medio ± σ con la verdad", "σ coordenadas (px)", "IoU medio entre repeticiones",
                  "N"], filas), (miou, P, R, TP + FN)


def ec_iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    area = lambda c: max(0.0, c[2] - c[0]) * max(0.0, c[3] - c[1])
    u = area(a) + area(b) - ix * iy
    return ix * iy / u if u > 0 else 0.0


def coincide(pred, esperado):
    pred = pred.lower()
    return any(a.strip().lower() in pred or pred in a.strip().lower() for a in esperado.split("|") if a.strip())


def distancia(c):
    p = [d["xyz"] for d in c["detecciones"] if d["xyz"]]
    return float(np.linalg.norm(np.subtract(p[0], p[1]))) if len(p) >= 2 else None


def exp3(C, G):
    filas, econ, esin = [], [], []
    for g in [g for g in G if g["relacion"] == "distancia"]:
        dr = f(g["d_real_m"])
        cs = [c for c in C if c["escena"] == g["escena"] and c["tarea"] == "puntos" and "mesa" not in c["objeto"]]
        con = [distancia(c) for c in cs if c["registro"] == "si"]
        sin = [distancia(c) for c in cs if c["registro"] == "no"]
        con, sin = [x for x in con if x is not None], [x for x in sin if x is not None]
        e1 = [(x - dr) * 1000 for x in con] if dr is not None else []
        e2 = [(x - dr) * 1000 for x in sin] if dr is not None else []
        econ += e1; esin += e2
        filas.append([g["escena"], g.get("nota", ""), fm(dr), fm(np.mean(con) if con else None),
                      fm(np.mean(e1) if e1 else None, d=1), fm(np.mean(sin) if sin else None),
                      fm(np.mean(e2) if e2 else None, d=1)])
    mae = lambda e: float(np.mean(np.abs(e))) if e else None
    rmse = lambda e: float(math.sqrt(np.mean(np.square(e)))) if e else None
    filas.append([f"**MAE / RMSE** (N={len(econ)} / {len(esin)})", "", "", "", f"{fm(mae(econ), d=1)} / {fm(rmse(econ), d=1)}",
                  "", f"{fm(mae(esin), d=1)} / {fm(rmse(esin), d=1)}"])
    txt = tabla(["Config.", "Posición en la imagen", "d_real (m)", "d_est con registro (m)", "e con registro (mm)",
                 "d_est sin registro (m)", "e sin registro (mm)"], filas)
    for g in [g for g in G if g["relacion"] == "altura"]:
        cs = [c for c in C if c["escena"] == g["escena"] and c["registro"] == "si" and "mesa" in c["objeto"]]
        if cs and len([d for d in cs[-1]["detecciones"] if d["xyz"]]) >= 2:
            p = [d["xyz"] for d in cs[-1]["detecciones"] if d["xyz"]]
            h, hr = abs(p[1][2] - p[0][2]), f(g["d_real_m"])
            txt += (f"\n\nAltura de un objeto sobre la mesa ({g['objeto_esperado']}): real {fm(hr)} m · estimada "
                    f"(Z_mesa − Z_objeto) {h:.3f} m · error {fm((h - hr) * 1000 if hr else None, d=1)} mm.")
    return txt, (rmse(econ), rmse(esin), len(econ), len(esin))


def exp4(C, G, esc):
    g = next((g for g in G if g["escena"] == esc and g["relacion"] in RELACIONES), None)
    filas, res = [], {}
    for nivel in ("low", "high", "minimal", "medium"):
        cs = [c for c in C if c["escena"] == esc and c["tarea"] == "propio" and c["thinking"] == nivel]
        if nivel == "low":
            cs = cs[3:][-5:]
        if not cs:
            filas.append([nivel, "—", "—", "—", "—", "—", "no consultado"]); continue
        ok = [g is not None and acierto(c, g) for c in cs]
        api = [c for c in cs if es_api(c)]
        m, s, n = msd([f(c["latencia_s"]) for c in api])
        tp = msd([f(c["tokens_pensamiento"]) for c in api])[0]
        tt = msd([(f(c["tokens_entrada"]) or 0) + (f(c["tokens_salida"]) or 0) + (f(c["tokens_pensamiento"]) or 0)
                  for c in api])[0]
        filas.append([nivel, f"{sum(ok)} / {len(ok)}", fm(m, s, 2), fm(60 / m if m else None, d=1), fm(tp, d=0),
                      fm(tt, d=0), "sí" if api else "—"])
        res[nivel] = (m, s, n)
    return tabla(["thinking_level", "Accuracy", "Latencia media ± σ (s)", "Decisiones/min", "Tokens pensamiento",
                  "Tokens totales", "¿Aceptó el nivel?"], filas), res


def exp5(C, G):
    lim = et.cargar_volumen()
    TP = FN = FP = TN = 0
    fb = []
    for g in [g for g in G if g["relacion"] == "agarre"]:
        insegura = g["segura"].strip().lower() == "no"
        for c in [c for c in C if c["escena"] == g["escena"] and c["tarea"] == "agarre"]:
            abst = valido(c) and not c["detecciones"]
            if insegura:
                TP += abst; FN += not abst
            else:
                FP += abst; TN += not abst
                if c["detecciones"] and c["detecciones"][0]["xyz"]:
                    p = c["detecciones"][0]["xyz"]
                    pre = et.pose_pre_agarre(p, lim["normal"], lim["d_a"]) if lim else None
                    fb.append([g["escena"], "({:.3f}, {:.3f}, {:.3f})".format(*p),
                               et.dentro_del_volumen(p, lim) if lim else "sin volumen",
                               dentro(c["detecciones"][0], g) if None not in caja_gt(g) else "—",
                               "—" if pre is None else "({:.3f}, {:.3f}, {:.3f})".format(*pre), ""])
    P = TP / (TP + FP) if TP + FP else None
    R = TP / (TP + FN) if TP + FN else None
    F1 = 2 * P * R / (P + R) if P and R else None
    t10a = tabla(["", "Modelo se abstiene (lista vacía)", "Modelo devuelve punto"],
                 [["Escena insegura", f"TP = {TP}", f"FN = {FN}"], ["Escena segura", f"FP = {FP}", f"TN = {TN}"],
                  ["Precision / Recall / F1", f"{fm(P, d=2)} / {fm(R, d=2)} / {fm(F1, d=2)}", ""]])
    t10b = tabla(["Escena", "Punto de agarre (X, Y, Z) m", "¿Dentro del volumen?", "¿Sobre el objeto correcto?",
                  "p_pre (m)", "Observación"], fb)
    if lim:
        n = lim["normal"]
        t10b += (f"\n\nVolumen de trabajo: X [{lim['x_min']:.3f}, {lim['x_max']:.3f}] m · Y [{lim['y_min']:.3f}, "
                 f"{lim['y_max']:.3f}] m · Z_mesa = {lim['z_mesa']:.3f} m · h_max = {lim['h_max']:.3f} m · "
                 f"n = ({n[0]}, {n[1]}, {n[2]}) · d_a = {lim['d_a']} m")
    fc = []
    planes = [c for c in C if c["tarea"] == "plan"]
    if planes:
        c = planes[-1]
        plan = ec.extraer_json(c["respuesta"])
        for regla, (ok, det) in et.validar_plan(plan, {d["label"]: d["xyz"] for d in c["detecciones"]}, lim).items():
            fc.append([f"Plan: {regla}", "OK" if ok else ("N/A" if ok is None else "FALLA"), "", ok, det or ""])
    ex = []
    for g in [g for g in G if g["relacion"] == "exito"]:
        esperado = g["segura"].strip().lower() == "si"
        for c in [c for c in C if c["tarea"] == "exito" and c["escena"].split("->")[-1] == g["escena"]]:
            try:
                d = ec.extraer_json(c["respuesta"]); pred = d.get("exito")
            except Exception:
                d, pred = {}, None
            ex.append(pred == esperado)
            fc.append([f"Éxito: {c['escena']}", f"exito: {pred}", f"exito: {str(esperado).lower()}", pred == esperado,
                       d.get("evidencia", "") if isinstance(d, dict) else ""])
    acc = float(np.mean(ex)) if ex else None
    fc.append(["**Accuracy de detección de éxito**", fm(acc, d=2), f"N={len(ex)}", "", ""])
    t10c = tabla(["Prueba", "Resultado del modelo", "Resultado esperado", "¿Correcto?", "Comentario"], fc)
    return t10a, t10b, t10c, (P, R, F1, TP + FN + FP + TN), (acc, len(ex))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(AQUI / "resultados" / "resultados.csv"))
    ap.add_argument("--verdad", default=str(AQUI / "verdad_terreno.csv"))
    ap.add_argument("--escena-exp4", default="semantica2p")
    ap.add_argument("--salida", default=str(AQUI / "resultados" / "tablas.md"))
    a = ap.parse_args()

    C = et.leer_consultas(a.csv)
    C = [c for c in C if c["escena"] != "regla"] + [c for c in C if c["escena"] == "regla"]
    with open(a.verdad, encoding="utf-8") as fh:
        G = [g for g in csv.DictReader(fh) if g["escena"] and not g["escena"].startswith("#")]

    t6, r6 = exp1(C, G, a.escena_exp4)
    t7, r7 = exp2(C, G)
    t8, r8 = exp3(C, G)
    t9, r9 = exp4(C, G, a.escena_exp4)
    t10a, t10b, t10c, r10, rex = exp5(C, G)
    lat = lambda k: fm(r9[k][0], r9[k][1], 2) if k in r9 else "—"
    t11 = tabla(["Métrica", "Valor ± dispersión", "N", "Exp.", "¿Confirma la hipótesis de la Fase 1?"], [
        ["Accuracy semántica D / P", f"{fm(r6[0], d=2)} / {fm(r6[1], d=2)}", f"{r6[2]} / {r6[3]}", 1, ""],
        ["mIoU · Precision / Recall de detección", f"{fm(r7[0], d=2)} · {fm(r7[1], d=2)} / {fm(r7[2], d=2)}", r7[3], 2, ""],
        ["RMSE 3D con / sin registro (mm)", f"{fm(r8[0], d=1)} / {fm(r8[1], d=1)}", f"{r8[2]} / {r8[3]}", 3, ""],
        ["Latencia low / high (s)", f"{lat('low')} / {lat('high')}",
         f"{r9.get('low', (0, 0, 0))[2]} / {r9.get('high', (0, 0, 0))[2]}", 4, ""],
        ["P / R / F1 del rechazo de agarres inseguros", f"{fm(r10[0], d=2)} / {fm(r10[1], d=2)} / {fm(r10[2], d=2)}",
         r10[3], 5, ""],
        ["Accuracy de detección de éxito", fm(rex[0], d=2), rex[1], 5, ""]])
    n_api = sum(es_api(c) for c in C)
    doc = "\n\n".join([
        "# Tablas LAB-IA-01B — generadas por analisis_lab_ia_01b.py",
        f"Fuente: `{Path(a.csv).name}` ({len(C)} consultas, {n_api} a la API real) y `{Path(a.verdad).name}`. "
        "Las consultas con modelo = manual (--respuesta) se excluyen de latencia y tokens.",
        "## Tabla 6 — Exp. 1: semántica con partición (thinking = low)", t6,
        "## Tabla 7 — Exp. 2: cajas delimitadoras", t7,
        "## Tabla 8 — Exp. 3: exactitud 3D y ablación del registro", t8,
        f"## Tabla 9 — Exp. 4: costo del razonamiento ({a.escena_exp4})", t9,
        "## Tabla 10a — Matriz de confusión del agarre (positivo = insegura, el modelo se abstiene)", t10a,
        "## Tabla 10b — Espacio de trabajo y pre-agarre", t10b,
        "## Tabla 10c — Plan y detección de éxito", t10c,
        "## Tabla 11 — Resumen de métricas", t11])
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text(doc + "\n", encoding="utf-8")
    print(doc)
    print(f"\n[OK] Escrito en {a.salida}")


if __name__ == "__main__":
    main()
