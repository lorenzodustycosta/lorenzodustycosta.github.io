"""Lettura e validazione dei contenuti in content/.

Unico punto del progetto che legge content/: lo usa build.py e, dalla Fase 4,
anche il backend del chatbot.

    from sitegen.content import load_all
    site = load_all()               # inglese
    site_it = load_all(lang="it")   # italiano, con l'inglese dove manca la traduzione
    site.experiences[0].role

Lingue: l'inglese è nei file "base" (mathsport.md, services.yaml); le altre
lingue in file paralleli con il suffisso (mathsport.it.md, services.it.yaml).
Se un file tradotto manca si usa quello inglese: missing_translations() li elenca.
"""

from pathlib import Path

import frontmatter
import yaml
from pydantic import BaseModel, ValidationError

from sitegen.models import (
    Education,
    Experience,
    Pages,
    Profile,
    Project,
    Publication,
    Services,
    SiteContent,
    SkillCategory,
    UiStrings,
)

CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"

# Lingua in cui sono scritti i file di contenuto base (mathsport.md); le altre hanno il suffisso
DEFAULT_LANGUAGE = "en"
# Lingua servita sulla radice del sito (/); le altre stanno sotto /<lang>/
SITE_LANGUAGE = "it"
# Ordine del selettore di lingua e degli hreflang
LANGUAGES = ("it", "en")

# Stringhe di interfaccia: un file solo, con una sezione per lingua
I18N_FILE = "i18n.yaml"
# Contatti privati per la variante "full" del CV: in .gitignore, mai pubblicati né tradotti
PRIVATE_FILE = "private.yaml"


class ContentError(Exception):
    """Contenuto non valido: il messaggio indica il file e il problema."""


def _validate[M: BaseModel](model: type[M], data: object, source: Path) -> M:
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ContentError(f"{source}:\n{exc}") from exc


def _yaml_error(path: Path, exc: yaml.YAMLError, first_line: int = 1) -> ContentError:
    """Errore di sintassi YAML con file e riga reale, invece del traceback di PyYAML.

    first_line: riga del file da cui parte lo YAML (2 per il frontmatter, dopo il primo "---").
    """
    mark = getattr(exc, "problem_mark", None)
    where = f", line {mark.line + first_line}" if mark else ""
    problem = getattr(exc, "problem", None) or str(exc)
    return ContentError(f"{path}{where}: YAML syntax error: {problem}")


def _read_yaml(path: Path) -> object:
    try:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise _yaml_error(path, exc) from exc


def _is_translation(path: Path) -> bool:
    """True per i file tradotti: "mathsport.it.md" ha il suffisso di una lingua prima dell'estensione."""
    return Path(path.stem).suffix.lstrip(".") in LANGUAGES


def _translated(path: Path, lang: str) -> Path:
    """File da leggere per una lingua: la versione tradotta se esiste, altrimenti quella inglese."""
    if lang == DEFAULT_LANGUAGE:
        return path
    candidate = path.with_name(f"{path.stem}.{lang}{path.suffix}")
    return candidate if candidate.is_file() else path


def _base_files(content_dir: Path) -> list[Path]:
    """Tutti i file di contenuto in inglese (esclusi i tradotti e le stringhe di interfaccia)."""
    files = [p for p in content_dir.glob("*.yaml") if p.name not in (I18N_FILE, PRIVATE_FILE)]
    files += content_dir.glob("*/*.md")
    return sorted(p for p in files if not _is_translation(p))


def missing_translations(lang: str, content_dir: Path = CONTENT_DIR) -> list[str]:
    """File senza la versione nella lingua indicata (path relativi a content/)."""
    if lang == DEFAULT_LANGUAGE:
        return []
    return [
        str(p.relative_to(content_dir)) for p in _base_files(content_dir) if _translated(p, lang) == p
    ]


def _load_yaml_model[M: BaseModel](model: type[M], path: Path, lang: str) -> M:
    path = _translated(path, lang)
    return _validate(model, _read_yaml(path), path)


