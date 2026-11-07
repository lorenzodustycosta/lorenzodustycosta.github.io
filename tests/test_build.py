import re
import shutil

import pytest

import build
from sitegen.content import ContentError, load_all
from sitegen.render import keep_hyphenated, make_env, make_url, month_year


def test_make_url_joins_base_and_path():
    assert make_url("", "css/main.css") == "/css/main.css"
    assert make_url("/sub/", "/css/main.css") == "/sub/css/main.css"


def test_keep_hyphenated_wraps_only_hyphenated_words():
    assert keep_hyphenated("Day-ahead <b> forecast") == '<span class="nowrap">Day-ahead</span> &lt;b&gt; forecast'


@pytest.mark.parametrize(
    ("value", "expected"),
    [("2020-01", "Jan 2020"), ("2011", "2011"), ("present", "Present"), (None, "")],
)
def test_month_year(value, expected):
    assert month_year(value) == expected


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    dist_dir = tmp_path_factory.mktemp("site") / "dist"
    build.build(base_url="", site_url="https://example.com", dist_dir=dist_dir)
    return dist_dir


@pytest.mark.parametrize(
    "page",
    ["index.html", "experience/index.html", "education/index.html", "projects/index.html",
     "contact/index.html", "404.html", "sitemap.xml", "robots.txt", "css/main.css",
     "en/index.html", "en/experience/index.html", "en/education/index.html", "en/projects/index.html",
     "en/contact/index.html"],
)
def test_build_writes_page(dist, page):
    assert (dist / page).is_file()


def test_pages_use_absolute_links_and_meta(dist):
    index = (dist / "index.html").read_text(encoding="utf-8")
    assert 'href="/css/main.css"' in index
    assert '<meta name="description"' in index
    assert 'property="og:url" content="https://example.com/"' in index
    assert "noindex" not in index


def test_education_shows_details(dist):
    html = (dist / "en" / "education" / "index.html").read_text(encoding="utf-8")
    assert "Numerical Solution of Diffusion Equations" in html
    assert "Heat in a Battery" in html
    assert "Numerical methods" in html  # elenco delle skill
    # Titolo originale della tesi sotto quello tradotto, marcato come italiano
    title = html.index("Theoretical Analysis and Computational Aspects")
    original = html.index('<p class="title-original" lang="it">Analisi Teorica')
    assert title < original


def test_toolbox_hides_skills_marked_false(dist):
    home = (dist / "en" / "index.html").read_text(encoding="utf-8")
    education = (dist / "en" / "education" / "index.html").read_text(encoding="utf-8")
    assert "Crank–Nicolson" not in home
    assert "Crank–Nicolson" in education  # resta nella card della summer school
    assert "Domain &amp; Interest" in home
    assert "Aerospace" in home


def test_experience_shows_highlight_details(dist):
    html = (dist / "en" / "experience" / "index.html").read_text(encoding="utf-8")
    assert "<details>" in html
    assert "XGBoost quantile model" in html  # voce di `details`
    assert "post-match analysis platform" in html  # testo di `context`
    assert '<span class="tag">renewable energy</span>' in html


def test_metrics_follow_their_highlight(dist):
    html = (dist / "en" / "experience" / "index.html").read_text(encoding="utf-8")
    assert html.index("Optimized KPI") < html.index("KPI reprocessing time") < html.index("Refactored several microservices")


def test_freelance_skills_are_shown_per_project(dist):
    html = (dist / "en" / "experience" / "index.html").read_text(encoding="utf-8")
    wind = html.index("Built an end-to-end")
    polars = html.index("Optimized KPI")
    assert wind < html.index("XGBoost") < polars
    assert polars < html.index("Python · Polars") < html.index("Refactored several microservices")
    # Il filtro della Fase 2 legge data-skills: deve contenere anche le skill dei singoli punti
    assert 'data-skills="python xgboost' in html


def test_home_services_link_to_the_right_page(dist):
    home = (dist / "en" / "index.html").read_text(encoding="utf-8")
    assert "What I can do for you" not in home  # frase introduttiva tolta
    assert 'href="/en/experience/#wallabies"' in home
    assert "Related Works" in home
    assert "Recent work" not in home


def test_service_links_point_to_existing_anchors(dist):
    home = (dist / "en" / "index.html").read_text(encoding="utf-8")
    links = re.findall(r'href="/en/(experience|education)/#([\w-]+)"', home)
    assert links
    for page, anchor in links:
        assert f'id="{anchor}"' in (dist / "en" / page / "index.html").read_text(encoding="utf-8")


