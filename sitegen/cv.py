"""CV in PDF: sceglie le voci dai contenuti del sito e renderizza l'HTML del CV.

Lo usa scripts/build_cv.py, che poi trasforma l'HTML in PDF con Playwright.
Qui niente browser: solo dati e Jinja2, così si testa con pytest senza Chromium.

    from sitegen.cv import render_cv_html
    html, missing = render_cv_html("it", variant="public", css_href="assets/css/cv.css")

Campi del CV (tutti opzionali) e fallback: docs/cv-schema.md.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from markupsafe import Markup

from sitegen.content import (
    CONTENT_DIR,
    PRIVATE_FILE,
    ContentError,
    _load_yaml_model,
    _read_yaml,
    _validate,
    load_all,
    load_ui_strings,
)
from sitegen.models import (
    CvSettings,
    Education,
    Experience,
    PrivateContacts,
    SiteContent,
    Skill,
)
from sitegen.render import make_env, markdown_inline

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
CV_FILE = "cv.yaml"
VARIANTS = ("public", "full")
# Highlight tenuti insieme a ruolo, azienda e date nella stessa pagina (cv.html, .cv-keep)
KEEP_WITH_HEADER = 2


@dataclass
class CvBullet:
    """Un highlight nel CV: il suo cv_summary, oppure (fallback) il suo titolo con il settore."""

    text: str
    tag: str | None = None  # solo nel fallback: con cv_summary il settore non si stampa
    fallback: bool = False


@dataclass
class CvExperience:
    experience: Experience
    bullets: list[CvBullet]

    @property
    def head_bullets(self) -> list[CvBullet]:
        """I bullet che stanno nella stessa pagina dell'intestazione del ruolo."""
        return self.bullets[:KEEP_WITH_HEADER]

    @property
    def tail_bullets(self) -> list[CvBullet]:
        return self.bullets[KEEP_WITH_HEADER:]


@dataclass
class CvData:
    """Tutto quello che serve al template, già filtrato e con i fallback applicati."""

    site: SiteContent
    settings: CvSettings
    lang: str
    variant: str
    summary: str
    experiences: list[CvExperience]
    degrees: list[Education]  # lauree e scuole: nella sidebar
    certificates: list[Education]  # nella sidebar, dopo lauree e scuole
    skill_groups: list[tuple[str, list[Skill]]]  # (etichetta categoria, skill)
    languages: list[tuple[str, str | None]]  # (lingua, livello)
    private: PrivateContacts | None = None
    missing: list[str] = field(default_factory=list)  # testi CV ancora da scrivere


_TAG_OR_TEXT = re.compile(r"(<[^>]+>)")
_HYPHENATED = re.compile(r"\w+(?:-\w+)+")


def cv_inline(text: str) -> Markup:
    """markdown_inline, ma senza andare a capo dentro le parole col trattino ("sport-tech", "free-tier").

    Se Chromium va a capo dopo il trattino, pdftotext ricompone la parola togliendolo ("sporttech")
    e un ATS non la riconosce più. Come keep_hyphenated del sito, ma sull'HTML del Markdown:
    tocca solo il testo fra i tag, non gli attributi (gli URL dei link).
    """
    parts = _TAG_OR_TEXT.split(str(markdown_inline(text)))
    for i in range(0, len(parts), 2):  # indici pari: testo; dispari: tag
        parts[i] = _HYPHENATED.sub(lambda m: f'<span class="nowrap">{m.group(0)}</span>', parts[i])
    return Markup("".join(parts))


def load_cv_settings(lang: str, content_dir: Path = CONTENT_DIR) -> CvSettings:
    path = content_dir / CV_FILE
    if not path.is_file():
        raise ContentError(f"{path} not found (see docs/cv-schema.md)")
    return _load_yaml_model(CvSettings, path, lang)


def load_private(content_dir: Path = CONTENT_DIR) -> PrivateContacts:
    """Contatti della variante "full". Il file è in .gitignore: se manca, errore con le istruzioni."""
    path = content_dir / PRIVATE_FILE
    if not path.is_file():
        raise ContentError(
            f"{path} not found: the 'full' variant needs it (format in docs/cv-schema.md). "
            "Never commit this file."
        )
    return _validate(PrivateContacts, _read_yaml(path), path)


