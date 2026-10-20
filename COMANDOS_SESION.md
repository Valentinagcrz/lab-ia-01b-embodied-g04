# LAB-IA-01B: comandos en orden (Ruta A, sin ROS 2)

Grupo: Mariana Ladino, Cristian Quintero, Sara García y Gabriel González. El repositorio es `burger-kinova-equipo-04`; confirmen con el docente si el grupo es G04.

Ábranlo en Antigravity con *File → Open Workspace from File → `LAB_IA_01B_Ruta_A.code-workspace`*. La terminal de Ubuntu se abre con *Terminal → New Terminal*. Si sale PowerShell, escriban `wsl -d Ubuntu-24.04`.

En cada terminal nueva:
```bash
cd "/mnt/d/ULTIMITO SEMESTRE/IA/labx/plantilla_lab_ia_embodied"
source ~/venv_embodied/bin/activate        # después de la instalación de la Fase 0
export GEMINI_API_KEY="su-clave"           # nunca en el código
G=G04
```
📸 = pantallazo para el instrumento ABET.

---
## Fase 0: entorno y prueba sin robot (ya se puede hacer)
```bash
sudo apt install -y python3-venv gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-libav
python3 -m venv --system-site-packages ~/venv_embodied && source ~/venv_embodied/bin/activate
pip install -r requirements.txt
python3 --version && pip show google-genai | head -2          # 📸 Tabla 1
python3 -m pytest tests -q                                     # 📸 E1: 15 passed
python3 simulacion_sin_robot.py                                # ensayo completo con datos SIMULADOS (no es evidencia)
git init -q 2>/dev/null; git add -A && git commit -m "TODO 1-4 resueltos" && git log --oneline -1   # SHA para la Tabla 1
```

## Fase 1: antes de capturar
- Revisen con el docente la matriz de pruebas (Tabla 2 del instrumento, ya llena).
- Escriban las hipótesis (ya redactadas en el instrumento) **antes** de ver datos.
- La persona que arma las escenas P no debe ser la que escribe el prompt.

## Fase 2: captura (turno de 15 min, con el driver ROS de la anfitriona detenido)
```bash
ping -c 3 192.168.1.10
python3 test_kinova_camera.py --ip 192.168.1.10 --stream depth          # q para cerrar
C="python3 embodied_sin_ros.py capturar"
$C --escena regla       --nota "hoja A4 horizontal, centrada, Z=___ m"
$C --escena semantica1  --nota "D: dos cajas, termo sobre una"
$C --escena semantica1p --nota "P: dos cajas, bandeja como distractor"
$C --escena semantica2  --nota "D: dos celulares, llaves junto a uno"
$C --escena semantica2p --nota "P: pertenencia con otros objetos"
$C --escena semantica3  --nota "D: cuaderno abierto y cuaderno cerrado"
$C --escena semantica3p --nota "P: estado, otra disposición"
$C --escena semantica4  --nota "D: esfero dentro del estuche y dos sueltos"
$C --escena semantica4p --nota "P: contención con distractor"
$C --escena burger      --nota "D: cajas y bandeja del carrito"
$C --escena burgerp     --nota "P: relacional, otra disposición"
for i in 1 2 3 4 5; do $C --escena dist$i --nota "config $i (4 y 5 cerca del borde)"; done
for i in 1 2 3; do $C --escena agarre_s$i --nota "agarre seguro $i"; done
$C --escena agarre_i1 --nota "inseguro: objeto encima"
$C --escena agarre_i2 --nota "inseguro: mano cerca (solo la mano)"
$C --escena agarre_i3 --nota "inseguro: caja volcada"
$C --escena exito_antes1; $C --escena exito_bien1      # la tarea se hace bien a mano
$C --escena exito_antes2; $C --escena exito_mal1       # la tarea se hace mal a propósito
$C --escena exito_antes3; $C --escena exito_bien2
$C --escena exito_antes4; $C --escena exito_mal2
grep -h pixeles_validos_pct capturas/*_meta.json        # 📸 E2: repitan la escena si da < 60 %
```
Después llenen `verdad_terreno.csv` con GIMP (cajas en px), la cinta (`d_real_m`) y `segura`, **antes de consultar**.

## Fase 3: calibración (Tabla 3/4)
```bash
python3 embodied_sin_ros.py calibrar --escena regla --u1 <px> --u2 <px> --ancho-real-m 0.297 --distancia-m <Z>   # 📸 E3
python3 embodied_sin_ros.py consultar --escena regla --tarea puntos --grupo $G \
   --objeto "la esquina superior izquierda y la esquina superior derecha de la hoja blanca"                   # 📸 E3
# error % = |d − 0.297| / 0.297 × 100. Si pasa del 5 %, repitan la calibración.
```