def test_intro_links_to_selos_design(dist):
    home = (dist / "en" / "index.html").read_text(encoding="utf-8")
    assert '<a href="https://selosdesign.com">Selos Design</a>' in home


def test_404_is_not_indexed(dist):
    assert "noindex" in (dist / "404.html").read_text(encoding="utf-8")


def test_no_phone_numbers_published(dist):
    # Vincolo di privacy: niente numeri di telefono sul sito
    for html in dist.rglob("*.html"):
        assert "tel:" not in html.read_text(encoding="utf-8")


def test_production_build_has_no_dev_pages(dist):
    assert not (dist / "_dev").exists()
    assert "_dev" not in (dist / "sitemap.xml").read_text(encoding="utf-8")
    for html in dist.rglob("*.html"):
        assert "fonts.googleapis.com" not in html.read_text(encoding="utf-8")


def test_email_links_have_subject(dist):
    for page in ["en/index.html", "en/contact/index.html"]:
        html = (dist / page).read_text(encoding="utf-8")
        assert "mailto:lorenzodusty.costa@gmail.com?subject=Contact%20from%20website" in html
        assert 'href="mailto:lorenzodusty.costa@gmail.com"' not in html


def site_with_analytics(**kwargs):
    site = load_all(**kwargs)
    profile = site.profile.model_copy(update={"analytics_token": "0123456789abcdef0123456789abcdef"})
    return site.model_copy(update={"profile": profile})


@pytest.mark.parametrize("dev", [False, True])
def test_analytics_only_in_production(tmp_path, monkeypatch, dev):
    monkeypatch.setattr(build, "load_all", site_with_analytics)
    build.build(base_url="", site_url="https://example.com", dist_dir=tmp_path / "dist", dev=dev)
    html = (tmp_path / "dist" / "index.html").read_text(encoding="utf-8")
    assert "Analytics rispettosi della privacy, senza cookie." in html
    script = re.search(r"<script defer src=\"https://static\.cloudflareinsights\.com/beacon\.min\.js\"[^>]*>", html)
    if dev:
        assert script is None
    else:
        assert script is not None
        assert '"token": "0123456789abcdef0123456789abcdef"' in script.group(0)


def test_home_has_no_about_or_meta_line(dist):
    home = (dist / "en" / "index.html").read_text(encoding="utf-8")
    assert "<img" not in home.split('<section class="section"')[0]  # senza photo in profile.yaml, nessuna foto
    assert "Available for freelance projects" not in home
    assert 'id="about-title"' not in home  # l'intro dell'hero basta
    assert "ruler" not in home and "ruled" not in home


def test_home_sections_share_the_same_title_style(dist):
    home = (dist / "en" / "index.html").read_text(encoding="utf-8")
    titles = re.findall(r'<h2 class="section-title" id="[^"]+">([^<]+)</h2>', home)
    assert titles == ["Services", "How I work", "Selected work", "Experience", "Toolbox"]


def test_featured_projects_on_home(dist):
    home = (dist / "en" / "index.html").read_text(encoding="utf-8")
    cards = re.findall(r'<li class="work">.*?</li>', home, flags=re.S)
    assert len(cards) == 2
    assert '<h3>Probabilistic <span class="nowrap">day-ahead</span> forecasting of wind power production</h3>' in cards[0]
    assert '<h3><span class="nowrap">Real-time</span> data APIs for the Coppa Italia and Supercoppa finals</h3>' in cards[1]
    assert 'href="/en/experience/#mathsport"' in cards[1]
    # In produzione nessuna cornice vuota al posto delle immagini mancanti
    assert "image missing" not in home


def test_services_notes_removed(dist):
    home = (dist / "en" / "index.html").read_text(encoding="utf-8")
    assert "I follow the work through to deployment" not in home
    assert "I prefer working on defined projects" not in home


def site_with_photo(**kwargs):
    site = load_all(**kwargs)
    return site.model_copy(update={"profile": site.profile.model_copy(update={"photo": "img/missing.webp"})})


def test_missing_photo_fails_the_build(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "load_all", site_with_photo)
    with pytest.raises(ContentError, match="img/missing.webp"):
        build.build(dist_dir=tmp_path / "dist")


def test_hero_shows_photo(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "load_all", site_with_photo)
    monkeypatch.setattr(build, "check_static_files", lambda site: None)
    build.build(dist_dir=tmp_path / "dist")
    html = (tmp_path / "dist" / "index.html").read_text(encoding="utf-8")
    assert '<img class="hero-photo" src="/img/missing.webp" alt="Lorenzo Dusty Costa" width="480" height="480"' in html


