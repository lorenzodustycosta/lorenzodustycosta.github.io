"""Genera il banner del profilo LinkedIn (1584x396) con i font e i colori del sito. Non fa parte della build.

    python scripts/linkedin_banner.py                  # inglese, grafico a tutta larghezza
    python scripts/linkedin_banner.py --lang it        # italiano
    python scripts/linkedin_banner.py --chart left     # grafico solo a sinistra e al centro
    python scripts/linkedin_banner.py --chart both     # entrambe le varianti, per confrontarle

Scrive in branding/:
- linkedin-banner.png          il banner, esattamente 1584x396 (renderizzato a 2x e ridimensionato)
- linkedin-banner-preview.png  lo stesso con le zone sicure sovrapposte: foto profilo su desktop
                               e zona del testo che resta visibile su mobile
Con --lang it i nomi diventano linkedin-banner-it*.png; con --chart both prendono il suffisso
-full / -left.

Come scripts/social_images.py: una pagina HTML resa da Chromium headless con i font self-hosted del
sito. Colori e font non sono copiati qui: la pagina collega static/css/tokens.css con il tema chiaro
(fondo crema), e il controllo del contrasto legge i valori dallo stesso file.

Il grafico è decorativo e ridisegna la previsione eolica day-ahead del sito (banda P10–P90, P50,
produzione effettiva) con la serie sintetica di sitegen/wind_chart.py, la stessa dello sfondo
dell'hero. Nessun dato di clienti.

Fallisce se un testo esce dalla zona sicura mobile, tocca l'area della foto su desktop, o se il suo
contrasto con lo sfondo reale (pixel per pixel, grafico compreso) è sotto WCAG AA (4.5:1).

Dipendenze (non servono per il sito): pip install -r requirements-cv.txt && playwright install chromium
"""

import argparse
import io
import re
import sys
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import DEFAULT_SITE_URL  # noqa: E402
from sitegen.content import ContentError, load_all  # noqa: E402
from sitegen.wind_chart import chart_svg, wind_series  # noqa: E402

TOKENS = ROOT / "static" / "css" / "tokens.css"
OUT_DIR = ROOT / "branding"

