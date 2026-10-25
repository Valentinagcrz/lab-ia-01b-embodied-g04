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
import time
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
    ("dist1", "Termo DE PIE y una caja, ~10 cm entre sí, cerca del CENTRO. Los dos COMPLETOS en la imagen (ve ~38x21 cm).",
     ("d_real_m", "Distancia centro tapa termo -> centro tapa caja (m)")),
    ("dist2", "Termo de pie y caja, ~15 cm, cerca del centro, ambos completos.", ("d_real_m", "Distancia centro a centro (m)")),
    ("dist3", "Termo de pie y caja, ~20 cm, cerca del centro, ambos completos.", ("d_real_m", "Distancia centro a centro (m)")),
    ("dist4", "Termo y caja ~15 cm, pegados al borde DERECHO de la imagen (no el izquierdo), completos.", ("d_real_m", "Distancia centro a centro (m)")),
    ("dist5", "Termo y caja ~20 cm, cerca del borde de ARRIBA o ABAJO a la derecha, completos. Sin manos.", ("d_real_m", "Distancia centro a centro (m)")),
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


def vista_previa(ip, escena, instr):
    """Muestra la cámara de color EN VIVO hasta que el usuario decida. Devuelve 'c', 's', 'q' o None.

    Un hilo lee la cámara y guarda solo el último cuadro; la ventana siempre se refresca, y si no llegan
    cuadros por 2.5 s se cierra y se vuelve a abrir el stream (la imagen 1080p por Wi-Fi se atasca a veces).
    Cuadrícula: cuadros de 5 cm a la altura de la mesa (Z = 0.51 m). La cámara solo acepta un consumidor,
    por eso el stream se cierra antes de capturar.
    """
    import threading
    import cv2
    import numpy as np
    sys.path.insert(0, str(AQUI))
    from embodied_sin_ros import abrir_stream

    estado = {"frame": None, "t": 0.0, "cap": None, "vivo": True, "error": ""}

    def lector():
        while estado["vivo"]:
            if estado["cap"] is None:
                try:
                    estado["cap"] = abrir_stream(ip, "color", 100)
                    estado["t"] = time.time()
                except Exception as e:  # noqa: BLE001
                    estado["error"] = str(e)[:80]
                    time.sleep(1.0)
                    continue
            ok, f = estado["cap"].read()
            if ok:
                estado["frame"], estado["t"], estado["error"] = f, time.time(), ""
            elif time.time() - estado["t"] > 2.5:
                estado["cap"].release(); estado["cap"] = None

    hilo = threading.Thread(target=lector, daemon=True)
    hilo.start()
    fx, z = 2562.0, 0.51
    paso = int(round(fx * 0.05 / z)) // 2                 # 5 cm en la mesa, en la imagen a mitad de tamaño
    tecla = None
    while tecla is None:
        f = estado["frame"]
        if f is None:
            img = np.zeros((540, 960, 3), np.uint8)
            cv2.putText(img, "Conectando con la camara... " + estado["error"], (20, 270),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            img = cv2.resize(f, (960, 540), interpolation=cv2.INTER_AREA)
            for x in range(480 % paso, 960, paso):
                cv2.line(img, (x, 0), (x, 540), (0, 255, 255), 1)
            for y in range(270 % paso, 540, paso):
                cv2.line(img, (0, y), (960, y), (0, 255, 255), 1)
            cv2.rectangle(img, (0, 0), (115, 540), (0, 0, 255), 2)       # franja izquierda sin profundidad
            edad = time.time() - estado["t"]
            if edad > 1.0:
                cv2.putText(img, f"imagen congelada {edad:.0f} s - reconectando...", (200, 300),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        cv2.putText(img, f"{escena}:  c = capturar   s = saltar   q = salir   (cuadros de 5 cm)", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(img, instr[:110], (10, 525), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.imshow("VISTA PREVIA", img)
        k = cv2.waitKey(40) & 0xFF
        if k in (ord("c"), ord("s"), ord("q"), 13, 32):
            tecla = "c" if k in (13, 32) else chr(k)
    estado["vivo"] = False
    hilo.join(timeout=4)
    if estado["cap"] is not None:
        estado["cap"].release()
    cv2.destroyAllWindows()
    for _ in range(5):
        cv2.waitKey(1)
    time.sleep(1.5)                       # dar tiempo a que la cámara libere la conexión antes de capturar
    return tecla


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
    ap.add_argument("--sin-vista", dest="vista", action="store_false", help="No mostrar la cámara en vivo")
    a = ap.parse_args()
    lista = [e for e in ESCENAS if not a.solo or e[0] in a.solo]
    print("=" * 70 + "\nTURNO DE CAPTURA LAB-IA-01B · Enter = capturar · s = saltar · q = salir\n" + "=" * 70)
    for i, (escena, instr, medida) in enumerate(lista, 1):
        ya = (CAP / f"{escena}_color.png").exists()
        if ya and not a.solo:
            continue
        print(f"\n[{i}/{len(lista)}] {escena}\n   ARMEN: {instr}")
        while True:
            op = vista_previa(a.ip, escena, instr) if a.vista else None
            if op is None:
                op = input("   Enter cuando esté lista (s = saltar, q = salir): ").strip().lower()
            elif op == "c":
                op = ""
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