def test_toolbox_lists_spoken_languages(dist):
    home = (dist / "en" / "index.html").read_text(encoding="utf-8")
    assert "<dt>Spoken languages</dt>" in home
    assert "Italian · English · Turkish" in home


@pytest.fixture(scope="module")
def dev_dist(tmp_path_factory):
    dist_dir = tmp_path_factory.mktemp("dev-site") / "dist"
    build.build(base_url="", site_url="https://example.com", dist_dir=dist_dir, dev=True)
    return dist_dir


def test_dev_build_shows_project_images(dev_dist):
    home = (dev_dist / "en" / "index.html").read_text(encoding="utf-8")
    cards = re.findall(r'<li class="work">.*?</li>', home, flags=re.S)
    assert 'src="/img/projects/wind-forecast.webp"' in cards[0]
    assert 'width="1600" height="900"' in cards[0]
    assert 'src="/img/projects/coppa-italia-2021-final.webp"' in cards[1]
    assert 'width="1600" height="900"' in cards[1]


@pytest.mark.parametrize("dev", [True, False])
def test_missing_image_frame_only_in_dev(dev):
    env = make_env(build.TEMPLATES_DIR, "", "https://example.com")
    template = env.from_string(
        '{% from "partials/macros.html" import media_figure with context %}{{ media_figure(item, reserve=True) }}'
    )
    html = template.render(item={"image": None}, dev=dev)
    assert ("image missing" in html) is dev


def test_font_playground_renders_real_content(dev_dist):
    html = (dev_dist / "_dev" / "fonts.html").read_text(encoding="utf-8")
    assert "noindex" in html
    assert 'src="/_dev/fonts-playground.js"' in html
    assert (dev_dist / "_dev" / "fonts-playground.js").is_file()
    assert 'href="/css/main.css"' in html  # stesso CSS della produzione
    assert "Lavori correlati" in html  # servizi (in italiano, la lingua del sito)
    assert "Setup manuale per partita" in html  # metriche di Math&Sport
    assert "Analisi Teorica" in html  # tesi
    ids = re.findall(r'\bid="([^"]+)"', html)
    assert len(ids) == len(set(ids))
    for target in re.findall(r'aria-labelledby="([^"]+)"', html):
        assert target in ids


# --- Bilingue -------------------------------------------------------------