## Fase 5: Exp. 1 (semántica, D/P)
```bash
# Desarrollo: SOLO escenas D, en un CSV aparte. Anoten cada cambio de PROMPTS["propio"] en la Tabla 5
python3 embodied_sin_ros.py consultar --escena semantica1 --tarea propio --grupo $G --csv resultados/desarrollo.csv \
   --objeto "la caja de hamburguesa libre y segura para tomar desde arriba"
git commit -am "prompt congelado" && git log --oneline -1                     # SHA del prompt congelado

declare -A OBJ=( [semantica1]="la caja de hamburguesa libre y segura para tomar desde arriba"
  [semantica2]="el celular que pertenece a la persona que dejó sus llaves al lado"
  [semantica3]="el cuaderno que está abierto"  [semantica4]="el esfero que está dentro del estuche"
  [burger]="la caja de hamburguesa libre del carrito que se puede llevar a la bandeja" )
for e in semantica1 semantica2 semantica3 semantica4 burger; do for s in "" p; do for i in 1 2 3; do
  python3 embodied_sin_ros.py consultar --escena $e$s --tarea propio --thinking low --grupo $G --objeto "${OBJ[$e]}"
done; done; done
for s in "" p; do for i in 1 2 3; do       # versión ingenua
  python3 embodied_sin_ros.py consultar --escena burger$s --tarea puntos --thinking low --grupo $G --objeto "la caja"
done; done                                                     # 📸 E4: un acierto y un fallo (capturas/*_resultado.png)
```

## Fase 6: Exp. 2 (cajas)
```bash
for e in semantica1 burger; do for i in 1 2 3 4 5; do
  python3 embodied_sin_ros.py consultar --escena $e --tarea cajas --objeto "" --grupo $G
done; done
```

## Fase 7: Exp. 3 (3D y ablación del registro)
```bash
O="el centro de la tapa del termo y el centro de la tapa de la caja"
for i in 1 2 3 4 5; do for r in 1 2; do
  python3 embodied_sin_ros.py consultar --escena dist$i --tarea puntos --grupo $G --objeto "$O"
  R=$(tail -1 resultados/resultados.csv | python3 -c "import csv,sys; print(list(csv.reader(sys.stdin))[0][-1])")
  python3 embodied_sin_ros.py consultar --escena dist$i --tarea puntos --grupo $G --objeto "$O" --sin-registro --respuesta "$R"
done; done                       # 📸 E6: capturas/distN_puntos_resultado.png y distN_puntos_sinreg_resultado.png
python3 embodied_sin_ros.py consultar --escena dist1 --tarea puntos --grupo $G \
   --objeto "el centro de la tapa del termo y la mesa justo al lado del termo"        # altura (el primer punto es el objeto)
```

## Fase 8: Exp. 4 (thinking_level, intercalado)
```bash
for i in 1 2 3 4 5; do for nivel in low high; do
  python3 embodied_sin_ros.py consultar --escena semantica2p --tarea propio --thinking $nivel --grupo $G \
     --objeto "el celular que pertenece a la persona que dejó sus llaves al lado"
done; done                                                     # 📸 E7 (filas del CSV)
```

## Fase 9: Exp. 5 (espacio de trabajo, agarre, plan y éxito)
```bash
python3 embodied_sin_ros.py consultar --escena regla --tarea puntos --grupo $G \
   --objeto "las cuatro esquinas de la zona útil de la mesa"
python3 espacio_trabajo.py volumen --escena regla --h-max 0.25 --d-a 0.10           # h_max = altura del objeto más alto
for e in agarre_s1 agarre_s2 agarre_s3 agarre_i1 agarre_i2 agarre_i3; do
  python3 embodied_sin_ros.py consultar --escena $e --tarea agarre --grupo $G --objeto "la caja de hamburguesa"
  python3 espacio_trabajo.py agarre --escena $e
done
python3 embodied_sin_ros.py consultar --escena burger --tarea plan --grupo $G --objeto "llevar la caja libre a la bandeja"
python3 espacio_trabajo.py plan --escena burger                                       # 📸 E8
for par in "exito_antes1 exito_bien1" "exito_antes2 exito_mal1" "exito_antes3 exito_bien2" "exito_antes4 exito_mal2"; do
  set -- $par; python3 embodied_sin_ros.py exito --antes $1 --despues $2 --grupo $G --objeto "la caja libre quedó dentro de la bandeja"
done                                                           # 📸 E8
```

## Fase 10: métricas
```bash
python3 analisis_lab_ia_01b.py          # escribe resultados/tablas.md con las Tablas 6 a 11
```
