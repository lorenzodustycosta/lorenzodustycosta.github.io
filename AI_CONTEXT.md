# Sito personale – Lorenzo Dusty Costa, Data Scientist freelance

> Documento di progetto per agenti di sviluppo (Claude Code, Codex, ecc.).
> Va nella root del repository. Leggilo per intero prima di scrivere codice.

---

## 0. Istruzioni per l'agente

- **Lavora una fase alla volta.** Non anticipare funzionalità di fasi successive. Alla fine di ogni fase fermati, riassumi cosa hai fatto e verifica i criteri di accettazione insieme a me prima di proseguire.
- **Chiedi prima di decidere** su tutto ciò che è marcato `[DA DECIDERE]`.
- **Il proprietario conosce bene Python e poco JavaScript.** Scrivi codice Python idiomatico e leggibile; il JavaScript deve essere vanilla, minimo, commentato e senza build step. **Niente TypeScript, niente Node.js/npm, niente framework frontend.**
- Preferisci soluzioni semplici e poche dipendenze. Ogni nuova dipendenza va motivata.
- Commit piccoli e descrittivi (Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `content:`).
- Nessuna dipendenza o servizio a pagamento senza mia conferma esplicita.
- Nessun segreto (API key, token) nel repository. Mai.
- Mantieni aggiornata la sezione **Stato avanzamento** in fondo a questo file.

---

## 1. Obiettivo

Sito web personale per promuovere la mia attività di data scientist freelance:

1. presentare chi sono e quali servizi offro;
2. mostrare esperienze lavorative e accademiche con **più dettaglio del CV**, in modo **interattivo**;
3. in futuro, un **chatbot** che risponde a domande su di me tramite RAG su un backend Python.

Pubblico principale: recruiter, potenziali clienti, CTO/responsabili tecnici. Molti visiteranno da **mobile** (es. da LinkedIn).

---

## 2. Vincoli

| Vincolo | Dettaglio |
|---|---|
| Hosting | **GitHub Pages**, gratuito |
| Dominio | **Nessun dominio a pagamento**: `https://<username>.github.io` |
| Repository | Deve chiamarsi esattamente `<username>.github.io` → `lorenzodustycosta.github.io` |
| Sito | Solo file statici (GitHub Pages non esegue codice server) |
| Backend (Fase 4) | Python, ospitato separatamente su free tier |
| Costi | Zero, salvo i consumi dell'API LLM in Fase 4 (pochi €/mese, con tetto di spesa) |
| Privacy | Niente cookie di tracciamento → niente banner GDPR. Non pubblicare i numeri di telefono |

---

## 3. Stack tecnico

Generatore di sito statico **scritto in Python**, su misura:

| Componente | Scelta |
|---|---|
| Linguaggio build | Python 3.12+ |
| Template | **Jinja2** (sintassi simile ai template Django) |
| Contenuti | YAML + Markdown con frontmatter (`python-frontmatter`) |
| Markdown → HTML | `markdown-it-py` (o `markdown`) |
| Validazione dati | **pydantic** (un errore nei contenuti fa fallire la build) |
| Server locale | `python build.py --serve`: build + `http.server` + rebuild automatico al salvataggio (`watchfiles`) |
| CSS | CSS puro con variabili (design token), un solo file principale. Niente preprocessori |
| JavaScript | Vanilla ES modules, nessun bundler, caricato con `<script type="module" defer>` |
| Grafici (Fase 2, opz.) | Observable Plot o D3 da CDN, solo nelle pagine che li usano |
| Test | pytest |
| Gestione dipendenze | `requirements.txt` + venv (deciso) |
| Deploy | GitHub Actions: `python build.py` → `actions/upload-pages-artifact` → `actions/deploy-pages` |

---

## 4. Principio architetturale chiave: contenuti come dati

**Tutti i contenuti** (esperienze, formazione, progetti, pubblicazioni, skill, servizi) vivono in file strutturati dentro `content/`, **mai hard-coded nei template**.

Gli stessi file alimenteranno:
1. le pagine del sito;
2. i dettagli interattivi;
3. la knowledge base del chatbot (Fase 4).

La lettura e validazione dei contenuti è in un **modulo Python riusabile** (`sitegen/content.py`) che in Fase 4 verrà importato anche dal backend del chatbot. Una sola fonte di verità, un solo codice che la legge.