def test_italian_is_the_site_language(dist):
    html = (dist / "experience" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="it">' in html
    assert 'href="/projects/"' in html
    assert 'rel="canonical" href="https://example.com/experience/"' in html
    assert 'property="og:locale" content="it_IT"' in html
    assert "Esperienza" in html  # testi italiani
    assert "XGBoost quantile model" not in html
    assert not (dist / "it").exists()


def test_english_pages_have_lang_and_prefixed_links(dist):
    html = (dist / "en" / "experience" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="en">' in html
    assert 'href="/en/projects/"' in html
    assert 'rel="canonical" href="https://example.com/en/experience/"' in html
    assert 'property="og:locale" content="en_US"' in html


@pytest.mark.parametrize(("page", "lang"), [("experience/index.html", "it"), ("en/experience/index.html", "en")])
def test_every_page_links_both_languages(dist, page, lang):
    html = (dist / page).read_text(encoding="utf-8")
    assert f'<html lang="{lang}">' in html
    assert '<link rel="alternate" hreflang="it" href="https://example.com/experience/">' in html
    assert '<link rel="alternate" hreflang="en" href="https://example.com/en/experience/">' in html
    assert '<link rel="alternate" hreflang="x-default" href="https://example.com/experience/">' in html
    # Selettore di lingua: testo EN / IT, la lingua corrente marcata
    assert f'hreflang="{lang}" lang="{lang}" aria-current="true">{lang.upper()}</a>' in html


def test_sitemap_lists_both_languages(dist):
    sitemap = (dist / "sitemap.xml").read_text(encoding="utf-8")
    assert "<loc>https://example.com/</loc>" in sitemap
    assert "<loc>https://example.com/en/</loc>" in sitemap
    assert '<xhtml:link rel="alternate" hreflang="en" href="https://example.com/en/projects/"/>' in sitemap
    assert sitemap.count("<url>") == 2 * len(build.PAGES)


def test_404_only_in_italian(dist):
    assert not (dist / "en" / "404.html").exists()
    assert '<html lang="it">' in (dist / "404.html").read_text(encoding="utf-8")


def test_missing_translations_are_reported(monkeypatch, capsys):
    monkeypatch.setattr(build, "missing_translations", lambda lang: ["experiences/mathsport.md"] if lang == "it" else [])
    build.report_missing_translations()
    out = capsys.readouterr().out
    assert "Warning [it]:" in out
    assert "experiences/mathsport.md" in out


def test_complete_translation_builds_without_warnings(tmp_path, capsys):
    build.build(site_url="https://example.com", dist_dir=tmp_path / "dist")
    assert "Warning" not in capsys.readouterr().out


# --- Font self-hosted -----------------------------------------------------


def test_fonts_are_self_hosted(dist):
    css = (dist / "css" / "main.css").read_text(encoding="utf-8")
    fonts = re.findall(r'url\("\.\./fonts/([^"]+)"\)', css)
    assert fonts
    for name in fonts:
        assert (dist / "fonts" / name).is_file()
    index = (dist / "en" / "index.html").read_text(encoding="utf-8")
    for preload in re.findall(r'<link rel="preload" href="/([^"]+)"', index):
        assert (dist / preload).is_file()


# --- Immagini e stato (campi opzionali) -----------------------------------


PNG_640x360 = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (640).to_bytes(4, "big") + (360).to_bytes(4, "big") + bytes(8)


def site_with_project_image(**kwargs):
    site = load_all(**kwargs)
    project = site.projects[0].model_copy(update={
        "image": "img/projects/test.png", "image_alt": "Test chart",
        "image_caption": "Illustrative data", "status": "Open source",
    })
    return site.model_copy(update={"projects": [project, *site.projects[1:]]})


@pytest.fixture
def static_with_image(tmp_path, monkeypatch):
    static = tmp_path / "static"
    shutil.copytree(build.STATIC_DIR, static)
    (static / "img" / "projects").mkdir(parents=True, exist_ok=True)
    (static / "img" / "projects" / "test.png").write_bytes(PNG_640x360)
    monkeypatch.setattr(build, "STATIC_DIR", static)
    return static


def test_project_image_and_status_are_rendered(tmp_path, monkeypatch, static_with_image):
    monkeypatch.setattr(build, "load_all", site_with_project_image)
    build.build(dist_dir=tmp_path / "dist")
    html = (tmp_path / "dist" / "projects" / "index.html").read_text(encoding="utf-8")
    assert '<img src="/img/projects/test.png" alt="Test chart" width="640" height="360"' in html
    assert "<figcaption>Illustrative data</figcaption>" in html
    assert '<span class="status">Open source</span>' in html


def test_missing_project_image_fails_the_build(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "load_all", site_with_project_image)
    with pytest.raises(ContentError, match="img/projects/test.png not found"):
        build.build(dist_dir=tmp_path / "dist")


def test_unsupported_image_format_fails_the_build(tmp_path, monkeypatch, static_with_image):
    (static_with_image / "img" / "projects" / "test.png").write_bytes(b"GIF89a" + bytes(30))
    monkeypatch.setattr(build, "load_all", site_with_project_image)
    with pytest.raises(ContentError, match="unsupported image format"):
        build.build(dist_dir=tmp_path / "dist")


# --- Link interni ---------------------------------------------------------


def test_internal_links_and_anchors_exist(dist):
    """Ogni href/src interno punta a un file esistente e ogni #ancora esiste nella pagina di arrivo."""
    from html.parser import HTMLParser
    from urllib.parse import unquote, urlsplit

    class Collector(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links, self.ids = [], set()

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if "id" in attrs:
                self.ids.add(attrs["id"])
            for name in ("href", "src"):
                if attrs.get(name):
                    self.links.append(attrs[name])

    def parse(path):
        collector = Collector()
        collector.feed(path.read_text(encoding="utf-8"))
        return collector

    def target_file(page, link_path):
        if not link_path:
            return page
        target = dist / unquote(link_path).lstrip("/") if link_path.startswith("/") else page.parent / link_path
        return target / "index.html" if target.is_dir() else target

    pages = {page: parse(page) for page in dist.rglob("*.html")}
    broken = []
    for page, parsed in pages.items():
        for link in parsed.links:
            parts = urlsplit(link)
            if parts.scheme or link.startswith("//"):
                continue  # link esterni e mailto:
            target = target_file(page, parts.path)
            if not target.is_file():
                broken.append(f"{page.relative_to(dist)} -> {link}")
            elif parts.fragment and target.suffix == ".html":
                ids = pages[target].ids if target in pages else parse(target).ids
                if parts.fragment not in ids:
                    broken.append(f"{page.relative_to(dist)} -> {link} (anchor missing)")
    assert not broken, "\n".join(broken)
