"""Entry point del generatore del sito.

    python build.py            # build in dist/
    python build.py --serve    # build + server locale + rebuild al salvataggio
                               # (aggiunge anche le pagine di sviluppo in dist/_dev/)
    python build.py --serve --lan  # come sopra, raggiungibile dal telefono sulla stessa rete Wi-Fi

Lingue: italiano su /, inglese su /en/. I contenuti base sono in inglese; dove manca
un file italiano si usa quello inglese e la build stampa un warning (non fallisce).

Variabili d'ambiente:
    BASE_URL   prefisso dei link generati (default "": sito servito dalla root,
               come su https://lorenzodustycosta.github.io e in locale).
    SITE_URL   dominio pubblico, usato per gli URL assoluti (sitemap, Open Graph).
"""

import argparse
import datetime
import functools
import os
import shutil
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from sitegen import seo
from sitegen.content import (
    CONTENT_DIR,
    LANGUAGES,
    SITE_LANGUAGE,
    ContentError,
    load_all,
    load_ui_strings,
    missing_translations,
)
from sitegen.images import ImageError, image_size
from sitegen.render import make_env, make_url, write_page

ROOT = Path(__file__).parent
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
DIST_DIR = ROOT / "dist"
DEV_DIR = ROOT / "dev"  # CSS e JS usati solo dalle pagine di sviluppo
WATCHED_DIRS = [CONTENT_DIR, TEMPLATES_DIR, STATIC_DIR, DEV_DIR, ROOT / "sitegen"]
DEFAULT_SITE_URL = "https://lorenzodustycosta.github.io"

# Prefisso dei path per lingua: "" per la lingua del sito (italiano), "en/" per l'inglese
LANG_PREFIX = {lang: "" if lang == SITE_LANGUAGE else f"{lang}/" for lang in LANGUAGES}

# (chiave in pages.yaml, template, path sul sito). L'ordine è quello del menu.
PAGES = [
    ("home", "pages/index.html", ""),
    ("experience", "pages/experience.html", "experience/"),
    ("education", "pages/education.html", "education/"),
    ("projects", "pages/projects.html", "projects/"),
    ("contact", "pages/contact.html", "contact/"),
]


def check_static_files(site) -> None:
    """I file indicati nei contenuti (CV, immagini, foto) devono esistere in static/.

    Le immagini di esperienze, highlight e progetti devono anche essere WebP, PNG
    o SVG leggibili, perché la build ne legge le dimensioni.
    """
    profile = site.profile
    for path in (profile.cv, profile.image, profile.photo):
        if path and not (STATIC_DIR / path).is_file():
            raise ContentError(f"profile.yaml: static/{path} not found")
    items = [(e.id, e) for e in site.experiences] + [(p.id, p) for p in site.projects]
    items += [(e.id, h) for e in site.experiences for h in e.highlights]
    for item_id, item in items:
        if not item.image:
            continue
        if not (STATIC_DIR / item.image).is_file():
            raise ContentError(f"{item_id}: static/{item.image} not found")
        try:
            image_size(STATIC_DIR / item.image)
        except ImageError as exc:
            raise ContentError(f"{item_id}: {exc}") from exc


def report_missing_translations() -> None:
    """Stampa un warning con i file e le stringhe di interfaccia non ancora tradotti."""
    for lang in LANGUAGES:
        files = missing_translations(lang)
        _, keys = load_ui_strings(lang)
        if files:
            print(f"Warning [{lang}]: {len(files)} files without translation, English used: {', '.join(files)}")
        if keys:
            print(f"Warning [{lang}]: {len(keys)} strings missing in i18n.yaml, English used: {', '.join(keys)}")


# Pagine di sviluppo: (template, path sul sito, titolo). Mai nella build di produzione.
DEV_PAGES = [
    ("_dev/fonts.html", "_dev/fonts.html", "Font playground"),
]


