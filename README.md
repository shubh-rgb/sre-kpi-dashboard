# SRE KPI Dashboard

This repository contains a local stack for building an SRE KPI dashboard using:

- **PostgreSQL** as the KPI storage backend
- **Grafana** for visualization
- **Python ETL pipeline** to ingest KPI CSV data into PostgreSQL

## Getting started

1. Start the stack:

```bash
sudo docker-compose up --build
```

2. Grafana is available at `http://localhost:3000`.
   - Default credentials: `admin` / `admin`

3. PostgreSQL is available at `localhost:5432`.
   - Database: `governance`
   - User: `postgres`
   - Password: `admin`

## Sample data

A sample CSV file is provided in `pipeline/sample_kpis.csv`.
The pipeline reads that CSV on startup and inserts rows into `sre_kpis`.

## Pipeline

The pipeline service runs `pipeline/etl.py`, waits for PostgreSQL, creates the target schema and table dynamically, and loads KPI rows from `pipeline/sample_kpis.csv`.

You can change the ingestion target by overriding these environment variables in `docker-compose.yml`:

- `DB_SCHEMA` — Postgres schema name
- `TABLE_NAME` — target table name
- `SAMPLE_CSV_PATH` — CSV file path inside `pipeline/`

## Grafana provisioning

Grafana auto-provisions:

- a PostgreSQL datasource from `grafana/provisioning/datasources/datasource.yml`
- a dashboard from `grafana/provisioning/dashboards/sre_kpi_dashboard.json`

Open `http://localhost:3000` and browse the `SRE KPI Dashboard`.
