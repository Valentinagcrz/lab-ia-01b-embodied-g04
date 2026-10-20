#!/usr/bin/env python3
"""
simulacion_sin_robot.py — Ensayo completo del pipeline SIN robot y SIN clave de API.

Genera escenas RGB-D sintéticas (mesa a 0.80 m, caja a 0.60 m y termo a 0.55 m) con los
intrínsecos de config_camara_kinova.json, calcula la respuesta que daría un Gemini
"perfecto" y ejecuta los subcomandos reales de embodied_sin_ros.py con --respuesta.
Todo se escribe en resultados/simulacion.csv y en capturas/sim_* para NO mezclarlo con
los datos reales del laboratorio.

    python3 simulacion_sin_robot.py

IMPORTANTE: son datos SIMULADOS. Sirven para verificar el código (E1) y ensayar los
comandos; no son evidencia experimental de las Tablas 3 a 7.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

import embodied_comun as ec
import espacio_trabajo as et

AQUI = Path(__file__).resolve().parent
CAP = AQUI / "capturas"
CSV_SIM = AQUI / "resultados" / "simulacion.csv"
ANCHO, ALTO = 640, 480           # resolución con intrínsecos en config_camara_kinova.json


def escena(cfg, objetos, z_mesa=0.80):
    """objetos: lista de (centro_xyz_color, lado_m, color_bgr). Devuelve color BGR y profundidad (mm)."""
    kd, kc, t = cfg.profundidad, cfg.color, cfg.traslacion_depth_a_color
    v, u = np.mgrid[0:kd.alto, 0:kd.ancho].astype(float)
    rx, ry = (u - kd.cx) / kd.fx, (v - kd.cy) / kd.fy
    z = np.full(u.shape, z_mesa)
    for c, lado, _ in sorted(objetos, key=lambda o: -o[0][2]):      # el más cercano se pinta al final
        cd = np.asarray(c) - t
        dentro = (np.abs(rx * cd[2] - cd[0]) < lado / 2) & (np.abs(ry * cd[2] - cd[1]) < lado / 2)
        z[dentro] = cd[2]
    depth = np.round(z * 1000).astype(np.uint16)
    depth[::7, ::11] = 0                                             # huecos como en el sensor real

    color = np.full((kc.alto, kc.ancho, 3), (185, 190, 195), np.uint8)
    for c, lado, bgr in sorted(objetos, key=lambda o: -o[0][2]):
        u0 = int(kc.fx * (c[0] - lado / 2) / c[2] + kc.cx); u1 = int(kc.fx * (c[0] + lado / 2) / c[2] + kc.cx)
        v0 = int(kc.fy * (c[1] - lado / 2) / c[2] + kc.cy); v1 = int(kc.fy * (c[1] + lado / 2) / c[2] + kc.cy)
        cv2.rectangle(color, (u0, v0), (u1, v1), bgr, -1)
    cv2.putText(color, "ESCENA SINTETICA (simulacion)", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    return color, depth


def yx(xyz, k):
    u = k.fx * xyz[0] / xyz[2] + k.cx
    v = k.fy * xyz[1] / xyz[2] + k.cy
    return [round(v / (k.alto - 1) * 1000, 1), round(u / (k.ancho - 1) * 1000, 1)]


def guardar(nombre, color, depth, nota):
    CAP.mkdir(exist_ok=True)
    cv2.imwrite(str(CAP / f"{nombre}_color.png"), color)
    cv2.imwrite(str(CAP / f"{nombre}_depth.png"), depth)
    (CAP / f"{nombre}_meta.json").write_text(json.dumps({
        "escena": nombre, "nota": nota, "simulada": True, "color": {"ancho": color.shape[1], "alto": color.shape[0]},
        "profundidad": {"ancho": depth.shape[1], "alto": depth.shape[0], "unidad": "mm",
                        "pixeles_validos_pct": round(100 * (depth > 0).mean(), 1)}}, indent=2, ensure_ascii=False))


def correr(*args):
    cmd = [sys.executable, str(AQUI / "embodied_sin_ros.py"), *args, "--grupo", "SIM", "--csv", str(CSV_SIM)]
    print("\n$ python3 embodied_sin_ros.py " + " ".join(a if " " not in a else f"'{a}'" for a in args))
    salida = subprocess.run(cmd, capture_output=True, text=True, cwd=AQUI)
    lineas, saltar = [], False
    for l in salida.stdout.splitlines():
        if l.startswith("[INFO] Prompt"):
            saltar = True
        elif l.startswith("[INFO] Respuesta"):
            saltar = False
        if not saltar and l.strip():
            lineas.append(l)
    texto = "\n".join(lineas)
    print(texto[-1500:])
    if salida.returncode:
        print(salida.stderr[-800:])
    return salida.stdout


def main():
    if CSV_SIM.exists():
        CSV_SIM.unlink()
    cfg = ec.cargar_config(None, ANCHO, ALTO)
    k = cfg.color
    caja, termo = (0.05, 0.03, 0.60), (-0.10, -0.02, 0.55)
    objetos = [(caja, 0.12, (40, 90, 200)), (termo, 0.07, (60, 160, 60))]
    color, depth = escena(cfg, objetos)
    guardar("sim_dist", color, depth, "mesa 0.80 m, caja 0.60 m, termo 0.55 m")
    d_real = float(np.linalg.norm(np.subtract(caja, termo)))
    print(f"Verdad sintética: caja {caja}, termo {termo}, distancia real {d_real:.4f} m")

    resp = json.dumps([{"point": yx(caja, k), "label": "tapa caja"}, {"point": yx(termo, k), "label": "tapa termo"}])
    correr("consultar", "--escena", "sim_dist", "--tarea", "puntos", "--objeto",
           "el centro de la tapa de la caja y el centro de la tapa del termo", "--respuesta", resp)
    correr("consultar", "--escena", "sim_dist", "--tarea", "puntos", "--sin-registro", "--objeto",
           "el centro de la tapa de la caja y el centro de la tapa del termo", "--respuesta", resp)

    # Punto cerca del borde de la caja: aquí el registro sí importa
    borde = (caja[0] - 0.06 + 0.008, caja[1], 0.60)
    guardar("sim_dist_borde", color, depth, "misma escena; punto a 8 mm del borde de la caja")
    guardar("sim_mesa", color, depth, "misma escena; esquinas de la zona útil")
    d_real_b = float(np.linalg.norm(np.subtract(borde, termo)))
    resp_b = json.dumps([{"point": yx(borde, k), "label": "borde caja"}, {"point": yx(termo, k), "label": "tapa termo"}])
    correr("consultar", "--escena", "sim_dist_borde", "--tarea", "puntos", "--objeto", "borde de la caja y tapa del termo",
           "--respuesta", resp_b)
    correr("consultar", "--escena", "sim_dist_borde", "--tarea", "puntos", "--sin-registro", "--objeto",
           "borde de la caja y tapa del termo",
           "--respuesta", resp_b)

    # Volumen de trabajo con cuatro puntos de la mesa
    esquinas = [(-0.25, -0.18, 0.80), (0.25, -0.18, 0.80), (-0.25, 0.18, 0.80), (0.25, 0.18, 0.80)]
    correr("consultar", "--escena", "sim_mesa", "--tarea", "puntos", "--objeto", "las cuatro esquinas de la zona util",
           "--respuesta", json.dumps([{"point": yx(p, k), "label": f"esquina{i}"} for i, p in enumerate(esquinas)]))
    import espacio_trabajo as et_mod
    et_mod.CSV = CSV_SIM
    et_mod.VOLUMEN = AQUI / "resultados" / "volumen_simulacion.json"
    sys.argv = ["espacio_trabajo.py", "volumen", "--escena", "sim_mesa", "--h-max", "0.30"]
    print("\n$ python3 espacio_trabajo.py volumen --escena sim_mesa --h-max 0.30")
    et_mod.main()

    # Agarre seguro / inseguro y plan (escena insegura: el termo encima de la caja)
    guardar("sim_agarre_s1", color, depth, "agarre seguro (simulado)")
    c_i, d_i = escena(cfg, [(caja, 0.12, (40, 90, 200)), ((caja[0], caja[1], 0.52), 0.06, (60, 160, 60))])
    guardar("sim_agarre_i1", c_i, d_i, "agarre inseguro: termo encima de la caja (simulado)")
    correr("consultar", "--escena", "sim_agarre_s1", "--tarea", "agarre", "--objeto", "la caja",
           "--respuesta", json.dumps([{"point": yx(caja, k), "label": "agarre"}]))
    correr("consultar", "--escena", "sim_agarre_i1", "--tarea", "agarre", "--objeto", "la caja", "--respuesta", "[]")
    plan = {"objetos": [{"point": yx(caja, k), "label": "caja"}, {"point": yx((0.18, 0.10, 0.80), k), "label": "bandeja"}],
            "pasos": [{"accion": "mover_sobre", "objetivo": "caja"}, {"accion": "bajar", "objetivo": None},
                      {"accion": "cerrar_pinza", "objetivo": None}, {"accion": "subir", "objetivo": None},
                      {"accion": "mover_sobre", "objetivo": "bandeja"}, {"accion": "bajar", "objetivo": None},
                      {"accion": "abrir_pinza", "objetivo": None}, {"accion": "subir", "objetivo": None}]}
    correr("consultar", "--escena", "sim_dist", "--tarea", "plan", "--objeto", "llevar la caja a la bandeja",
           "--respuesta", json.dumps(plan))
    for nombre, esc in (("agarre", "sim_agarre_s1"), ("plan", "sim_dist")):
        sys.argv = ["espacio_trabajo.py", nombre, "--escena", esc]
        print(f"\n$ python3 espacio_trabajo.py {nombre} --escena {esc}")
        et_mod.main()

    # Detección de éxito: antes (caja en la mesa) / después (caja movida a la bandeja)
    c_d, d_d = escena(cfg, [((0.18, 0.10, 0.60), 0.12, (40, 90, 200)), (termo, 0.07, (60, 160, 60))])
    guardar("sim_exito_bien1", c_d, d_d, "después: caja en la bandeja (simulado)")
    correr("exito", "--antes", "sim_dist", "--despues", "sim_exito_bien1", "--objeto", "la caja quedó en la bandeja",
           "--respuesta", '{"exito": true, "confianza": 0.9, "evidencia": "respuesta escrita a mano"}')

    # Análisis reproducible (Fase 10) sobre los datos simulados
    verdad = AQUI / "resultados" / "verdad_simulacion.csv"
    verdad.write_text(
        "escena,particion,relacion,objeto_esperado,u_min,v_min,u_max,v_max,segura,d_real_m,nota\n"
        f"sim_dist,-,distancia,tapa caja|tapa termo,,,,,,{d_real:.4f},centro (simulado)\n"
        f"sim_dist_borde,-,distancia,borde caja|tapa termo,,,,,,{d_real_b:.4f},borde de la caja (simulado)\n"
        "sim_agarre_s1,-,agarre,caja,300,200,430,330,si,,\n"
        "sim_agarre_i1,-,agarre,caja,300,200,430,330,no,,\n"
        "sim_exito_bien1,-,exito,caja,,,,,si,,\n", encoding="utf-8")
    import analisis_lab_ia_01b as an
    sys.argv = ["analisis_lab_ia_01b.py", "--csv", str(CSV_SIM), "--verdad", str(verdad),
                "--salida", str(AQUI / "resultados" / "tablas_simulacion.md")]
    print("\n$ python3 analisis_lab_ia_01b.py --csv resultados/simulacion.csv --verdad resultados/verdad_simulacion.csv")
    an.main()
    print("\n[OK] Simulación terminada. Resultados en resultados/simulacion.csv y capturas/sim_*")


if __name__ == "__main__":
    main()
