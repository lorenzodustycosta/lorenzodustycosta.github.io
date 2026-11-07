# Sito personale – Lorenzo Dusty Costa

Sito personale da data scientist freelance, generato da un piccolo generatore statico in Python (Jinja2 + contenuti YAML/Markdown) e pubblicato su GitHub Pages.

## Test locale

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python build.py          # build in dist/
python build.py --serve  # http://localhost:8000, rebuild al salvataggio
# font playground (solo con --serve): http://localhost:8000/_dev/fonts.html
python build.py --serve --lan  # anche dal telefono, sulla stessa rete Wi-Fi: stampa l'indirizzo da aprire
pytest                   # test
```

## Lingue

Italiano su `/` (lingua del sito, `SITE_LANGUAGE` in `sitegen/content.py`), inglese su `/en/`. I file di contenuto base restano in inglese; per tradurre un contenuto crea un file parallelo con il suffisso `.it`:

- `content/experiences/mathsport.md` → `content/experiences/mathsport.it.md` (copia completa, con frontmatter);
- `content/services.yaml` → `content/services.it.yaml`;
- stringhe di interfaccia: sezione `it:` di `content/i18n.yaml` (stesse chiavi della sezione `en:`).

Dove manca la versione italiana la build usa l'inglese e stampa un warning con l'elenco dei file e delle stringhe mancanti.

## Immagini di esperienze e progetti

Campi opzionali nel frontmatter: `image` (path dentro `static/`, es. `img/projects/wind.webp`), `image_alt` (obbligatorio se c'è `image`), `image_caption`, `status` (es. "Client project").
Formati: WebP (consigliato) o PNG. La build verifica che il file esista e ne legge larghezza e altezza.
