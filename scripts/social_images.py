"""Genera le immagini statiche del sito con Chrome headless (non fa parte della build).

- static/img/og-image.png        anteprima per LinkedIn e social, 1200x630 (italiano, lingua del sito)
- static/img/og-image-en.png     la stessa in inglese (per le pagine /en/)
- static/img/apple-touch-icon.png icona per la schermata home di iPhone/Android, 180x180

Usa gli stessi font self-hosted e gli stessi colori del sito. Da rilanciare a mano solo se
cambiano nome, ruolo o colori:

    python scripts/social_images.py

Serve Google Chrome o Chromium installato (variabile CHROME per indicare il binario).
"""

import os
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sitegen.content import LANGUAGES, SITE_LANGUAGE, load_all  # noqa: E402

STATIC = ROOT / "static"
FONTS = (STATIC / "fonts").as_uri()

# Stessi valori dei token in static/css/tokens.css (tema scuro, quello di default)
PAPER, INK, MUTED, RULE, ACCENT = "#17171a", "#e9e6df", "#a39f96", "#34333a", "#86c5a1"

FONT_FACES = f"""
@font-face {{ font-family: "Source Serif 4"; font-weight: 600; src: url("{FONTS}/source-serif-4-latin-600-normal.woff2"); }}
@font-face {{ font-family: "IBM Plex Sans"; font-weight: 400; src: url("{FONTS}/ibm-plex-sans-latin-400-normal.woff2"); }}
@font-face {{ font-family: "IBM Plex Mono"; font-weight: 500; src: url("{FONTS}/ibm-plex-mono-latin-500-normal.woff2"); }}
* {{ margin: 0; box-sizing: border-box; }}
"""


def og_image_html(name: str, headline: str, location: str, site: str) -> str:
    return f"""<!doctype html><meta charset="utf-8"><style>{FONT_FACES}
body {{ width: 1200px; height: 630px; background: {PAPER}; color: {INK}; font-family: "IBM Plex Sans";
       padding: 88px 96px; display: flex; flex-direction: column; }}
.label {{ font-family: "IBM Plex Mono"; font-weight: 500; font-size: 24px; letter-spacing: 0.08em;
         text-transform: uppercase; color: {ACCENT}; }}
h1 {{ font-family: "Source Serif 4"; font-weight: 600; font-size: 96px; line-height: 1.05; margin-top: 28px; }}
.rule {{ width: 120px; height: 4px; background: {ACCENT}; margin-top: 44px; }}
.topics {{ font-size: 32px; color: {MUTED}; margin-top: 36px; }}
.site {{ margin-top: auto; padding-top: 24px; border-top: 1px solid {RULE};
        font-family: "IBM Plex Mono"; font-size: 24px; color: {MUTED}; }}
</style>
<p class="label">{escape(headline)} · {escape(location)}</p>
<h1>{escape(name)}</h1>
<div class="rule"></div>
<p class="topics">Forecasting · Machine learning · Data pipeline · Cloud</p>
<p class="site">{escape(site)}</p>"""


def touch_icon_html(initials: str) -> str:
    # Quadrato pieno: iOS e Android arrotondano gli angoli da soli
    return f"""<!doctype html><meta charset="utf-8"><style>{FONT_FACES}
body {{ width: 180px; height: 180px; background: {ACCENT}; color: {PAPER}; display: grid; place-items: center;
       font-family: "Source Serif 4"; font-weight: 600; font-size: 80px; letter-spacing: 0.02em; }}
</style>{escape(initials)}"""


def screenshot(chrome: str, html: str, size: tuple[int, int], target: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
             f"--window-size={size[0]},{size[1]}", f"--screenshot={target}", page.as_uri()],
            check=True, capture_output=True,
        )
    print(f"Scritto {target.relative_to(ROOT)}")


def main() -> None:
    chrome = os.environ.get("CHROME") or next(
        (c for c in ("google-chrome", "chromium", "chromium-browser") if shutil.which(c)), None
    )
    if chrome is None:
        sys.exit("Chrome o Chromium non trovato: imposta la variabile CHROME")
    # Un'anteprima per lingua, con qualifica e sede tradotte (profile.<lang>.yaml);
    # il campo `image` di ciascun profilo punta al file della sua lingua
    for lang in LANGUAGES:
        profile = load_all(lang=lang).profile
        name = "og-image.png" if lang == SITE_LANGUAGE else f"og-image-{lang}.png"
        screenshot(chrome, og_image_html(profile.name, profile.headline, profile.location, "lorenzodustycosta.github.io"),
                   (1200, 630), STATIC / "img" / name)
    profile = load_all(lang=SITE_LANGUAGE).profile
    initials = "".join(part[0] for part in (profile.name.split()[0], profile.name.split()[-1]))
    screenshot(chrome, touch_icon_html(initials), (180, 180), STATIC / "img" / "apple-touch-icon.png")


if __name__ == "__main__":
    main()
