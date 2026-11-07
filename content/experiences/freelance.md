---
id: freelance
role: Freelance Data Scientist
start: 2025-05
end: present
sectors: [energy, sport-tech]
type: freelance
summary: >-
  Forecasting, data pipelines and backend development for clients in renewable
  energy and sport-tech.
highlights:
  - text: Built an end-to-end probabilistic forecasting pipeline for wind power production
    featured: true
    title: Probabilistic day-ahead forecasting of wind power production
    image: img/projects/wind-forecast.webp
    image_alt: "Time series chart over three days of wind power as a share of installed capacity: the model's day-ahead forecast with its P10–P90 band, compared with actual production"
    image_caption: Day-ahead forecast with P10–P90 band vs. actual production, hourly resolution
    metrics:
      - label: nMAE, quarter-hour P50 (share of installed capacity)
        value: "~10%"
    skills: [python, xgboost, quantile-regression, forecasting, probabilistic-modeling, feature-engineering, gcp, bigquery, cloud-run, cloud-scheduler, cloud-storage, docker]
    tag: renewable energy
    context: >-
      The client needed a proof of concept to test the feasibility of a
      probabilistic forecasting model for the energy produced by 5 wind plants,
      based on weather forecasts and historical production data. I managed the
      whole project independently on the technical side, on a GCP cloud
      environment provided by the client.
    details:
      - Developed the production data ingestion scripts and scheduled the ingestion of weather forecasts from several providers
      - Set up BigQuery tables and backup queries
      - Feature engineering with Python and BigQuery
      - Trained an XGBoost quantile model per plant with the pinball loss, applying conformalized quantile regression (CQR) to correct the P10 and P90 bounds
      - Modeled different market formats and auction types for the day-ahead market, at hourly and quarter-hour resolution
      - Performance similar to two commercial production forecast providers (nMAE ~10% of installed capacity on quarter-hour P50 forecasts) and in line with industry standards, despite a short and seasonally biased test period (summer)
      - Handed the PoC over to the client's internal team
  - text: Optimized KPI computation pipelines
    skills: [python, polars]
    tag: sport-tech
    metrics:
      - label: KPI reprocessing time
        value: "-99%"
    context: >-
      The client works on tracking and event data analysis for football
      matches. To build a post-match analysis platform, they needed to improve
      their existing framework, which reprocessed the whole match frame by
      frame and took over 90 minutes.
    details:
      - Developed, together with the client's team, a framework that reprocesses a full match in a few seconds
      - Used batch and parallel processing
      - Optimized the pass-related KPIs
  - text: Refactored several microservices to integrate a new data provider
    skills: [java, python, postgresql]
    tag: sport-tech
    context: >-
      The client had to rework some business-critical microservices because
      of a change of data provider that had to reach production quickly.
      Within the planned timeline, I refactored the Java and Python components
      and the underlying PostgreSQL database structure, keeping the code and
      data model compatible with the previous provider.
    details:
      - Developed the Java client for the API calls
      - Mapped the outputs of the two providers
      - Rebuilt the objects saved to the database
      - Revised the PostgreSQL tables to distinguish between providers
      - Adapted the Python components that read the PostgreSQL tables
featured: true
---
