# Sito personale – Lorenzo Dusty Costa

Sito personale da data scientist freelance, generato da un piccolo generatore statico in Python (Jinja2 + contenuti YAML/Markdown) e pubblicato su GitHub Pages.

## Test locale

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python build.py          # build in dist/
python build.py --serve  # http://localhost:8000, rebuild al salvataggio
pytest                   # test
```