WIDTH, HEIGHT, SCALE = 1584, 396, 2
MAX_BYTES = 8 * 1024 * 1024
# Zone sicure (x0, y0, x1, y1) in px del banner, dalle indicazioni di LinkedIn
PHOTO_ZONE = (0, HEIGHT // 2, 400, HEIGHT)  # foto profilo su desktop: in basso a sinistra
MOBILE_TEXT_ZONE = (750, 60, 1500, 330)  # dove il testo resta visibile anche su mobile
WCAG_AA = 4.5

# Seconda riga: specifica del banner, non è un contenuto del sito
TAGLINES = {
    "en": "Forecasting · Machine learning · KPIs & data pipelines",
    "it": "Forecasting · Machine learning · KPI e data pipeline",
}


# Maschere del grafico (più livelli, intersecati): sfuma ai bordi e lascia vuota l'area della foto
# profilo in basso a sinistra. "full" attraversa tutto il banner ma si spegne dietro il testo, così
# linee e banda non abbassano il contrasto; "left" si ferma prima del testo.
PHOTO_FADE = "radial-gradient(ellipse 470px 250px at 150px 100%, transparent 60%, #000 100%)"
TEXT_FADE = "radial-gradient(ellipse 520px 150px at 1150px 205px, transparent 62%, #000 100%)"
MASKS = {
    "full": ["linear-gradient(to right, transparent, #000 12%, #000 88%, transparent)", PHOTO_FADE, TEXT_FADE],
    "left": ["linear-gradient(to right, transparent, #000 10%, #000 34%, transparent 54%)", PHOTO_FADE],
}


def banner_html(headline: str, tagline: str, site: str, chart: str, variant: str) -> str:
    # Colori e font solo dai token del sito (tema chiaro = fondo crema); le tinte del grafico
    # sono mescolate dall'accento con color-mix, senza valori nuovi
    return f"""<!doctype html>
<html lang="en" data-theme="light"><meta charset="utf-8">
<link rel="stylesheet" href="{TOKENS.as_uri()}">
<style>
* {{ margin: 0; box-sizing: border-box; }}
body {{ width: {WIDTH}px; height: {HEIGHT}px; overflow: hidden; position: relative; background: var(--paper); }}
.chart {{
  position: absolute; inset: 0; width: 100%; height: 100%;
  mask-image: {', '.join(MASKS[variant])};
  mask-composite: intersect;
}}
.band {{ fill: color-mix(in srgb, var(--link) 45%, var(--paper)); opacity: 0.35; }}
.p50 {{ fill: none; stroke: var(--link); stroke-width: 3; opacity: 0.4; }}
.actual {{ fill: none; stroke: color-mix(in srgb, var(--link) 55%, var(--ink)); stroke-width: 2.5;
          stroke-dasharray: 9 7; opacity: 0.32; }}
.text {{
  position: absolute; right: {WIDTH - MOBILE_TEXT_ZONE[2]}px; top: 50%; transform: translateY(-50%);
  text-align: right;
}}
h1 {{ font-family: var(--font-heading); font-weight: var(--heading-weight); font-size: 60px; line-height: 1.1;
     color: var(--ink); }}
.tagline {{ font-family: var(--font-body); font-size: 25px; margin-top: 16px; color: var(--ink-muted); }}
.site {{ font-family: var(--font-mono); font-weight: 500; font-size: 20px; margin-top: 22px; color: var(--link);
        letter-spacing: 0.02em; }}
</style>
<body>
{chart}
<div class="text">
  <h1 data-check>{escape(headline)}</h1>
  <p class="tagline" data-check>{escape(tagline)}</p>
  <p class="site" data-check>{escape(site)}</p>
</div>
</body></html>"""


# ---- Rendering e controlli ----------------------------------------------

def render(html: str):
    """HTML → (immagine 2x, sfondo 2x senza testo, riquadri e colori dei testi in px del banner)."""
    from PIL import Image
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright missing: pip install -r requirements-cv.txt && playwright install chromium") from None

    with tempfile.TemporaryDirectory(prefix="banner-") as tmp, sync_playwright() as p:
        page_file = Path(tmp) / "banner.html"
        page_file.write_text(html, encoding="utf-8")
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=SCALE)
        page.goto(page_file.as_uri())
        page.evaluate("document.fonts.ready")
        loaded = page.evaluate("[...document.fonts].filter(f => f.status === 'loaded').map(f => f.family)")
        for family in ("Source Serif 4", "IBM Plex Sans", "IBM Plex Mono"):
            if family not in loaded:
                raise SystemExit(f"Font not loaded: {family}")
        texts = page.evaluate("""[...document.querySelectorAll('[data-check]')].map(el => {
            // riquadro dell'inchiostro effettivo: un Range sul testo, non il blocco a tutta larghezza
            const range = document.createRange(); range.selectNodeContents(el);
            const r = range.getBoundingClientRect();
            return {text: el.textContent, color: getComputedStyle(el).color,
                    box: [r.left, r.top, r.right, r.bottom]};
        })""")
        full = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
        page.add_style_tag(content="[data-check] { visibility: hidden; }")
        background = Image.open(io.BytesIO(page.screenshot())).convert("RGB")
        browser.close()
    return full, background, texts


def luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def light_tokens() -> dict[str, tuple[int, int, int]]:
    """Colori del tema chiaro letti da tokens.css (i valori di :root, sovrascritti da [data-theme=light])."""
    css = TOKENS.read_text(encoding="utf-8")
    blocks = re.findall(r":root\s*\{(.*?)\}", css, re.S) + re.findall(r':root\[data-theme="light"\]\s*\{(.*?)\}', css, re.S)
    colors = {}
    for block in blocks:
        for name, value in re.findall(r"--([\w-]+):\s*#([0-9a-fA-F]{6})", block):
            colors[name] = tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    return colors


