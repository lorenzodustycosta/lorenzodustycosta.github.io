"""Genera il CV in PDF dagli stessi contenuti del sito (content/), con i font e i colori del sito.

    python scripts/build_cv.py                          # tutte le lingue, variante public, in build/cv/
    python scripts/build_cv.py --lang it                # solo italiano
    python scripts/build_cv.py --variant full           # con telefono (content/private.yaml): MAI committare
    python scripts/build_cv.py --html-only              # solo l'anteprima HTML (con CSS e font), senza Chromium
    python scripts/build_cv.py --max-pages 3            # limite di pagine diverso da cv.yaml

Per ogni lingua scrive il PDF (cv-<lang>.pdf). L'HTML da cui nasce resta in una cartella temporanea;
con --html-only invece si scrive solo quello (cv-<lang>.html + assets/), da aprire nel browser per
lavorare sullo stile. La variante full aggiunge "-full" al nome dei file.

Fallisce se un PDF supera il limite di pagine (max_pages in cv.yaml) o se i font del sito
non risultano incorporati. Stampa un warning con le voci senza testi CV (highlight senza cv_summary, ...).

Dipendenze (non servono per il sito): pip install -r requirements-cv.txt && playwright install chromium
Schema dei contenuti: docs/cv-schema.md
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sitegen.content import LANGUAGES, ContentError, load_all  # noqa: E402
from sitegen.cv import VARIANTS, load_cv_settings, render_cv_html  # noqa: E402

STATIC = ROOT / "static"
DEFAULT_OUT = ROOT / "build" / "cv"
# Prefissi dei nomi dei font del sito nel PDF (es. "AAAAAA+IBMPlexSans"): servono a verificarne l'incorporazione
SITE_FONTS = ("SourceSerif4", "IBMPlexSans", "IBMPlexMono")


def copy_assets(out_dir: Path, photos: set[str]) -> None:
    """CSS, font e foto accanto all'HTML, così Chromium (o il browser, con --html-only) li trova sul disco."""
    assets = out_dir / "assets"
    (assets / "css").mkdir(parents=True, exist_ok=True)
    for name in ("tokens.css", "cv.css"):
        shutil.copy2(STATIC / "css" / name, assets / "css" / name)
    shutil.copytree(STATIC / "fonts", assets / "fonts", dirs_exist_ok=True)
    for photo in photos:  # profile.photo delle lingue, path dentro static/ (es. img/lorenzo.webp)
        (assets / photo).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(STATIC / photo, assets / photo)


def file_stem(lang: str, variant: str) -> str:
    return f"cv-{lang}" if variant == "public" else f"cv-{lang}-full"


def write_pdfs(html_files: list[Path], out_dir: Path) -> list[Path]:
    """HTML → PDF in out_dir con Chromium headless. Un solo browser per tutti i file."""
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright missing: pip install -r requirements-cv.txt && playwright install chromium") from None

    pdfs = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except PlaywrightError as exc:
            raise SystemExit(f"Chromium won't start ({exc.message.splitlines()[0]}).\nRun: playwright install chromium") from None
        page = browser.new_page()
        for html in html_files:
            page.goto(html.as_uri(), wait_until="load")
            page.evaluate("document.fonts.ready")  # aspetta i woff2, altrimenti il PDF usa i font di fallback
            pdf = out_dir / html.with_suffix(".pdf").name
            # prefer_css_page_size: formato e margini da @page in cv.css; tagged: PDF con struttura (accessibilità, ATS)
            page.pdf(path=pdf, prefer_css_page_size=True, print_background=True, tagged=True)
            pdfs.append(pdf)
        browser.close()
    return pdfs


def check_pdf(pdf: Path, max_pages: int) -> list[str]:
    """Problemi bloccanti del PDF: troppe pagine, font del sito non incorporati, testo non estraibile."""
    from pypdf import PdfReader

    reader = PdfReader(pdf)
    problems = []
    pages = len(reader.pages)
    if pages > max_pages:
        problems.append(f"{pdf.name}: {pages} pages, limit is {max_pages} (shorten the texts or change max_pages in cv.yaml)")
    fonts = set()
    for page in reader.pages:
        for font in (page.get("/Resources") or {}).get("/Font", {}).values():
            fonts.add(str(font.get_object().get("/BaseFont", "")).split("+")[-1])
    missing_fonts = [f for f in SITE_FONTS if not any(name.startswith(f) for name in fonts)]
    if missing_fonts:
        problems.append(f"{pdf.name}: site fonts not embedded: {missing_fonts} (found: {sorted(fonts)})")
    if not reader.pages[0].extract_text().strip():
        problems.append(f"{pdf.name}: no selectable text")
    print(f"Written {pdf.relative_to(ROOT) if pdf.is_relative_to(ROOT) else pdf} ({pages} page{'s' * (pages != 1)})")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the CV PDF from content/.")
    parser.add_argument("--lang", choices=[*LANGUAGES, "all"], default="all")
    parser.add_argument("--variant", choices=VARIANTS, default="public",
                        help="public: email, LinkedIn, GitHub (default). full: also phone numbers, local only")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output folder (default: {DEFAULT_OUT.relative_to(ROOT)})")
    parser.add_argument("--max-pages", type=int, help="page limit (default: max_pages in cv.yaml)")
    parser.add_argument("--html-only", action="store_true", help="only the HTML preview, no PDF")
    args = parser.parse_args()

    langs = LANGUAGES if args.lang == "all" else (args.lang,)
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cv-") as tmp:
        # L'HTML serve solo a Chromium: resta nella cartella temporanea, salvo --html-only
        html_dir = out_dir if args.html_only else Path(tmp)
        try:
            photos = {load_all(lang=lang).profile.photo for lang in langs} - {None}
        except ContentError as exc:
            raise SystemExit(f"Content error: {exc}") from None
        copy_assets(html_dir, photos)
        html_files, limits, missing = [], {}, {}
        try:
            for lang in langs:
                html, missing[lang] = render_cv_html(lang, args.variant, css_href="assets/css/cv.css")
                target = html_dir / f"{file_stem(lang, args.variant)}.html"
                target.write_text(html, encoding="utf-8")
                html_files.append(target)
                limits[out_dir / target.with_suffix(".pdf").name] = args.max_pages or load_cv_settings(lang).max_pages
                if args.html_only:
                    print(f"Written {target} (preview)")
        except ContentError as exc:
            raise SystemExit(f"Content error: {exc}") from None

        problems = []
        if not args.html_only:
            for pdf in write_pdfs(html_files, out_dir):
                problems += check_pdf(pdf, limits[pdf])

    for lang, items in missing.items():
        if items:
            print(f"Warning [{lang}]: {len(items)} CV texts still to write (fallback used):")
            for item in items:
                print(f"  - {item}")
    if args.variant == "full":
        print("Note: 'full' variant contains private contacts. Do not commit or publish it.")
    if problems:
        raise SystemExit("CV check failed:\n" + "\n".join(f"  - {p}" for p in problems))


if __name__ == "__main__":
    main()
