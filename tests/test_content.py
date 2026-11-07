import re
import shutil

import pytest

from sitegen.content import CONTENT_DIR, ContentError, load_all, load_ui_strings, missing_translations


@pytest.fixture
def content_copy(tmp_path):
    """Copia di content/ da modificare liberamente nei test."""
    return shutil.copytree(CONTENT_DIR, tmp_path / "content")


@pytest.fixture
def english_only(content_copy):
    """Copia di content/ senza traduzioni italiane, per testare il fallback sull'inglese."""
    for path in content_copy.rglob("*.it.*"):
        path.unlink()
    i18n = content_copy / "i18n.yaml"
    text = i18n.read_text(encoding="utf-8")
    i18n.write_text(text[: text.index("\nit:")] + "\nit: {}\n", encoding="utf-8")
    return content_copy


def edit(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not found in {path}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def test_real_content_is_valid():
    site = load_all()
    assert site.experiences, "no experiences loaded"
    assert site.profile.email


def test_experiences_are_in_reverse_chronological_order():
    starts = [e.start for e in load_all().experiences]
    assert starts == sorted(starts, reverse=True)


def test_unknown_skill_fails(content_copy):
    edit(content_copy / "experiences" / "mathsport.md", "skills: [python,", "skills: [cobol,")
    with pytest.raises(ContentError, match="unknown skills"):
        load_all(content_copy)


def test_unknown_skill_in_education_fails(content_copy):
    edit(content_copy / "education" / "kaggle-sql.md", "skills: [sql]", "skills: [cobol]")
    with pytest.raises(ContentError, match="unknown skills"):
        load_all(content_copy)


def test_unknown_skill_in_highlight_fails(content_copy):
    edit(content_copy / "experiences" / "freelance.md", "skills: [python, polars]", "skills: [cobol]")
    with pytest.raises(ContentError, match="unknown skills"):
        load_all(content_copy)


def test_services_load_and_validate():
    services = load_all().services
    assert [s.id for s in services.services] == ["data-science", "data-analysis"]
    assert all(s.recent_work for s in services.services)
    assert len(services.how_i_work) == 5


def test_unknown_service_link_fails(content_copy):
    edit(content_copy / "services.yaml", "link: freelance", "link: does-not-exist")
    with pytest.raises(ContentError, match="unknown link"):
        load_all(content_copy)


def test_start_after_end_fails(content_copy):
    edit(content_copy / "experiences" / "mathsport.md", "end: 2023-10", "end: 2019-10")
    with pytest.raises(ContentError, match="after end"):
        load_all(content_copy)


def test_malformed_date_fails(content_copy):
    edit(content_copy / "experiences" / "mathsport.md", "start: 2020-01", "start: 01/2020")
    with pytest.raises(ContentError, match="mathsport.md"):
        load_all(content_copy)


def test_duplicate_id_fails(content_copy):
    edit(content_copy / "experiences" / "sisal.md", "id: sisal", "id: mathsport")
    with pytest.raises(ContentError, match="duplicate ids"):
        load_all(content_copy)


def test_unexpected_field_fails(content_copy):
    # Un refuso nel nome di un campo non deve passare inosservato
    edit(content_copy / "experiences" / "sisal.md", "summary:", "sumary:")
    with pytest.raises(ContentError, match="sisal.md"):
        load_all(content_copy)


# --- Lingue ---------------------------------------------------------------


def test_italian_falls_back_to_english(english_only):
    assert load_all(english_only, lang="it").experiences == load_all(english_only).experiences


def test_real_italian_translation_is_complete():
    assert missing_translations("it") == []
    assert load_ui_strings("it")[1] == []
    italian = load_all(lang="it")
    assert [e.id for e in italian.experiences] == [e.id for e in load_all().experiences]


def test_italian_file_is_used_when_present(english_only):
    content_copy = english_only
    original = content_copy / "experiences" / "mathsport.md"
    translated = content_copy / "experiences" / "mathsport.it.md"
    shutil.copy(original, translated)
    edit(translated, "role: Data Scientist & Analytics Manager", "role: ROLE IN ITALIAN")

    english = {e.id: e for e in load_all(content_copy).experiences}
    italian = {e.id: e for e in load_all(content_copy, lang="it").experiences}
    assert english["mathsport"].role == "Data Scientist & Analytics Manager"  # il file .it non entra nell'inglese
    assert italian["mathsport"].role == "ROLE IN ITALIAN"
    assert len(italian) == len(english)  # niente doppioni
    assert "experiences/mathsport.md" not in missing_translations("it", content_copy)
    assert "experiences/sisal.md" in missing_translations("it", content_copy)


def test_italian_yaml_is_used_when_present(english_only):
    content_copy = english_only
    shutil.copy(content_copy / "services.yaml", content_copy / "services.it.yaml")
    edit(content_copy / "services.it.yaml", "related_works_label: Related Works", "related_works_label: ITALIAN LABEL")
    assert load_all(content_copy, lang="it").services.related_works_label == "ITALIAN LABEL"
    assert "services.yaml" not in missing_translations("it", content_copy)


def test_missing_translations_lists_all_files_and_skips_english(english_only):
    missing = missing_translations("it", english_only)
    assert "profile.yaml" in missing
    assert "experiences/freelance.md" in missing
    assert "i18n.yaml" not in missing
    assert missing_translations("en", english_only) == []


def test_unknown_language_fails():
    with pytest.raises(ContentError, match="unknown language"):
        load_all(lang="fr")


def test_ui_strings_fall_back_to_english(english_only):
    content_copy = english_only
    edit(content_copy / "i18n.yaml", "it: {}", "it:\n  toolbox: ITALIAN TOOLBOX")
    strings, missing = load_ui_strings("it", content_copy)
    assert strings.toolbox == "ITALIAN TOOLBOX"
    assert strings.services == "Services"
    assert "services" in missing and "toolbox" not in missing
    assert load_ui_strings("en", content_copy)[1] == []


def test_unknown_ui_string_fails(english_only):
    content_copy = english_only
    edit(content_copy / "i18n.yaml", "it: {}", "it:\n  abuot: typo")
    with pytest.raises(ContentError, match="unknown keys"):
        load_ui_strings("it", content_copy)


# --- Immagini e stato -----------------------------------------------------


def test_image_without_alt_fails(content_copy):
    edit(content_copy / "experiences" / "sisal.md", "summary:", "image: img/projects/x.webp\nsummary:")
    with pytest.raises(ContentError, match="image_alt is required"):
        load_all(content_copy)


def test_media_fields_are_optional_and_validated(content_copy):
    path = content_copy / "projects" / "torneo-copa-mundial.md"
    # Toglie i campi immagine reali, così il test non dipende dai contenuti
    path.write_text(re.sub(r"(?m)^image\w*: .*\n", "", path.read_text(encoding="utf-8")), encoding="utf-8")
    edit(
        path,
        "summary:",
        "status: In production\nimage: img/projects/x.webp\nimage_alt: Screenshot\nimage_caption: Home page\nsummary:",
    )
    project = load_all(content_copy).projects[0]
    assert (project.status, project.image, project.image_alt) == ("In production", "img/projects/x.webp", "Screenshot")


def test_featured_highlights_in_order():
    featured = load_all().featured_highlights
    assert [exp.id for exp, _ in featured] == ["freelance", "mathsport"]
    assert all(h.title for _, h in featured)


def test_highlight_image_without_alt_fails(content_copy):
    path = content_copy / "experiences" / "mathsport.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(re.sub(r"(?m)^    image_alt: .*\n", "", text, count=1), encoding="utf-8")
    assert "image_alt" not in path.read_text(encoding="utf-8")
    with pytest.raises(ContentError, match="image_alt is required"):
        load_all(content_copy)


def test_yaml_syntax_error_names_the_file(content_copy):
    edit(content_copy / "experiences" / "sisal.md", "    details:\n", "    details: ->\n")
    with pytest.raises(ContentError, match=r"sisal\.md, line 16: YAML syntax error"):
        load_all(content_copy)


def test_all_broken_files_are_reported_together(content_copy):
    edit(content_copy / "experiences" / "sisal.md", "    details:\n", "    details: ->\n")
    edit(content_copy / "education" / "kaggle-sql.md", "kind:", "knid:")
    with pytest.raises(ContentError, match="2 file") as info:
        load_all(content_copy)
    assert "sisal.md" in str(info.value) and "kaggle-sql.md" in str(info.value)