### Struttura repository

```
/
├─ PROJECT_PLAN.md            # questo file
├─ README.md
├─ requirements.txt
├─ build.py                   # entry point: python build.py [--serve]
├─ .github/workflows/
│   └─ deploy.yml
├─ content/
│   ├─ profile.yaml           # nome, headline, contatti pubblici, link
│   ├─ skills.yaml            # tassonomia skill (id, label, categoria)
│   ├─ services.yaml
│   ├─ experiences/           # un .md per esperienza (frontmatter + corpo = dettaglio lungo)
│   ├─ education/
│   ├─ projects/
│   └─ publications/
├─ sitegen/                   # package Python del generatore
│   ├─ __init__.py
│   ├─ models.py              # modelli pydantic (Experience, Skill, Project, ...)
│   ├─ content.py             # load_all() → oggetti validati; riusato dal backend
│   ├─ render.py              # Jinja2 + Markdown → HTML
│   └─ seo.py                 # sitemap.xml, robots.txt, meta tag
├─ templates/
│   ├─ base.html
│   ├─ partials/              # header, footer, experience_card.html, ...
│   └─ pages/                 # index.html, experience.html, projects.html, ...
├─ static/
│   ├─ css/main.css
│   ├─ js/                    # experiences.js, filters.js, theme.js
│   ├─ img/
│   └─ cv/Lorenzo_Dusty_Costa_CV.pdf
├─ tests/
├─ dist/                      # output della build (in .gitignore)
└─ backend/                   # solo dalla Fase 4
```

### Schema esperienza (frontmatter)

```yaml
---
id: mathsport
role: Data Scientist & Analytics Manager
company: Math&Sport
start: 2020-01
end: 2023-10            # oppure "present"
location: Milan, Italy
sector: sport-tech      # sport-tech | gaming | telco | retail | energy | consulting
type: employee          # employee | freelance
summary: >
  Riassunto breve, 1–2 righe, coerente col CV.
highlights:             # bullet del CV (versione compatta)
  - ...
skills: [python, aws, docker, kubernetes, api-design, devops]
metrics:                # numeri chiave, opzionali
  - label: Weekend ops workload
    value: "-50%"
featured: true          # candidato a case study
order: 3
---

Corpo Markdown = **dettaglio lungo** mostrato all'espansione:
contesto, problema, approccio, stack, risultati, cosa ho imparato.
```

Validazioni minime in `models.py`:
- gli `id` delle skill usati nelle esperienze devono esistere in `skills.yaml`;
- `start` ≤ `end`; date in formato `YYYY-MM`;
- `id` univoci per collection.

---

## Convenzione di metodo (importante quanto il codice)
A ogni bivio tecnico non banale, annotare in una riga la decisione e il perché,
in un file `DECISIONS.md` alla root. Formato: "scelto X invece di Y perché Z".
Queste note servono sia da documentazione sia come materiale da spiegare a un
cliente. Quando prendi una decisione di design significativa, proponi la riga da aggiungere a DECISIONS.md.

## 5. Fasi di sviluppo

### Fase 0 – Setup

**Task**
- [ ] Struttura cartelle come da §4, `.gitignore` (venv, `dist/`, `__pycache__`)
- [ ] `requirements.txt` con le dipendenze del §3
- [ ] `build.py` minimale: copia `static/`, renderizza `templates/pages/index.html` in `dist/`
- [ ] Opzione `--serve`: server locale su `http://localhost:8000` con rebuild al salvataggio
- [ ] Gestione dei path assoluti: tutti i link generati partono da una `BASE_URL` configurabile
- [ ] Workflow `.github/workflows/deploy.yml`: setup Python, install, build, deploy su Pages a ogni push su `main`
- [ ] README con i comandi: creazione venv, install, `python build.py`, `python build.py --serve`, `pytest`
- [ ] Pagina placeholder online

**Criteri di accettazione**
- Push su `main` → sito aggiornato su `https://<username>.github.io` senza interventi manuali
- Il README basta a far partire il progetto su una macchina pulita

---

### Fase 1 – Sito statico minimo ma completo

Obiettivo: sito presentabile e linkabile da LinkedIn.

