# CV in PDF: schema dei contenuti

Il CV si genera dagli stessi file di `content/` che alimentano il sito:

```bash
python scripts/build_cv.py --lang all --variant public
```

Tutti i campi del CV sono **opzionali**. Se un campo manca si usa il testo del sito (vedi "Fallback") e lo script lo segnala in un warning. Il sito non usa nessuno di questi campi.

Le lingue funzionano come nel resto del sito: i testi italiani vanno nei file `.it` (`freelance.it.md`, `cv.it.yaml`).

## Esperienze (`content/experiences/*.md`)

Ogni highlight dell'esperienza diventa **un bullet del CV**, senza limite di numero. Il bullet è solo il `cv_summary` dell'highlight: nel CV non compaiono `text`/`title` dell'highlight, il settore (`tag`) né le `metrics` (i numeri vanno scritti dentro `cv_summary`). Sotto ruolo, azienda e date non si stampa nessun riassunto dell'esperienza (il `summary` del sito non si usa).

Campo a livello di esperienza:

| Campo | Tipo | Default | Uso |
|---|---|---|---|
| `cv` | bool | `true` | `false` esclude l'esperienza dal CV |

Campi dentro ogni highlight (tutti opzionali):

| Campo | Default | Uso |
|---|---|---|
| `cv_summary` | fallback con warning (vedi sotto) | il testo del bullet, 1–3 righe |
| `cv` | `true` | `false` esclude l'highlight dal CV |
| `cv_title` | `title`, altrimenti `text` | solo nel fallback: il testo del bullet quando manca `cv_summary` |

Senza `cv_summary` il bullet mostra `cv_title` (o `title`, o `text`) seguito dal settore (`tag`), e lo script lo segnala nel warning. Il testo accetta Markdown inline (`**grassetto**`, `[link](https://...)`).

### Esempio

```yaml
---
id: mathsport
role: Data Scientist & Analytics Manager
company: Math&Sport
# ... altri campi del sito, invariati ...
highlights:
  - text: Managed DevOps activities           # sul sito; nel CV non compare
    metrics:                                 # sul sito; nel CV non compaiono
      - label: Manual setup per match
        value: "~150 min → ~0"
    cv_summary: >-
      Automated the weekend setup on AWS (configuration, EC2 instances, data storage):
      from about 150 minutes per match to almost zero.
  - text: Internal tooling                   # non va nel CV
    cv: false
skills: [python, aws, docker]
---
```

I campi `cv_summary`, `cv_title` e `cv` vanno **rientrati come gli altri campi dell'highlight** (4 spazi, allineati a `metrics:`). La versione italiana (`mathsport.it.md`) ha gli stessi campi, con i testi in italiano.

## Formazione e certificati (`content/education/*.md`)

| Campo | Tipo | Default | Uso |
|---|---|---|---|
| `cv` | bool | `true` | `false` esclude la voce |
| `cv_summary` | testo | nessuno | riga sotto titolo, ente, date e voto |

Lauree (`kind: degree`) e scuole (`kind: school`) vanno nella sidebar dopo le skill, prima le lauree. I certificati (`kind: certificate`) vanno nella sidebar dopo la formazione, con titolo, ente e anno.

## Progetti e pubblicazioni

| File | Campo | Default |
|---|---|---|
| `content/projects/*.md` | `cv` (bool), `cv_summary` (testo) | `true`, `summary` |
| `content/publications/*.md` | `cv` (bool) | `true` |

Una sezione senza voci non compare.

## Impostazioni generali (`content/cv.yaml`, `content/cv.it.yaml`)

```yaml
summary: >-                 # profilo in testa al CV (default: profile.summary, con warning)
  Data scientist with 10+ years of experience...
website: https://lorenzodustycosta.github.io/en/   # opzionale: sito nell'intestazione, dopo l'email
skills: [python, sql, polars, xgboost, forecasting, aws, gcp, docker]
                            # id di skills.yaml; nella sidebar raggruppati per categoria
                            # (default: tutte le skill con toolbox: true, con warning)
languages:                  # default: profile.languages, senza livello
  - {name: Italian, level: Native}
  - {name: English, level: C1}
gdpr: >-                    # obbligatorio: riga finale del CV
  I authorise the processing of the personal data contained in this CV ...
max_pages: 2                # oltre questo numero di pagine lo script fallisce
labels:                     # obbligatorio: titoli delle sezioni
  contact: Contact          # intestazione: luogo, email, telefono
  online: Online            # intestazione: sito, LinkedIn, GitHub
  summary: Profile
  experience: Experience
  publications: Publications
  projects: Projects
  certificates: Certificates
  education: Education
  skills: Skills
  languages: Languages
```

Un id di skill sconosciuto fa fallire lo script.

## Contatti privati (`content/private.yaml`, solo variante `full`)

Il file è in `.gitignore` e **non va mai committato**: il repository è pubblico.

```yaml
phones: ["+39 ..."]         # obbligatorio, almeno uno
address: ...                # opzionale
```

La variante `public`, quella pubblicabile, ignora questo file anche quando esiste. Nell'intestazione mostra luogo, email, LinkedIn e GitHub (da `profile.yaml`).

## Fallback e warning

| Manca | Si usa | Warning |
|---|---|---|
| `cv_summary` di un highlight | `cv_title`, `title` o `text` dell'highlight, con il settore | `experiences/<id>: cv_summary of highlight N` |
| `cv_summary` (progetto) | `summary` | no |
| `summary` in `cv.yaml` | `profile.summary` | `cv.yaml: summary` |
| `skills` in `cv.yaml` | skill della Toolbox | `cv.yaml: skills` |
| `languages` in `cv.yaml` | `profile.languages` | no |

## Ordine e layout

- Esperienze, formazione e pubblicazioni sono in ordine cronologico inverso, come nel sito. Per togliere una voce si usa `cv: false`.
- Nel DOM l'ordine è: nome e contatti, profilo, esperienze, pubblicazioni, progetti, skill, formazione, certificati, lingue, GDPR. La sidebar appare a sinistra solo per effetto del CSS. Attenzione: chi estrae il testo dal PDF (pdftotext, pypdf, gli ATS) lo fa **pagina per pagina**, quindi la sidebar di pagina 1 viene letta prima delle voci che continuano a pagina 2. L'ordine del DOM vale per intero solo nella struttura del PDF taggato.
- Nella sidebar compaiono solo le categorie di skill con almeno una voce in `skills` di `cv.yaml`.
- Impaginazione: un bullet non si spezza mai fra due pagine. Ruolo, azienda e date restano nella stessa pagina dei primi due bullet dell'esperienza (o dell'unico, se è uno solo); poi l'esperienza può continuare nella pagina dopo, fra un bullet e l'altro. Ogni titolo di sezione resta con l'intestazione della prima voce. È fatto con un wrapper `.cv-keep` (`break-inside: avoid`), perché `break-after: avoid` sui titoli in Chromium non è affidabile.
- Parole col trattino ("sport-tech") non vanno mai a capo sul trattino (filtro `cv_inline`): pdftotext le ricomporrebbe senza trattino ("sporttech").
- Template: `templates/cv/cv.html`. Stile: `static/css/cv.css`, che importa font e colori da `static/css/tokens.css`, gli stessi del sito.
