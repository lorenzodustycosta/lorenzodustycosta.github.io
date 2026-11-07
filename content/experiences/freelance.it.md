---
id: freelance
role: Data Scientist freelance
start: 2025-05
end: present
sectors: [energy, sport-tech]
type: freelance
summary: >-
  Forecasting, data pipeline e sviluppo backend per clienti nei settori delle
  energie rinnovabili e dello sport-tech.
highlights:
  - text: Sviluppo di una pipeline end-to-end di forecasting probabilistica per la produzione eolica
    featured: true
    title: Forecasting probabilistico per il day-ahead della produzione eolica
    image: img/projects/wind-forecast.webp
    image_alt: "Grafico di una serie temporale su tre giorni della produzione eolica come quota della capacità installata: la previsione day-ahead del modello con la sua banda P10–P90, confrontata con la produzione effettiva"
    image_caption: Previsione per il day-ahead con banda P10–P90 vs. produzione effettiva, risoluzione oraria
    metrics:
      - label: nMAE, P50 al quarto d'ora (quota della capacità installata)
        value: "~10%"
    skills: [python, xgboost, quantile-regression, forecasting, probabilistic-modeling, feature-engineering, gcp, bigquery, cloud-run, cloud-scheduler, cloud-storage, docker]
    tag: energie rinnovabili
    context: >-
      Il cliente aveva bisogno di un proof of concept per verificare la
      fattibilità di un modello di forecasting probabilistico dell'energia
      prodotta da 5 impianti eolici, a partire da previsioni meteo e dati
      storici di produzione. L'intero progetto è stato gestito in autonomia
      sul fronte tecnico, su un ambiente cloud GCP fornito dal cliente.
    details:
      - Sviluppo degli script di ingestione dei dati di produzione e schedulazione dell'ingestione delle previsioni meteo da diversi provider
      - Configurazione delle tabelle BigQuery e delle query di backup
      - Feature engineering con Python e BigQuery
      - Addestramento di un modello XGBoost a quantili per ciascun impianto, con pinball loss, e applicazione della conformalized quantile regression (CQR) per correggere i limiti P10 e P90
      - Modellazione di diversi formati di mercato e tipi di asta per il mercato day-ahead, a risoluzione oraria e al quarto d'ora
      - Prestazioni simili a quelle di due provider commerciali di previsioni di produzione (nMAE ~10% della capacità installata sulle previsioni P50 al quarto d'ora) e in linea con gli standard di settore, pur con un periodo di test breve e stagionalmente sbilanciato (estate)
      - Consegna della PoC al team interno del cliente
  - text: Ottimizzazione delle pipeline di calcolo dei KPI
    skills: [python, polars]
    tag: sport-tech
    metrics:
      - label: Tempo di rielaborazione dei KPI
        value: "-99%"
    context: >-
      Il cliente opera nell'analisi di dati di tracking e dati evento per partite di calcio. Per lo sviluppo di una piattaforma di analisi post-match, necessitava di migliorare il framework in uso, che riprocessava l'intera partita frame per frame, impiegando oltre 90 minuti.
    details:
      - Sviluppo, insieme al team del cliente, di un framework che rielabora un'intera partita in pochi secondi
      - Uso di elaborazione batch e parallela
      - Ottimizzazione dei KPI relativi ai passaggi
  - text: Refactoring di alcuni microservizi per integrare un nuovo data provider.
    skills: [java, python, postgresql]
    tag: sport-tech
    context: >-
      Il cliente doveva rivedere alcuni microservizi business-critical in tempi brevi a causa
      di un cambio di data provider da portare in produzione in breve tempo. Rispettando i tempi previsti, sono stati rifattorizzati i componenti Java e Python e la struttura del database PostgreSQL sottostante, mantenendo codice e modello dati compatibili con il provider precedente.
    details:
      - Sviluppo del client Java per le chiamate API
      - Mappatura degli output dei due provider
      - Ricostruzione degli oggetti da salvare a DB
      - Revisione delle tabelle PostgreSQL per distinguere i provider
      - Adattamento dei componenti Python che leggono le tabelle PostgreSQL
featured: true
---