def _load_skill_categories(path: Path) -> list[SkillCategory]:
    # In skills.yaml le skill sono annidate sotto la categoria: qui aggiungiamo
    # a ogni skill l'id della sua categoria.
    categories = []
    for raw in _read_yaml(path):
        skills = [{**s, "category": raw.get("id")} for s in raw.get("skills", [])]
        categories.append(_validate(SkillCategory, {**raw, "skills": skills}, path))
    return categories


def _load_collection[M: BaseModel](folder: Path, model: type[M], lang: str, errors: list[str]) -> list[M]:
    """Un file Markdown per elemento: frontmatter = campi, corpo = `body`.

    Un file con errori viene saltato e il problema aggiunto a `errors`, così si vedono tutti insieme.
    """
    items = []
    for base in sorted(folder.glob("*.md")):
        if _is_translation(base):
            continue
        path = _translated(base, lang)
        try:
            try:
                post = frontmatter.load(path)
            except yaml.YAMLError as exc:
                raise _yaml_error(path, exc, first_line=2) from exc
            items.append(_validate(model, {**post.metadata, "body": post.content}, path))
        except ContentError as exc:
            errors.append(str(exc))
    return items


def _attempt(errors: list[str], load, *args):
    """Esegue un caricamento; in caso di ContentError registra il messaggio e restituisce None."""
    try:
        return load(*args)
    except ContentError as exc:
        errors.append(str(exc))
        return None


def load_all(content_dir: Path = CONTENT_DIR, lang: str = DEFAULT_LANGUAGE) -> SiteContent:
    """Legge e valida tutti i contenuti in una lingua.

    Solleva ContentError con l'elenco di tutti i file che hanno problemi, non solo il primo.
    """
    if lang not in LANGUAGES:
        raise ContentError(f"unknown language {lang!r} (expected one of {LANGUAGES})")
    errors: list[str] = []
    experiences = _load_collection(content_dir / "experiences", Experience, lang, errors)
    education = _load_collection(content_dir / "education", Education, lang, errors)
    projects = _load_collection(content_dir / "projects", Project, lang, errors)
    publications = _load_collection(content_dir / "publications", Publication, lang, errors)
    data = {
        "profile": _attempt(errors, _load_yaml_model, Profile, content_dir / "profile.yaml", lang),
        "pages": _attempt(errors, _load_yaml_model, Pages, content_dir / "pages.yaml", lang),
        "skill_categories": _attempt(errors, _load_skill_categories, _translated(content_dir / "skills.yaml", lang)),
        "services": _attempt(errors, _load_yaml_model, Services, content_dir / "services.yaml", lang),
        # Ordine cronologico inverso: la più recente prima
        "experiences": sorted(experiences, key=lambda e: e.start, reverse=True),
        "education": sorted(education, key=lambda e: e.start, reverse=True),
        "projects": projects,
        "publications": sorted(publications, key=lambda p: p.published, reverse=True),
    }
    if errors:
        # I controlli tra file (skill, link) hanno senso solo quando tutti i file si leggono
        raise ContentError(f"{len(errors)} file(s) with errors:\n\n" + "\n\n".join(errors))
    return _validate(SiteContent, data, content_dir)


def load_ui_strings(lang: str, content_dir: Path = CONTENT_DIR) -> tuple[UiStrings, list[str]]:
    """Stringhe di interfaccia di una lingua e l'elenco delle chiavi che mancano.

    La sezione inglese deve essere completa; nelle altre lingue le chiavi
    mancanti prendono il valore inglese.
    """
    path = content_dir / I18N_FILE
    raw = _read_yaml(path) or {}
    english = raw.get(DEFAULT_LANGUAGE) or {}
    translated = raw.get(lang) or {}
    unknown = set(translated) - set(english)
    if unknown:
        raise ContentError(f"{path}: unknown keys for {lang!r}: {sorted(unknown)}")
    strings = _validate(UiStrings, {**english, **translated}, path)
    missing = [] if lang == DEFAULT_LANGUAGE else sorted(set(english) - set(translated))
    return strings, missing