**Task**
- [ ] Modelli pydantic e loader in `sitegen/` per tutte le collection
- [ ] Popolare `content/` con i dati dell'**Appendice A** (lingua dei contenuti: inglese)
- [ ] Test pytest: tutti i contenuti si caricano e validano; un file volutamente errato fa fallire la validazione
- [ ] Template base: header con navigazione, footer, dark/light mode (rispetta `prefers-color-scheme` + toggle in `theme.js`)
- [ ] **Home**: headline, 2–3 righe di presentazione, servizi freelance, call to action contatti
- [ ] **Experience**: timeline compatta generata dai contenuti (ordine cronologico inverso)
- [ ] **Education**: lauree, summer school, certificati
- [ ] **Projects & Publications**
- [ ] **Contact**: email, LinkedIn, GitHub. **Niente numeri di telefono.** Modulo opzionale via servizio gratuito (es. Formspree) `[DA DECIDERE]`
- [ ] CV scaricabile in PDF
- [ ] Rimuovere il `noindex` del placeholder da `base.html`
- [ ] SEO (`seo.py`): `<title>`, meta description, Open Graph e Twitter card (immagine di anteprima), `sitemap.xml`, `robots.txt`
- [ ] Pagina 404 (`404.html`, supportata nativamente da GitHub Pages)

**Criteri di accettazione**
- Responsive verificato a 360px, 768px, 1280px; nessuno scroll orizzontale
- Lighthouse ≥ 90 su Performance, Accessibility, Best Practices, SEO
- Nessun testo di contenuto hard-coded nei template (tutto da `content/`)
- `pytest` verde, eseguito anche nel workflow prima del deploy
- Anteprima corretta incollando l'URL su LinkedIn

---

### Fase 2 – Interattività sulle esperienze

**Vincolo importante:** l'hover non esiste su touch. L'interazione principale è **click/tap**; l'hover è solo un miglioramento progressivo su desktop.

**Approccio:** progressive enhancement. L'HTML generato da Python deve funzionare **senza JavaScript**; il JS aggiunge solo comodità.

**Task**
- [ ] **Card espandibili**: basate su `<details>/<summary>` (funzionano senza JS). Stato chiuso = summary + highlights; stato aperto = corpo Markdown completo
  - Desktop: hover evidenzia la card (solo CSS)
  - Accessibile da tastiera; animazioni disattivate con `prefers-reduced-motion`
- [ ] **Filtro per skill e settore** (`filters.js`): chip cliccabili; le esperienze non pertinenti si attenuano (non spariscono). Stato del filtro nell'URL (`?skill=python`) per poterlo condividere
  - Python scrive le skill di ogni card come attributo `data-skills="python aws docker"`, così il JS si limita a leggere attributi e cambiare classi CSS
- [ ] **Pagine case study** per le esperienze `featured: true` (`/projects/<id>/`), generate da Python
- [ ] *(Opzionale)* Visualizzazione skill ↔ esperienze (heatmap o network): Python esporta i dati in un JSON statico, la pagina lo disegna con Observable Plot/D3 da CDN

**Case study suggeriti**: wind power forecasting probabilistico; ottimizzazione Polars (−99% tempo); motore matematico SuperEnalotto; API real-time Coppa Italia/Supercoppa.

**Criteri di accettazione**
- Contenuti leggibili anche con JS disabilitato
- Tutto utilizzabile da touch e da tastiera
- Nessun peggioramento di Lighthouse rispetto alla Fase 1
- JS scritto a mano < 200 righe totali, commentato

**Nota contenuti:** nei dettagli lunghi descrivere l'approccio, mai dati o informazioni riservate dei clienti.

---

### Fase 3 – Rifiniture (trasversale, si può fare a pezzi)

- [ ] **i18n IT/EN**: `/` in inglese, `/it/` in italiano. Contenuti tradotti come file paralleli (es. `mathsport.en.md`, `mathsport.it.md`) o campi per lingua nel frontmatter `[DA DECIDERE]`; stringhe di interfaccia in `content/i18n.yaml`. Il loader deve supportarlo, quindi va previsto già nei modelli della Fase 1
- [ ] **Analytics senza cookie** (es. GoatCounter) `[DA DECIDERE]`
- [ ] Audit accessibilità (contrasti, alt text, focus visibile)
- [ ] Controllo link rotti in CI
- [ ] *(Opzionale)* Sezione blog/note tecniche come nuova collection

---

