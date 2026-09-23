"""Graba las animaciones HTML a video MP4 (para incrustarlas en el PowerPoint).

Cada animación se abre en Chromium headless, se graba su corrida completa (el propio Playwright
captura el video), se convierte a H.264 con el ffmpeg del sistema y se guarda un cuadro de portada.
El cuadro de portada se verifica con Pillow: si saliera en blanco, se avisa.
"""
from __future__ import annotations

import pathlib
import subprocess

from PIL import Image, ImageStat
from playwright.sync_api import sync_playwright

CHARLA = pathlib.Path("/home/pablo/Escritorio/open-legal-chile/docs/charla")
VIDEO = CHARLA / "video"
VIDEO.mkdir(exist_ok=True)
TEMP = pathlib.Path("/tmp/grabaciones")
TEMP.mkdir(exist_ok=True)

# (archivo, segundos a grabar, segundo del cuadro de portada)
ANIMACIONES = [
    ("animacion_llm", 21.0, 13.0),
    ("animacion_flujo", 8.0, 5.5),
    ("animacion_ahorro", 6.5, 4.5),
    ("animacion_grafo", 15.0, 10.0),
    ("animacion_citas", 13.5, 9.0),
    ("animacion_caso", 14.0, 9.5),
    ("animacion_idea", 16.5, 9.0),
]

# Se puede grabar solo algunas:  python grabar_animaciones.py animacion_idea
import sys as _sys

_pedidas = set(_sys.argv[1:])
if _pedidas:
    ANIMACIONES = [a for a in ANIMACIONES if a[0] in _pedidas]

with sync_playwright() as p:
    navegador = p.chromium.launch()
    for nombre, segundos, segundo_poster in ANIMACIONES:
        contexto = navegador.new_context(
            viewport={"width": 1010, "height": 740},
            record_video_dir=str(TEMP),
            record_video_size={"width": 1010, "height": 740},
        )
        pagina = contexto.new_page()
        pagina.goto((CHARLA / f"{nombre}.html").as_uri())
        pagina.wait_for_timeout(int(segundo_poster * 1000))
        poster = VIDEO / f"{nombre}_poster.png"
        pagina.screenshot(path=str(poster))
        pagina.wait_for_timeout(int(max(0.2, segundos - segundo_poster) * 1000))
        video = pagina.video
        contexto.close()
        if video is None:  # sin grabación no hay video que convertir
            print(f"  ✗ {nombre}: la grabación no produjo video")
            continue
        webm = pathlib.Path(video.path())

        mp4 = VIDEO / f"{nombre}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(webm),
             "-c:v", "libx264", "-preset", "slow", "-crf", "22",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(mp4)],
            check=True,
        )
        # verificación de que el cuadro de portada no esté en blanco
        with Image.open(poster) as im:
            gris = im.convert("L")
            desviacion = ImageStat.Stat(gris).stddev[0]
        duracion = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(mp4)],
            capture_output=True, text=True).stdout.strip()
        estado = "✓" if desviacion > 8 else "⚠ PORTADA CASI EN BLANCO"
        print(f"  {estado} {nombre}: {mp4.stat().st_size/1e6:.2f} MB · {float(duracion):.1f}s · "
              f"portada σ={desviacion:.1f}", flush=True)
        webm.unlink(missing_ok=True)
    navegador.close()

print("  ✓ videos en", VIDEO)
