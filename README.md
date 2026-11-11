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

## CV in PDF

Il CV si genera dagli stessi contenuti del sito (`content/`), con i font e i colori del sito. Serve Chromium, che il sito non usa: le dipendenze sono in un file a parte.

```bash
pip install -r requirements-cv.txt
playwright install chromium        # una volta, scarica Chromium headless

python scripts/build_cv.py                       # IT + EN, variante public → static/cv/ (da committare)
python scripts/build_cv.py --lang it             # una sola lingua (it | en | all)
python scripts/build_cv.py --html-only           # solo l'anteprima HTML, senza Chromium
python scripts/build_cv.py --variant full        # anche il telefono, da content/private.yaml
python scripts/build_cv.py --out altra/cartella  # cartella di output diversa
```

- Output: `static/cv/cv-costa-it.pdf` e `cv-costa-en.pdf`, linkati dal sito (`cv` in `profile.yaml`): rigenerali e committali quando cambiano i contenuti, la CI non li produce. Con `--variant full` e `--html-only` l'output va in `build/cv/`, che è in `.gitignore`.
- **Variante `full`**: legge `content/private.yaml` (in `.gitignore`) e scrive `cv-costa-<lang>-full.pdf`, anch'esso ignorato da git. Non va committata né pubblicata.
- Lo script fallisce se un PDF supera `max_pages` (2, in `content/cv.yaml`) o se i font del sito non sono incorporati. Stampa l'elenco degli highlight senza `cv_summary`.
- Campi del CV, fallback ed esempi: [docs/cv-schema.md](docs/cv-schema.md). Il test sul PDF vero (`tests/test_cv.py`) viene saltato se Playwright o Chromium non sono installati.

## Banner LinkedIn

Immagine per il profilo LinkedIn (1584x396), con i font e i colori del sito. Non fa parte del sito: va in `branding/`. Stesse dipendenze del CV (`requirements-cv.txt`).

```bash
python scripts/linkedin_banner.py                 # inglese, grafico a tutta larghezza → branding/linkedin-banner.png
python scripts/linkedin_banner.py --lang it       # italiano → branding/linkedin-banner-it.png
python scripts/linkedin_banner.py --chart left    # grafico solo a sinistra e al centro
python scripts/linkedin_banner.py --chart both    # entrambe le varianti (-full, -left), per confrontarle
```

- Ogni banner ha un `*-preview.png` con l'area della foto profilo (desktop) e la zona sicura del testo (mobile).
- Lo script fallisce se un testo esce dalla zona sicura, tocca l'area della foto o ha contrasto sotto 4.5:1 sui pixel reali dello sfondo.
- Il grafico usa una serie eolica sintetica: i dati dell'immagine del sito non sono nel repository.

## Lingue

Italiano su `/` (lingua del sito, `SITE_LANGUAGE` in `sitegen/content.py`), inglese su `/en/`. I file di contenuto base restano in inglese; per tradurre un contenuto crea un file parallelo con il suffisso `.it`:

- `content/experiences/mathsport.md` → `content/experiences/mathsport.it.md` (copia completa, con frontmatter);
- `content/services.yaml` → `content/services.it.yaml`;
- stringhe di interfaccia: sezione `it:` di `content/i18n.yaml` (stesse chiavi della sezione `en:`).

Dove manca la versione italiana la build usa l'inglese e stampa un warning con l'elenco dei file e delle stringhe mancanti.

## Immagini di esperienze e progetti

Campi opzionali nel frontmatter: `image` (path dentro `static/`, es. `img/projects/wind.webp`), `image_alt` (obbligatorio se c'è `image`), `image_caption`, `status` (es. "Client project").
Formati: WebP (consigliato) o PNG. La build verifica che il file esista e ne legge larghezza e altezza.
