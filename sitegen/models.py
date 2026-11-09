"""Modelli pydantic dei contenuti del sito.

Ogni file in content/ viene validato con uno di questi modelli: un campo
mancante, una data malformata o una skill inesistente fanno fallire la build.
"""

from collections import Counter
from datetime import date
from typing import Annotated, Literal
from urllib.parse import quote

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, HttpUrl, model_validator

# YAML legge `2011` come intero: lo convertiamo in stringa prima di validare il formato.
YearMonth = Annotated[str, BeforeValidator(str), Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]
PartialDate = Annotated[str, BeforeValidator(str), Field(pattern=r"^\d{4}(-(0[1-9]|1[0-2]))?$")]

Sector = Literal["sport-tech", "gaming", "telco", "retail", "energy", "consulting"]


class Model(BaseModel):
    # extra="forbid": un campo con un refuso nel nome è un errore, non viene ignorato
    model_config = ConfigDict(extra="forbid", frozen=True)


class Media(Model):
    """Campi opzionali per immagine ed etichetta di stato (esperienze e progetti).

    `image` è un path dentro static/ (es. "img/projects/wind.webp"): la build
    verifica che il file esista e ne legge le dimensioni.
    """

    image: str | None = None
    image_alt: str | None = None  # obbligatorio se c'è un'immagine
    image_caption: str | None = None  # didascalia, es. "Illustrative data"
    status: str | None = None  # es. "Client project", "Open source", "In production"

    @model_validator(mode="after")
    def check_image_alt(self):
        if self.image and not self.image_alt:
            raise ValueError("image_alt is required when image is set")
        return self


class Skill(Model):
    id: str
    label: str
    category: str
    toolbox: bool = True  # False: visibile solo nelle card, non nella Toolbox della home


class SkillCategory(Model):
    id: str
    label: str
    skills: list[Skill]


class Link(Model):
    label: str
    url: HttpUrl


class Profile(Model):
    name: str
    headline: str
    location: str
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    availability: str
    summary: str
    languages: list[str]
    links: list[Link]
    cv: str | None = None  # path dentro static/, es. "cv/Lorenzo_Dusty_Costa_CV.pdf"
    image: str | None = None  # immagine di anteprima per i social, path dentro static/
    photo: str | None = None  # foto profilo nella home: quadrata, path dentro static/
    email_subject: str | None = None  # oggetto precompilato dei link mailto
    # Token di Cloudflare Web Analytics: è pubblico (finisce comunque nell'HTML), non è un segreto
    analytics_token: str | None = Field(default=None, pattern=r"^[0-9a-zA-Z]+$")
    piva: str | None = Field(default=None, pattern=r"^\d{11}$")  # partita IVA italiana

    @property
    def mailto(self) -> str:
        """Link mailto, con l'oggetto precompilato se c'è."""
        if not self.email_subject:
            return f"mailto:{self.email}"
        return f"mailto:{self.email}?subject={quote(self.email_subject)}"


class PageMeta(Model):
    title: str
    description: str
    nav_label: str | None = None
    intro: str | None = None


class Pages(Model):
    home: PageMeta
    experience: PageMeta
    education: PageMeta
    projects: PageMeta
    contact: PageMeta
    not_found: PageMeta


class RecentWork(Model):
    text: str
    link: str  # id di un'esperienza o di una voce di education


class Service(Model):
    id: str
    title: str
    summary: str
    recent_work: list[RecentWork]


class WorkingMode(Model):
    title: str
    text: str


class Metric(Model):
    label: str
    value: str


class Highlight(Media):
    """Un risultato dentro un'esperienza; con featured: true compare in "Selected work" nella home."""

    text: str  # risultato in breve, sempre visibile
    title: str | None = None  # titolo breve, usato nella card di "Selected work"
    featured: bool = False
    tag: str | None = None  # es. il settore, quando l'esperienza ne copre più di uno
    metrics: list[Metric] = []  # numeri chiave, sempre visibili sotto il punto
    skills: list[str] = []  # per le esperienze con progetti diversi
    context: str | None = None
    details: list[str] = []


class Experience(Media):
    id: str
    role: str
    company: str | None = None
    start: YearMonth
    end: YearMonth | Literal["present"]
    location: str | None = None
    sectors: list[Sector] = Field(min_length=1)
    type: Literal["employee", "freelance"]
    summary: str
    highlights: list[Highlight]
    skills: list[str] = []
    featured: bool = False
    body: str = ""  # dettaglio lungo in Markdown (corpo del file)

    @property
    def all_skills(self) -> list[str]:
        """Skill dell'esperienza e dei singoli punti, senza ripetizioni."""
        return list(dict.fromkeys([*self.skills, *(s for h in self.highlights for s in h.skills)]))

    @model_validator(mode="after")
    def check_dates(self):
        # Le date YYYY-MM si confrontano correttamente come stringhe
        if self.end != "present" and self.start > self.end:
            raise ValueError(f"start ({self.start}) is after end ({self.end})")
        return self


