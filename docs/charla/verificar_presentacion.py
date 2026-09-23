"""Verifica presentacion.html: navega las 22 láminas, mide desbordes y errores JS, y captura pantallas."""
from playwright.sync_api import sync_playwright

RUTA = "file:///home/pablo/Escritorio/open-legal-chile/docs/charla/presentacion.html"
errores = []
with sync_playwright() as p:
    nav = p.chromium.launch()
    for ancho, alto in ((1600, 900), (1280, 720)):
        pg = nav.new_page(viewport={"width": ancho, "height": alto})
        pg.on("pageerror", lambda e: errores.append(f"pageerror: {e}"))
        pg.on("console", lambda m: errores.append(f"console: {m.text}") if m.type == "error" else None)
        pg.goto(RUTA)
        pg.wait_for_timeout(1100)
        n = pg.evaluate("document.querySelectorAll('.slide').length")
        problemas = []
        for i in range(n):
            pg.evaluate(f"ir({i})")
            pg.wait_for_timeout(620)
            info = pg.evaluate("""(() => {
                const s = document.querySelector('.slide.activa');
                const oy = s.scrollHeight - s.clientHeight;
                let peor = 0, txt = '';
                for (const el of s.querySelectorAll('.a, .tarjeta, h1, h2, h3, .num, li, p')) {
                    const r = el.getBoundingClientRect();
                    const fuera = Math.max(0, r.bottom - innerHeight, r.right - innerWidth, -r.top);
                    if (fuera > peor) { peor = fuera; txt = (el.textContent || '').trim().slice(0, 52); }
                }
                return {oy, peor: Math.round(peor), txt};
            })()""")
            if info["oy"] > 2 or info["peor"] > 6:
                problemas.append({"slide": i + 1, **info})
        print(f"  {ancho}x{alto}: {n} láminas · con problemas: {len(problemas)}")
        for pr in problemas[:10]:
            print(f"    ⚠ lámina {pr['slide']}: sobra-y={pr['oy']}px · desborde={pr['peor']}px «{pr['txt']}»")
        if ancho == 1600:
            for i, nombre in [(0, "01_portada"), (1, "02_porque"), (3, "03_puente"), (12, "04_grafo"),
                              (14, "05_ahorro"), (15, "06_citas"), (21, "07_fuentes")]:
                pg.evaluate(f"ir({i})")
                pg.wait_for_timeout(2300)
                pg.screenshot(path=f"/tmp/pres_{nombre}.png")
        pg.close()
    nav.close()
print("  errores JS:", errores[:6] if errores else "ninguno")
