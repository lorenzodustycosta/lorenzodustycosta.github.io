"""Entry point del generatore del sito.

    python build.py            # build in dist/
    python build.py --serve    # build + server locale + rebuild al salvataggio

Variabili d'ambiente:
    BASE_URL   prefisso dei link generati (default "": sito servito dalla root,
               come su https://lorenzodustycosta.github.io e in locale).
"""

import argparse
import functools
import os
import shutil
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).parent
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
DIST_DIR = ROOT / "dist"
WATCHED_DIRS = [ROOT / "content", TEMPLATES_DIR, STATIC_DIR, ROOT / "sitegen"]


def make_url(base_url: str, path: str) -> str:
    """Costruisce un link assoluto a partire da BASE_URL: url("css/main.css") -> "/css/main.css"."""
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def build(base_url: str = "", dist_dir: Path = DIST_DIR) -> None:
    """Rigenera da zero dist_dir: copia static/ e renderizza le pagine."""
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    shutil.copytree(STATIC_DIR, dist_dir, ignore=shutil.ignore_patterns(".gitkeep"))

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=True,
        undefined=StrictUndefined,  # una variabile mancante nel template fa fallire la build
    )
    env.globals["url"] = functools.partial(make_url, base_url)

    html = env.get_template("pages/index.html").render()
    (dist_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"Build completata in {dist_dir}")


def serve(base_url: str, port: int) -> None:
    """Serve dist/ su localhost e ricostruisce il sito a ogni modifica dei sorgenti."""
    from watchfiles import watch  # importato qui: serve solo in sviluppo

    build(base_url)
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(DIST_DIR))
    server = ThreadingHTTPServer(("localhost", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"Server su http://localhost:{port} (Ctrl+C per uscire)")

    try:
        for changes in watch(*WATCHED_DIRS):
            print(f"Modificati {len(changes)} file, rebuild...")
            try:
                build(base_url)
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
    args = parser.parse_args()

    base_url = os.environ.get("BASE_URL", "")
    if args.serve:
        serve(base_url, args.port)
    else:
        build(base_url)


if __name__ == "__main__":
    main()