class Thesis(Model):
    title: str
    title_original: str | None = None  # titolo nella lingua originale
    summary: str


class EducationProject(Model):
    title: str
    summary: str


class Education(Model):
    id: str
    title: str
    institution: str
    kind: Literal["degree", "school", "certificate"]
    start: PartialDate
    end: PartialDate | None = None
    grade: str | None = None
    url: HttpUrl | None = None
    description: str | None = None
    topics: list[str] = []
    thesis: Thesis | None = None
    project: EducationProject | None = None
    skills: list[str] = []
    body: str = ""

    @model_validator(mode="after")
    def check_dates(self):
        if self.end is not None and self.start > self.end:
            raise ValueError(f"start ({self.start}) is after end ({self.end})")
        return self


class Project(Media):
    id: str
    title: str
    summary: str
    url: HttpUrl | None = None
    skills: list[str] = []
    body: str = ""


class Publication(Model):
    id: str
    title: str
    venue: str
    publisher: str | None = None
    published: date
    coauthors: list[str] = []
    url: HttpUrl | None = None
    body: str = ""


class UiStrings(Model):
    """Stringhe di interfaccia di una lingua (content/i18n.yaml)."""

    skip_to_content: str
    main_navigation: str
    language: str
    dark_mode: str
    services: str
    selected_work: str
    all_experience: str
    cta_title: str
    cta_text: str
    cta_note: str
    cta_link: str
    hero_email: str
    toolbox: str
    spoken_languages: str
    download_cv: str
    email: str
    location: str
    languages: str
    degrees: str
    schools: str
    certificates: str
    thesis: str
    project: str
    projects: str
    publications: str
    coauthors: str
    back_home: str
    present: str
    months: list[str] = Field(min_length=12, max_length=12)
    privacy_analytics: str
    privacy_hosting: str
    vat_number: str


class Services(Model):
    """Sezione "servizi" della home (services.yaml)."""

    related_works_label: str
    how_i_work_label: str
    services: list[Service]
    how_i_work: list[WorkingMode]
    engagement_models_label: str | None = None
    engagement_models: list[WorkingMode] = []


class SiteContent(Model):
    """Tutti i contenuti del sito, con i controlli che coinvolgono più file."""

    profile: Profile
    pages: Pages
    skill_categories: list[SkillCategory]
    services: Services
    experiences: list[Experience]
    education: list[Education]
    projects: list[Project]
    publications: list[Publication]

    @property
    def featured_highlights(self) -> list[tuple[Experience, Highlight]]:
        """Highlight con featured: true e la loro esperienza, dal più recente."""
        return [(e, h) for e in self.experiences for h in e.highlights if h.featured]

    @property
    def skills(self) -> dict[str, Skill]:
        return {s.id: s for c in self.skill_categories for s in c.skills}

    @model_validator(mode="after")
    def check_unique_ids(self):
        collections = {
            "skills": [s.id for c in self.skill_categories for s in c.skills],
            "services": [s.id for s in self.services.services],
            "experiences": [e.id for e in self.experiences],
            "education": [e.id for e in self.education],
            "projects": [p.id for p in self.projects],
            "publications": [p.id for p in self.publications],
        }
        for name, ids in collections.items():
            duplicates = [i for i, n in Counter(ids).items() if n > 1]
            if duplicates:
                raise ValueError(f"duplicate ids in {name}: {duplicates}")
        return self

    @model_validator(mode="after")
    def check_skill_references(self):
        known = self.skills.keys()
        used = [(e.id, e.all_skills) for e in self.experiences]
        used += [(i.id, i.skills) for i in [*self.education, *self.projects]]
        for item_id, skills in used:
            unknown = set(skills) - known
            if unknown:
                raise ValueError(f"{item_id}: unknown skills {sorted(unknown)} (add them to skills.yaml)")
        return self

    @model_validator(mode="after")
    def check_service_links(self):
        known = {e.id for e in self.experiences} | {e.id for e in self.education}
        for service in self.services.services:
            for work in service.recent_work:
                if work.link not in known:
                    raise ValueError(f"service {service.id}: unknown link {work.link!r}")
        return self
