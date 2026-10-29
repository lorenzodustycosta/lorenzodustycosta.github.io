import build


def test_make_url_joins_base_and_path():
    assert build.make_url("", "css/main.css") == "/css/main.css"
    assert build.make_url("/sub/", "/css/main.css") == "/sub/css/main.css"


def test_build_writes_index_and_static(tmp_path):
    build.build(base_url="", dist_dir=tmp_path / "dist")

    index = (tmp_path / "dist" / "index.html").read_text(encoding="utf-8")
    assert 'href="/css/main.css"' in index
    assert (tmp_path / "dist" / "css" / "main.css").exists()
