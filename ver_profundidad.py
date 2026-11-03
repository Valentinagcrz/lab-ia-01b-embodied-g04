#!/usr/bin/env python3
"""ver_profundidad.py — Convierte las imágenes de profundidad (16 bits, mm) en imágenes a color para presentar.

Por cada escena genera capturas/profundidad_vista/<escena>_profundidad.png con la foto de color a la
izquierda y la profundidad coloreada a la derecha (rojo = cerca de la cámara, azul = lejos, negro = sin dato).

    python3 ver_profundidad.py              # todas las escenas
    python3 ver_profundidad.py dist3 regla  # solo esas
"""
import sys
from pathlib import Path

import cv2
import numpy as np

AQUI = Path(__file__).resolve().parent
CAP = AQUI / "capturas"
SALIDA = CAP / "profundidad_vista"
Z_MIN, Z_MAX = 450, 750  # mm: rango de colores (objetos ~0.50 m, mesa ~0.70 m)


def vista(escena):
    d = cv2.imread(str(CAP / f"{escena}_depth.png"), cv2.IMREAD_UNCHANGED)
    if d is None:
        return False
    validos = d > 0
    norm = np.clip((d.astype(np.float32) - Z_MIN) / (Z_MAX - Z_MIN), 0, 1)
    color_d = cv2.applyColorMap((255 * (1 - norm)).astype(np.uint8), cv2.COLORMAP_JET)
    color_d[~validos] = 0
    alto = 540
    color_d = cv2.resize(color_d, (alto * d.shape[1] // d.shape[0], alto), interpolation=cv2.INTER_NEAREST)
    partes = [color_d]
    foto = cv2.imread(str(CAP / f"{escena}_color.png"))
    if foto is not None:
        partes.insert(0, cv2.resize(foto, (alto * foto.shape[1] // foto.shape[0], alto)))
    img = np.hstack(partes)
    # barra de colores
    barra = np.zeros((60, img.shape[1], 3), np.uint8)
    x0, x1 = img.shape[1] - 520, img.shape[1] - 20
    for x in range(x0, x1):
        t = (x - x0) / (x1 - x0)
        c = cv2.applyColorMap(np.uint8([[255 * (1 - t)]]), cv2.COLORMAP_JET)[0, 0]
        barra[10:30, x] = c
    f = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(barra, f"{Z_MIN} mm (cerca)", (x0, 52), f, 0.5, (255, 255, 255), 1)
    cv2.putText(barra, f"{Z_MAX} mm (lejos)", (x1 - 130, 52), f, 0.5, (255, 255, 255), 1)
    pct = 100 * validos.mean()
    cv2.putText(barra, f"{escena}   negro = sin dato ({100 - pct:.0f} %)", (15, 38), f, 0.7, (255, 255, 255), 2)
    SALIDA.mkdir(exist_ok=True)
    cv2.imwrite(str(SALIDA / f"{escena}_profundidad.png"), np.vstack([img, barra]))
    return True


if __name__ == "__main__":
    escenas = sys.argv[1:] or sorted(p.name[:-10] for p in CAP.glob("*_depth.png") if not p.name.startswith("sim_"))
    hechas = [e for e in escenas if vista(e)]
    print(f"{len(hechas)} imágenes en {SALIDA.relative_to(AQUI)}")