### Fase 4 – Chatbot "Ask about Lorenzo"

GitHub Pages è statico: il backend sta **altrove**. La API key dell'LLM sta **solo** nel backend.

```
Sito (GitHub Pages) ──fetch──▶ API FastAPI (free tier) ──▶ LLM API
                                     ▲
                   knowledge base generata da content/ tramite sitegen.content
```

**Backend (`/backend`)**
- [ ] FastAPI, endpoint `POST /chat` (input: messaggio + breve storico; output: risposta + fonti)
- [ ] Build della knowledge base riusando `sitegen.content.load_all()`: un chunk per esperienza/sezione, con metadati `id`, `type`, `url` della pagina sul sito
- [ ] **Step A – semplice**: tutta la KB nel system prompt (il corpus è piccolo)
- [ ] **Step B – RAG vetrina**: embeddings precalcolati salvati in file (`.npy`/`.json`, niente DB vettoriale), retrieval top-k con similarità coseno (numpy), risposta con **citazione delle fonti** (link alla sezione del sito)
- [ ] System prompt: risponde solo su Lorenzo e la sua attività; se non sa, lo dice e suggerisce il contatto email; non inventa
- [ ] Sicurezza: CORS limitato a `https://<username>.github.io`, rate limiting per IP, lunghezza massima input, timeout, tetto di spesa impostato sull'account del provider LLM
- [ ] Hosting `[DA DECIDERE]`: Render, Hugging Face Spaces o Google Cloud Run (verificare i limiti attuali dei free tier)
- [ ] Provider/modello LLM `[DA DECIDERE]`: modello piccolo ed economico
- [ ] Test (pytest) su chunking, retrieval e endpoint

**Frontend**
- [ ] Widget chat leggero in JS vanilla (bottone flottante → pannello), caricato solo al primo click
- [ ] Gestione cold start (messaggio "sto svegliando il server…") e fallback: se il backend non risponde, mostra il contatto email
- [ ] Disclaimer breve: risposte generate da AI

**Automazione**
- [ ] GitHub Action: a ogni modifica di `content/**` ricostruisce gli embeddings e ridistribuisce il backend

**Criteri di accettazione**
- Nessuna chiave nel repo né nel frontend
- Risposte corrette e con fonti su un set di 15–20 domande di prova (es. "Ha esperienza con Kubernetes?", "Cosa ha fatto in ambito energia?", "Ha pubblicazioni?")
- Il sito funziona normalmente anche con backend offline

---

## 6. Linee guida di design

- Stile pulito, professionale, con un tocco "data": tipografia leggibile, molto spazio bianco, un colore d'accento
- Coerenza con il CV attuale (blu/indaco come accento) `[DA DECIDERE]`
- Mobile first
- Niente stock photo; solo foto profilo ed eventuali grafici reali
- Ogni pagina deve rispondere in 5 secondi a: *chi è, cosa fa, come contattarlo*

---

## Appendice A – Contenuti iniziali (dal CV)

Usare come fonte per popolare `content/`. I testi lunghi dei dettagli li scriverò io: inserire per ora un placeholder `<!-- TODO: dettaglio esteso -->` nel corpo di ogni esperienza.

### Profilo
- **Nome**: Lorenzo Dusty Costa
- **Headline**: Freelance Data Scientist & Backend Developer
- **Sede**: Milan area, Italy
- **Email**: lorenzodusty.costa@gmail.com
- **Link**: LinkedIn, GitHub `[DA DECIDERE: URL]`
- **Summary**: Data Scientist with 10+ years of experience and a strong academic background in mathematics. Started developing mathematical models for lottery and betting at Sisal, then expanded into data science consulting, backend development and cloud infrastructure. Over the past 5 years worked for two football-industry startups on end-to-end data solutions, from predictive modeling to cloud deployment. Interested in sport-tech, energy, healthcare, real estate, tourism and aerospace, with an ambition to apply AI for ethical and sustainable impact.
- **Lingue**: Italian, English, Turkish

### Esperienze

1. **Freelance Data Scientist** — 05/2025 – present — sectors: energy, sport-tech
   - Built an end-to-end day-ahead probabilistic wind power forecasting pipeline, from data ingestion to inference and evaluation (renewable energy).
   - Optimized KPI computation pipelines in Python with Polars, reducing processing time by 99% (sport-tech).
   - Refactored a business-critical Java API, DB and Python components to integrate a new client's data provider (sport-tech).
   - skills: python, polars, java, forecasting, probabilistic-modeling, sql

