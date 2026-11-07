"""Rendering HTML: ambiente Jinja2, filtri e scrittura delle pagine."""

import functools
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, pass_context
from markdown_it import MarkdownIt
from markupsafe import Markup, escape

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

_markdown = MarkdownIt("commonmark")


def make_url(base_url: str, path: str) -> str:
    """Costruisce un link assoluto a partire da BASE_URL: url("css/main.css") -> "/css/main.css"."""
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def month_year(value: str | None, months: list[str] = MONTHS, present: str = "Present") -> str:
    """"2020-01" -> "Jan 2020", "2011" -> "2011", "present" -> "Present"."""
    if not value:
        return ""
    if value == "present":
        return present
    year, _, month = value.partition("-")
    return f"{months[int(month) - 1]} {year}" if month else year


@pass_context
def _month_year_filter(context, value: str | None) -> str:
    """Filtro Jinja: come month_year(), con i nomi dei mesi della lingua della pagina (`t`)."""
    t = context["t"]
    return month_year(value, t.months, t.present)


def markdown(text: str) -> Markup:
    # Markup: l'HTML generato non va ri-escapato da Jinja
    return Markup(_markdown.render(text))


def markdown_inline(text: str) -> Markup:
    """Come markdown(), ma senza il <p> esterno: per testi dentro un elemento esistente."""
    return Markup(_markdown.renderInline(text))


def keep_hyphenated(text: str) -> Markup:
    """Impedisce di andare a capo dentro le parole col trattino: "day-ahead" resta intero."""
    return Markup(re.sub(r"\w+(?:-\w+)+", lambda m: f'<span class="nowrap">{m.group(0)}</span>', str(escape(text))))


def make_env(templates_dir: Path, base_url: str, site_url: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=True,
        undefined=StrictUndefined,  # una variabile mancante nel template fa fallire la build
        trim_blocks=True,
        lstrip_blocks=True,
    )
    url = functools.partial(make_url, base_url)
    env.globals["url"] = url
    env.globals["absolute_url"] = lambda path: site_url.rstrip("/") + url(path)
    env.filters["month_year"] = _month_year_filter
    env.filters["markdown"] = markdown
    env.filters["keep_hyphenated"] = keep_hyphenated
    env.filters["markdown_inline"] = markdown_inline
    return env


def output_file(dist_dir: Path, path: str) -> Path:
    """Path del sito -> file in dist/: "" -> index.html, "experience/" -> experience/index.html."""
    target = dist_dir / path
    return target / "index.html" if path == "" or path.endswith("/") else target


def write_page(env: Environment, template: str, dist_dir: Path, path: str, **context) -> None:
    target = output_file(dist_dir, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(env.get_template(template).render(path=path, **context), encoding="utf-8")
