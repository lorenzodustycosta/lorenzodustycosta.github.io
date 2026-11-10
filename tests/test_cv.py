"""CV in PDF: selezione delle voci, fallback, varianti e (se c'è Chromium) il PDF vero."""

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from sitegen.content import CONTENT_DIR, ContentError, missing_translations
from sitegen.cv import cv_data, render_cv_html

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def content_copy(tmp_path):
    return shutil.copytree(CONTENT_DIR, tmp_path / "content", ignore=shutil.ignore_patterns("private.yaml"))


def edit(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not found in {path}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


@pytest.mark.parametrize("lang", ["it", "en"])
def test_real_content_renders(lang):
    html, _ = render_cv_html(lang, content_dir=CONTENT_DIR)
    assert f'<html lang="{lang}" data-theme="light">' in html
    assert "Lorenzo Dusty Costa" in html
    assert "<details" not in html and "<script" not in html and "<button" not in html


def test_reading_order_for_ats():
    # Nome → contatti → profilo → esperienze → ... → sidebar → GDPR, nell'ordine del DOM
    html, _ = render_cv_html("en", content_dir=CONTENT_DIR)
    html = html[html.index("<body>"):]  # l'<head> ripete nome e ruolo nei meta
    markers = ["<h1>Lorenzo Dusty Costa", "lorenzodusty.costa@gmail.com", ">Profile<", ">Experience<",
               "<h3>Freelance Data Scientist", "<h3>Game Designer", ">Publications<",
               ">Education<", ">Skills<", "<h2>Certificates<", "<h2>Languages<", "Regulation (EU) 2016/679"]
    positions = [html.index(m) for m in markers]
    assert positions == sorted(positions)


def test_public_variant_has_no_phone(content_copy):
    (content_copy / "private.yaml").write_text('phones: ["+39 333 1234567"]\n', encoding="utf-8")
    html, _ = render_cv_html("it", "public", content_dir=content_copy)
    assert "333 1234567" not in html
    assert "tel:" not in html


def test_full_variant_shows_private_contacts(content_copy):
    (content_copy / "private.yaml").write_text('phones: ["+39 333 1234567"]\naddress: Via Esempio 1\n', encoding="utf-8")
    html, _ = render_cv_html("it", "full", content_dir=content_copy)
    assert "+39 333 1234567" in html
    assert "Via Esempio 1" in html


def test_full_variant_without_private_file_fails(content_copy):
    with pytest.raises(ContentError, match="private.yaml not found"):
        cv_data("it", "full", content_dir=content_copy)


def test_private_file_is_not_a_missing_translation(content_copy):
    (content_copy / "private.yaml").write_text('phones: ["1"]\n', encoding="utf-8")
    assert "private.yaml" not in missing_translations("it", content_copy)


def write_experience(content_dir, front=""):
    """Esperienza di prova "demo", indipendente dai testi CV dei contenuti veri."""
    (content_dir / "experiences" / "demo.md").write_text(
        "---\nid: demo\nrole: Demo Role\nstart: 2010-01\nend: 2010-06\nsectors: [sport-tech]\n"
        "type: freelance\nsummary: Site summary of the demo job\nhighlights:\n"
        "  - text: First site bullet\n    title: First activity\n    tag: energy\n"
        "  - text: Second site bullet\n    tag: sport-tech\n"
        "  - text: Third site bullet\n"
        "  - text: Fourth site bullet\n"
        f"{front}---\n", encoding="utf-8")


def demo(data):
    return next(e for e in data.experiences if e.experience.id == "demo")


def test_bullets_are_only_cv_summary(content_copy):
    write_experience(content_copy)
    path = content_copy / "experiences" / "demo.md"
    edit(path, "    tag: energy\n",
         "    tag: energy\n    metrics:\n      - {label: Site metric, value: '-42%'}\n"
         "    cv_summary: First summary for the CV\n")
    edit(path, "    tag: sport-tech\n", "    tag: sport-tech\n    cv_summary: Second summary for the CV\n")
    edit(path, "  - text: Third site bullet\n", "  - text: Third site bullet\n    cv_summary: Third summary\n")
    edit(path, "  - text: Fourth site bullet\n", "  - text: Fourth site bullet\n    cv_summary: Fourth summary\n")
    data = cv_data("en", content_dir=content_copy)
    item = demo(data)
    # Nessun limite: tutti e 4; i primi due restano con ruolo e date (.cv-keep)
    assert [b.text for b in item.bullets] == ["First summary for the CV", "Second summary for the CV",
                                              "Third summary", "Fourth summary"]
    assert [b.text for b in item.head_bullets] == ["First summary for the CV", "Second summary for the CV"]
    assert not any(m.startswith("experiences/demo") for m in data.missing)
    html, _ = render_cv_html("en", content_dir=content_copy)
    assert "First summary for the CV" in html
    for absent in ("First activity", "First site bullet", ">energy<", "Site metric", "-42%",
                   "Site summary of the demo job"):  # titolo, text, tag, metriche, summary dell'esperienza
        assert absent not in html


def test_missing_cv_summary_falls_back_with_warning(content_copy):
    write_experience(content_copy)
    edit(content_copy / "experiences" / "demo.md", "  - text: Second site bullet\n",
         "  - text: Second site bullet\n    cv: false\n")
    data = cv_data("en", content_dir=content_copy)
    item = demo(data)
    assert [(b.text, b.tag, b.fallback) for b in item.bullets] == [
        ("First activity", "energy", True), ("Third site bullet", None, True), ("Fourth site bullet", None, True)]
    assert "experiences/demo: cv_summary of highlight 1 (First activity...)" in data.missing


def test_header_and_first_two_bullets_stay_together():
    html, _ = render_cv_html("en", content_dir=CONTENT_DIR)
    keep = html.index('<div class="cv-keep">', html.index("<h2>Experience</h2>") - 60)
    block = html[keep:html.index("</div>", keep)]
    assert "<h2>Experience</h2>" in block and "<h3>Freelance Data Scientist" in block
    assert block.count("<li>") == 2


def test_cv_false_excludes_entries(content_copy):
    edit(content_copy / "experiences" / "spindox.md", "type: employee", "type: employee\ncv: false")
    edit(content_copy / "education" / "kaggle-sql.md", "kind: certificate", "kind: certificate\ncv: false")
    edit(content_copy / "projects" / "torneo-copa-mundial.md", "title: CopaMundial Website", "title: CopaMundial Website\ncv: false")
    html, _ = render_cv_html("en", content_dir=content_copy)
    assert "Spindox" not in html
    assert "Intro to SQL" not in html
    assert "CopaMundial" not in html
    assert ">Projects<" not in html  # sezione vuota: niente titolo


def test_cv_settings_skills_and_languages(content_copy):
    edit(content_copy / "cv.yaml", "max_pages: 2",
         "max_pages: 2\nskills: [sql, python]\nlanguages:\n  - {name: Italian, level: Native}\nsummary: Short profile")
    data = cv_data("en", content_dir=content_copy)
    assert [(label, [s.id for s in skills]) for label, skills in data.skill_groups] == [("Languages", ["sql", "python"])]
    assert data.languages == [("Italian", "Native")]
    assert data.summary == "Short profile"
    assert not any(m.startswith("cv.yaml") for m in data.missing)


def test_unknown_cv_skill_fails(content_copy):
    edit(content_copy / "cv.yaml", "max_pages: 2", "max_pages: 2\nskills: [no-such-skill]")
    with pytest.raises(ContentError, match="no-such-skill"):
        cv_data("en", content_dir=content_copy)


def test_degrees_before_schools(content_copy):
    data = cv_data("en", content_dir=content_copy)
    kinds = [d.kind for d in data.degrees]
    assert kinds == sorted(kinds, key=lambda k: k != "degree")


def test_cv_css_reuses_site_tokens():
    css = (ROOT / "static" / "css" / "cv.css").read_text(encoding="utf-8")
    assert '@import "tokens.css";' in css
    assert "--link:" not in css and "@font-face" not in css  # nessun token ridefinito


# --- PDF vero: solo se Playwright e Chromium sono installati (requirements-cv.txt) ---


def _chromium_available() -> bool:
    if not (importlib.util.find_spec("playwright") and importlib.util.find_spec("pypdf")):
        return False
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _chromium_available(), reason="Playwright/Chromium not installed (requirements-cv.txt)")
def test_pdf_is_a4_selectable_and_within_page_limit(tmp_path):
    from pypdf import PdfReader

    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_cv.py"), "--lang", "en", "--out", str(tmp_path)],
                   check=True, capture_output=True)
    reader = PdfReader(tmp_path / "cv-en.pdf")
    assert 1 <= len(reader.pages) <= 2
    width, height = (float(v) for v in reader.pages[0].mediabox.upper_right)
    assert (round(width), round(height)) == (595, 842)  # A4 in punti
    text = re.sub(r"\s+", " ", " ".join(page.extract_text() for page in reader.pages))
    # Testo selezionabile e nell'ordine di lettura giusto
    markers = ["Lorenzo Dusty Costa", "lorenzodusty.costa@gmail.com", "Profile", "Experience", "Game Designer"]
    positions = [text.index(m) for m in markers]
    assert positions == sorted(positions)


def test_website_in_header_once(content_copy):
    # Il sito di cv.yaml compare nell'intestazione, anche se è già tra i link del profilo
    edit(content_copy / "profile.yaml", "links:\n", "links:\n  - label: Website\n    url: https://lorenzodustycosta.github.io/en/\n")
    html, _ = render_cv_html("en", content_dir=content_copy)
    header = html[html.index("<header"):html.index("</header>")]
    assert header.count(">lorenzodustycosta.github.io/en<") == 1