2. **Lead Data Scientist @ Wallabies** — 11/2023 – 04/2025 — sport-tech
   - Improved football match outcome prediction accuracy by 3–8% through model optimization and feature engineering.
   - Supported multiple Serie A clubs in data-driven scouting with custom KPIs and automated analysis pipelines, reducing manual workload by up to 70%.
   - skills: python, machine-learning, feature-engineering, sports-analytics

3. **Data Scientist & Analytics Manager @ Math&Sport** — 01/2020 – 10/2023 — sport-tech
   - Designed and implemented data components for a real-time tracking system for Serie A coaching staff (tactical and physical insights).
   - Led development of APIs delivering real-time data for the 2020 and 2021 Coppa Italia and Supercoppa finals for broadcasters.
   - Managed DevOps: microservices on cloud, automation workflows, monitoring; reduced team weekend operational workload by over 50%.
   - Coordinated cross-functional teams of data scientists and developers; supervised two master's theses; published one peer-reviewed article.
   - skills: python, api-design, aws, docker, kubernetes, gitlab-ci, devops, team-leadership

4. **Data Scientist @ Spindox** — 09/2018 – 12/2019 — consulting (telco, retail)
   - Anomaly detection system for telco time series based on Seasonal Hybrid ESD (Python, R).
   - Model-based random forest (R, mobForest) for a smart booking platform; contributed to a 15% reduction in no-shows.
   - skills: python, r, time-series, anomaly-detection, random-forest

5. **Game Designer @ Sisal** — 01/2014 – 08/2018 — gaming
   - End-to-end betting model project: automated data collection via web scraping, mathematical models (Poisson, Markov chains), implementation in MATLAB and VBA.
   - Designed the mathematics of lottery games for Italian and international markets (probability, combinatorics, Monte Carlo) with MATLAB and R.
   - Worked on the revision of SuperEnalotto's mathematical engine (game mechanics, prize distribution); the new formula launched in 2016 contributed to 6 of the 10 largest jackpots ever awarded.
   - skills: probability, combinatorics, monte-carlo, matlab, r, vba, web-scraping

### Formazione
- **MSc in Mathematics** — Università degli Studi di Milano — 2011–2013 — 110/110 cum laude
- **BSc in Mathematics** — Università degli Studi di Milano — 2007–2011
- **Summer School in Industrial Mathematics** — ECMI — 07/2011

### Certificati
- Intro to SQL & Advanced SQL — Kaggle — 2023
- Machine Learning — Coursera — 2018
- Business Data Analysis — Talent Garden — 2017

### Pubblicazioni
- *Using Temporal Convolutional Networks to estimate ball possession in soccer games* — Expert Systems with Applications (Elsevier), 8 March 2023 — co-authors: Matteo Borghesi, Lia Morra, Fabrizio Lamberti

### Progetti personali
- **Football tournament management website** — Django, PostgreSQL (Neon), deploy su Render, keep-alive con cron-job.org, HTML/CSS responsive — torneocopamundial.it

### Skill (tassonomia iniziale per `skills.yaml`)
- **Languages**: Python, R, SQL, Java, JavaScript, Bash, MATLAB, VBA
- **Data/ML**: machine learning, time series, forecasting, probabilistic modeling, anomaly detection, Monte Carlo, Polars, deep learning (TCN)
- **Databases**: PostgreSQL, MongoDB, Redis, Elasticsearch
- **Cloud/DevOps**: AWS (EC2, S3, IAM), GCP, Docker, Kubernetes, GitLab CI/CD, Git, Linux
- **Domains**: sports analytics, energy, gaming/lottery, telco, retail

---

## Stato avanzamento

| Fase | Stato | Note |
|---|---|---|
| 0 – Setup | 🟡 in verifica | Struttura, build/serve, test, workflow pronti in locale. Manca: repo GitHub `lorenzodustycosta.github.io`, push e attivazione Pages (source: GitHub Actions) |
| 1 – Sito statico | ⬜ | |
| 2 – Interattività | ⬜ | |
| 3 – Rifiniture | ⬜ | |
| 4 – Chatbot | ⬜ | |