def build(
    base_url: str = "", site_url: str = DEFAULT_SITE_URL, dist_dir: Path = DIST_DIR, dev: bool = False
) -> None:
    """Rigenera da zero dist_dir: copia static/ e renderizza le pagine.

    Con dev=True aggiunge le pagine di DEV_PAGES in dist/_dev/ (fuori da sitemap e deploy)
    e non include lo script di analytics.
    """
    # Tutte le lingue, e tutti gli errori insieme: un file rotto non nasconde gli altri
    sites, errors = {}, []
    for lang in LANGUAGES:
        try:
            sites[lang] = load_all(lang=lang)
        except ContentError as exc:
            errors.append(f"[{lang}] {exc}")
    if errors:
        raise ContentError("\n\n".join(errors))
    for site in sites.values():
        check_static_files(site)
    report_missing_translations()

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    shutil.copytree(STATIC_DIR, dist_dir, ignore=shutil.ignore_patterns(".gitkeep"))

    env = make_env(TEMPLATES_DIR, base_url, site_url)
    url = env.globals["url"]
    absolute = env.globals["absolute_url"]
    env.globals["site_language"] = SITE_LANGUAGE  # per hreflang x-default
    # (larghezza, altezza) delle immagini, per width/height degli <img>; letto una volta per file
    env.globals["image_size"] = functools.cache(lambda path: image_size(STATIC_DIR / path))

    for lang, site in sites.items():
        prefix = LANG_PREFIX[lang]
        t, _ = load_ui_strings(lang)
        nav = [(key, getattr(site.pages, key), path) for key, _, path in PAGES if key != "home"]
        common = {
            "site": site,
            "t": t,
            "lang": lang,
            # link(path): link a una pagina nella lingua corrente; url(path) resta per i file statici
            "link": lambda path, prefix=prefix: url(prefix + path.lstrip("/")),
            "nav": nav,
            "build_year": datetime.date.today().year,
            # analytics: lo script di Cloudflare va solo in produzione, per non contare le visite locali
            "analytics": not dev,
            # dev: mostra le cornici "image missing" dove manca l'immagine di un progetto in evidenza
            "dev": dev,
        }
        for key, template, path in PAGES:
            # la stessa pagina in tutte le lingue, per hreflang e il selettore di lingua
            translations = {other: LANG_PREFIX[other] + path for other in LANGUAGES}
            write_page(
                env, template, dist_dir, prefix + path,
                page=getattr(site.pages, key), current=key, translations=translations, **common,
            )
        if lang == SITE_LANGUAGE:
            # GitHub Pages serve /404.html per ogni pagina inesistente: ne basta uno, nella lingua del sito
            write_page(
                env, "pages/404.html", dist_dir, "404.html",
                page=site.pages.not_found, current="404", translations={}, **common,
            )
            if dev:
                shutil.copytree(DEV_DIR, dist_dir / "_dev")
                for template, path, title in DEV_PAGES:
                    page = {"title": title, "description": "Development page, not published."}
                    write_page(
                        env, template, dist_dir, path,
                        page=page, current="dev", translations={}, today=datetime.date.today(),
                        **common,
                    )

    sitemap = [{lang: absolute(LANG_PREFIX[lang] + path) for lang in LANGUAGES} for _, _, path in PAGES]
    (dist_dir / "sitemap.xml").write_text(seo.sitemap_xml(sitemap))
    (dist_dir / "robots.txt").write_text(seo.robots_txt(absolute("sitemap.xml")))
    print(f"Build completata in {dist_dir}")


def lan_ip() -> str:
    """IP del PC sulla rete locale (nessun pacchetto inviato: connect su UDP sceglie solo l'interfaccia)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("192.0.2.1", 80))
        return s.getsockname()[0]


def serve(base_url: str, site_url: str, port: int, lan: bool = False) -> None:
    """Serve dist/ e ricostruisce il sito a ogni modifica dei sorgenti.

    Con lan=True il server è raggiungibile dagli altri dispositivi della rete di casa
    (es. Safari sul telefono), non solo da questo PC.
    """
    from watchfiles import watch  # importato qui: serve solo in sviluppo

    build(base_url, site_url, dev=True)
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(DIST_DIR))
    server = ThreadingHTTPServer(("0.0.0.0" if lan else "localhost", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Server su http://localhost:{port} (Ctrl+C per uscire)")
    if lan:
        print(f"Dal telefono (stessa rete Wi-Fi): http://{lan_ip()}:{port}")
    print(f"Font playground: http://localhost:{port}/_dev/fonts.html")

    try:
        for changes in watch(*WATCHED_DIRS):
            print(f"Modificati {len(changes)} file, rebuild...")
            try:
                build(base_url, site_url, dev=True)
            except Exception as exc:  # un errore nei sorgenti non deve fermare il server
                print(f"Errore di build: {exc}")
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera il sito statico in dist/.")
    parser.add_argument("--serve", action="store_true", help="server locale con rebuild automatico")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--lan", action="store_true", help="con --serve: raggiungibile anche dal telefono sulla stessa rete")
    args = parser.parse_args()

    base_url = os.environ.get("BASE_URL", "")
    site_url = os.environ.get("SITE_URL", DEFAULT_SITE_URL)
    if args.serve:
        serve(base_url, site_url, args.port, lan=args.lan)
    else:
        try:
            build(base_url, site_url)
        except ContentError as exc:
            raise SystemExit(f"Errore nei contenuti: {exc}") from None


if __name__ == "__main__":
    main()