def check(background, texts) -> list[str]:
    """Zone sicure e contrasto peggiore di ogni testo sui pixel di sfondo reali sotto di esso."""
    problems, paper = [], light_tokens()["paper"]
    for item in texts:
        x0, y0, x1, y1 = item["box"]
        label = item["text"]
        mx0, my0, mx1, my1 = MOBILE_TEXT_ZONE
        if x0 < mx0 or y0 < my0 or x1 > mx1 or y1 > my1:
            problems.append(f"'{label}' outside the mobile safe zone: box {[round(v) for v in item['box']]}")
        px0, py0, px1, py1 = PHOTO_ZONE
        if x0 < px1 and x1 > px0 and y0 < py1 and y1 > py0:
            problems.append(f"'{label}' overlaps the profile photo area")
        color = tuple(int(c) for c in re.findall(r"\d+", item["color"])[:3])
        crop = background.crop(tuple(round(v * SCALE) for v in item["box"]))
        worst = min(contrast(color, rgb) for _, rgb in crop.getcolors(crop.width * crop.height))
        status = "ok" if worst >= WCAG_AA else "FAIL"
        print(f"  contrast {worst:5.2f}:1 worst pixel ({contrast(color, paper):.2f}:1 on plain paper) "
              f"{status}  {label}")
        if worst < WCAG_AA:
            problems.append(f"'{label}' contrast {worst:.2f}:1 < {WCAG_AA}:1")
    return problems


def preview(banner):
    """Il banner con le zone sicure in semitrasparenza, per controllarlo a occhio.
    Due livelli separati (ImageDraw sovrascrive i pixel invece di mescolarli): prima il mobile, poi la foto."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.load_default(size=16)
    image = banner.convert("RGBA")

    # Mobile: fuori dalla zona del testo il banner può essere tagliato o coperto dalla foto
    mobile = Image.new("RGBA", image.size, (30, 60, 160, 55))
    draw = ImageDraw.Draw(mobile)
    draw.rectangle(MOBILE_TEXT_ZONE, fill=(0, 0, 0, 0), outline=(30, 60, 160, 230), width=3)
    mx0, my0, mx1, my1 = MOBILE_TEXT_ZONE
    draw.text((mx0 + 8, my0 - 22), "mobile: zona sicura del testo", fill=(20, 40, 130, 255), font=font)
    image = Image.alpha_composite(image, mobile)

    # Desktop: area coperta dalla foto profilo, con il cerchio della foto
    photo = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(photo)
    x0, y0, x1, y1 = PHOTO_ZONE
    draw.rectangle(PHOTO_ZONE, fill=(200, 40, 40, 50), outline=(200, 40, 40, 220), width=3)
    diameter = (y1 - y0) * 1.4
    draw.ellipse((48, y1 - diameter * 0.62, 48 + diameter, y1 + diameter * 0.38), fill=(200, 40, 40, 90))
    draw.text((x0 + 10, y0 + 8), "desktop: foto profilo", fill=(140, 20, 20, 255), font=font)
    return Image.alpha_composite(image, photo).convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the LinkedIn banner (1584x396).")
    parser.add_argument("--lang", choices=sorted(TAGLINES), default="en")
    parser.add_argument("--chart", choices=[*MASKS, "both"], default="full",
                        help="full: chart across the whole width; left: left and centre only; both: one file each")
    args = parser.parse_args()
    from PIL import Image

    try:
        profile = load_all(lang=args.lang).profile
    except ContentError as exc:
        raise SystemExit(f"Content error: {exc}") from None
    site = re.sub(r"^https?://|/$", "", DEFAULT_SITE_URL)  # lo stesso URL della build del sito

    chart = chart_svg(wind_series(), WIDTH, HEIGHT, top=34, bottom=HEIGHT - 26)
    variants = list(MASKS) if args.chart == "both" else [args.chart]
    OUT_DIR.mkdir(exist_ok=True)
    problems = []
    for variant in variants:
        stem = "linkedin-banner" + ("" if args.lang == "en" else f"-{args.lang}")
        stem += f"-{variant}" if args.chart == "both" else ""
        print(f"{stem} ({variant}):")
        full, background, texts = render(banner_html(profile.headline, TAGLINES[args.lang], site, chart, variant))
        problems += check(background, texts)
        banner = full.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        target = OUT_DIR / f"{stem}.png"
        banner.save(target, optimize=True)
        size = target.stat().st_size
        if banner.size != (WIDTH, HEIGHT) or size > MAX_BYTES:
            problems.append(f"{target.name}: {banner.size}, {size} bytes")
        preview(banner).save(OUT_DIR / f"{stem}-preview.png", optimize=True)
        print(f"  written branding/{stem}.png ({banner.size[0]}x{banner.size[1]}, {size // 1024} KB) and -preview.png")
    if problems:
        raise SystemExit("Banner check failed:\n" + "\n".join(f"  - {p}" for p in problems))


if __name__ == "__main__":
    main()