def _skill_groups(site: SiteContent, settings: CvSettings) -> list[tuple[str, list[Skill]]]:
    """Skill raggruppate per categoria, nell'ordine di skills.yaml.

    Con `skills` in cv.yaml: solo quelle, nell'ordine scritto dentro ogni categoria.
    Senza: le skill della Toolbox (toolbox: true), come nella home.
    """
    if settings.skills:
        known = site.skills
        unknown = [s for s in settings.skills if s not in known]
        if unknown:
            raise ContentError(f"{CV_FILE}: unknown skills {unknown} (add them to skills.yaml)")
        chosen = [known[s] for s in settings.skills]
        groups = [(c.label, [s for s in chosen if s.category == c.id]) for c in site.skill_categories]
    else:
        groups = [(c.label, [s for s in c.skills if s.toolbox]) for c in site.skill_categories]
    return [(label, skills) for label, skills in groups if skills]


def _experience(e: Experience, missing: list[str]) -> CvExperience:
    """Un bullet per highlight: solo cv_summary (niente titolo, tag, metriche: i numeri sono nel testo).

    Senza cv_summary si usa il titolo dell'highlight con il settore, e lo si segnala nel warning.
    """
    bullets = []
    for number, h in enumerate(e.highlights, start=1):
        if not h.cv:
            continue
        if h.cv_summary is not None:
            bullets.append(CvBullet(h.cv_summary))
            continue
        title = h.cv_title or h.title or h.text
        missing.append(f"experiences/{e.id}: cv_summary of highlight {number} ({title[:40]}...)")
        bullets.append(CvBullet(title, h.tag, fallback=True))
    return CvExperience(e, bullets)


def cv_data(lang: str, variant: str = "public", content_dir: Path = CONTENT_DIR) -> CvData:
    """Legge contenuti e cv.yaml di una lingua e prepara i dati del CV."""
    if variant not in VARIANTS:
        raise ContentError(f"unknown variant {variant!r} (expected one of {VARIANTS})")
    site = load_all(content_dir, lang=lang)
    settings = load_cv_settings(lang, content_dir)
    missing = []

    experiences = [_experience(e, missing) for e in site.experiences if e.cv]

    summary = settings.summary
    if summary is None:
        summary = site.profile.summary
        missing.append(f"{CV_FILE}: summary (profile.summary used)")
    if not settings.skills:
        missing.append(f"{CV_FILE}: skills (Toolbox skills used)")

    education = [e for e in site.education if e.cv]
    if settings.languages:
        languages = [(lang_.name, lang_.level) for lang_ in settings.languages]
    else:
        languages = [(name, None) for name in site.profile.languages]

    return CvData(
        site=site,
        settings=settings,
        lang=lang,
        variant=variant,
        summary=summary,
        experiences=experiences,
        # Prima le lauree, poi le scuole; dentro ogni gruppo l'ordine resta cronologico inverso
        degrees=sorted((e for e in education if e.kind != "certificate"), key=lambda e: e.kind != "degree"),
        certificates=[e for e in education if e.kind == "certificate"],
        skill_groups=_skill_groups(site, settings),
        languages=languages,
        private=load_private(content_dir) if variant == "full" else None,
        missing=missing,
    )


def render_cv_html(
    lang: str, variant: str = "public", css_href: str = "assets/css/cv.css", content_dir: Path = CONTENT_DIR
) -> tuple[str, list[str]]:
    """HTML del CV e l'elenco dei testi CV mancanti (per il warning in console)."""
    data = cv_data(lang, variant, content_dir)
    t, _ = load_ui_strings(lang, content_dir)
    env = make_env(TEMPLATES_DIR, base_url="", site_url="")
    env.filters["cv_inline"] = cv_inline
    html = env.get_template("cv/cv.html").render(cv=data, site=data.site, t=t, lang=lang, css_href=css_href)
    return html, data.missing
