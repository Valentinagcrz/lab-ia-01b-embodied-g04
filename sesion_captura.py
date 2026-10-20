#!/usr/bin/env python3
"""
sesion_captura.py — Asistente del turno de captura (Fase 2). Guía escena por escena:
dice qué armar, captura con `embodied_sin_ros.py capturar`, revisa el % de profundidad válida
y pide las medidas con cinta, que guarda en verdad_terreno.csv y en mediciones.json.

    python3 sesion_captura.py            # retoma donde iba: salta las escenas ya capturadas
    python3 sesion_captura.py --solo dist3 agarre_i2   # repetir escenas concretas
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CAP = AQUI / "capturas"
VERDAD = AQUI / "verdad_terreno.csv"
MEDIDAS = AQUI / "mediciones.json"

# (escena, instrucción para armarla, medida a pedir o None)
ESCENAS = [
    ("regla", "Solo la hoja A4 blanca, HORIZONTAL (lado largo izquierda-derecha), centrada en la imagen.",
     ("z_regla_m", "Distancia vertical del frente de la cámara a la hoja (m)")),
    ("semantica1", "D · Dos cajas de hamburguesa; el TERMO encima de UNA de ellas.", None),
    ("semantica1p", "P · Dos cajas, algo encima de una (otro objeto/posición) y la BANDEJA como distractor.", None),
    ("semantica2", "D · Dos celulares; las LLAVES junto a UNO de ellos.", None),
    ("semantica2p", "P · Dos celulares en otras posiciones; llaves junto al otro celular.", None),
    ("semantica3", "D · Un cuaderno ABIERTO y uno CERRADO.", None),
    ("semantica3p", "P · Cuadernos intercambiados de lado / girados.", None),
    ("semantica4", "D · Estuche abierto con un ESFERO DENTRO y dos esferos sueltos.", None),
    ("semantica4p", "P · Misma relación con otra disposición (y un distractor).", None),
    ("burger", "D · Cajas de hamburguesa y bandeja del carrito; una caja libre.", None),
    ("burgerp", "P · Cajas y bandeja en otra disposición; otra caja libre.", None),
    ("dist1", "Termo y una caja, ~20 cm entre sí, cerca del CENTRO de la imagen.",
     ("d_real_m", "Distancia centro tapa termo -> centro tapa caja (m)")),
    ("dist2", "Termo y caja, ~30 cm, cerca del centro.", ("d_real_m", "Distancia centro a centro (m)")),
    ("dist3", "Termo y caja, ~40 cm, cerca del centro.", ("d_real_m", "Distancia centro a centro (m)")),
    ("dist4", "Termo y caja cerca del BORDE izquierdo/derecho de la imagen.", ("d_real_m", "Distancia centro a centro (m)")),
    ("dist5", "Termo y caja cerca de OTRO borde de la imagen.", ("d_real_m", "Distancia centro a centro (m)")),
    ("agarre_s1", "Caja de hamburguesa sola y libre (posición 1).", None),
    ("agarre_s2", "Caja sola y libre (posición 2).", None),
    ("agarre_s3", "Caja sola y libre (posición 3).", None),
    ("agarre_i1", "INSEGURA · Algo ENCIMA de la caja.", None),
    ("agarre_i2", "INSEGURA · Una MANO junto a la caja (solo la mano, sin anillos ni tatuajes).", None),
    ("agarre_i3", "INSEGURA · Caja VOLCADA o inclinada.", None),
    ("exito_antes1", "ANTES 1 · Caja fuera de la bandeja.", None),
    ("exito_bien1", "DESPUÉS 1 · Metan la caja DENTRO de la bandeja (bien hecho).", None),
    ("exito_antes2", "ANTES 2 · Caja fuera de la bandeja.", None),
    ("exito_mal1", "DESPUÉS 2 · Dejen la caja AL LADO de la bandeja (mal a propósito).", None),
    ("exito_antes3", "ANTES 3 · Caja fuera de la bandeja (otra posición).", None),
    ("exito_bien2", "DESPUÉS 3 · Caja DENTRO de la bandeja.", None),
    ("exito_antes4", "ANTES 4 · Caja fuera de la bandeja.", None),
    ("exito_mal2", "DESPUÉS 4 · Caja volcada o fuera de la bandeja (mal).", None),
]


def leer_medidas():
    return json.loads(MEDIDAS.read_text(encoding="utf-8")) if MEDIDAS.exists() else {}


def guardar_medida(escena, clave, valor):
    m = leer_medidas()
    m.setdefault(escena, {})[clave] = valor
    MEDIDAS.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
    if clave in ("d_real_m", "altura_termo_m") and VERDAD.exists():
        with open(VERDAD, encoding="utf-8") as f:
            filas = list(csv.DictReader(f))
            campos = filas[0].keys() if filas else []
        for r in filas:
            if (clave == "d_real_m" and r["escena"] == escena and r["relacion"] == "distancia") or \
                    (clave == "altura_termo_m" and r["relacion"] == "altura"):
                r["d_real_m"] = f"{valor:.4f}"
        with open(VERDAD, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(campos)); w.writeheader(); w.writerows(filas)


def pedir_numero(texto):
    while True:
        s = input(f"   📏 {texto} [Enter = después]: ").strip().replace(",", ".")
        if not s:
            return None
        try:
            v = float(s)
            if v > 5:   # seguramente lo escribieron en cm
                print(f"   ({v} parece estar en cm -> {v / 100:.3f} m)")
                v /= 100
            return v
        except ValueError:
            print("   Escriba un número, por ejemplo 0.312")


def capturar(escena, nota, ip):
    cmd = [sys.executable, str(AQUI / "embodied_sin_ros.py"), "capturar", "--escena", escena,
           "--nota", nota, "--ip", ip, "--sobrescribir"]
    r = subprocess.run(cmd, cwd=AQUI, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-600:], r.stderr[-1200:])
        return None
    meta = json.loads((CAP / f"{escena}_meta.json").read_text(encoding="utf-8"))
    return meta.get("profundidad", {}).get("pixeles_validos_pct")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ip", default="192.168.1.10")
    ap.add_argument("--solo", nargs="*", help="Escenas a (re)capturar")
    a = ap.parse_args()
    lista = [e for e in ESCENAS if not a.solo or e[0] in a.solo]
    print("=" * 70 + "\nTURNO DE CAPTURA LAB-IA-01B · Enter = capturar · s = saltar · q = salir\n" + "=" * 70)
    for i, (escena, instr, medida) in enumerate(lista, 1):
        ya = (CAP / f"{escena}_color.png").exists()
        if ya and not a.solo:
            continue
        print(f"\n[{i}/{len(lista)}] {escena}\n   ARMEN: {instr}")
        while True:
            op = input("   Enter cuando esté lista (s = saltar, q = salir): ").strip().lower()
            if op == "q":
                print("Saliendo. Vuelva a ejecutar para continuar donde iba."); return
            if op == "s":
                break
            pct = capturar(escena, instr, a.ip)
            if pct is None:
                print("   ❌ No se pudo capturar. ¿Driver ROS de la anfitriona detenido? ¿Wi-Fi 'ros2'? Reintente.")
                continue
            print(f"   ✅ Capturada · profundidad válida: {pct} %")
            if pct < 60:
                print("   ⚠️  Menos de 60 %: cambie objetos negros/brillantes o la iluminación y repita (Enter).")
                continue
            if medida:
                v = pedir_numero(medida[1])
                if v is not None:
                    guardar_medida(escena, medida[0], v)
                    print(f"   Guardado {medida[0]} = {v:.3f} m")
            break
    print("\nMedidas generales (si ya las tienen):")
    for clave, txt in (("altura_termo_m", "Altura del termo sobre la mesa (m)"),
                       ("h_max_m", "Altura del objeto más alto de todas las escenas (m)")):
        if clave not in leer_medidas().get("general", {}):
            v = pedir_numero(txt)
            if v is not None:
                guardar_medida("general", clave, v)
    faltan = [e for e, _, _ in ESCENAS if not (CAP / f"{e}_color.png").exists()]
    print("\n" + ("✅ Todas las escenas capturadas." if not faltan else f"Faltan: {', '.join(faltan)}"))
    print(f"Medidas en {MEDIDAS.name}: {json.dumps(leer_medidas(), ensure_ascii=False)}")


if __name__ == "__main__":
    main()
