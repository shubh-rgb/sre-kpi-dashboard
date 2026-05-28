# SRE KPI Dashboard with Retail Analytics

This repository contains a local stack for building multi-purpose dashboards using:

- **PostgreSQL** as the data storage backend
- **Grafana** for visualization
- **Python ETL pipeline** to ingest KPI and retail data into PostgreSQL

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

## Running as a Normal User

1. Add your user to the docker group:
   sudo usermod -aG docker $USER

2. Log out and log back in (or reboot) for the change to take effect.

3. Run docker-compose commands as your normal user:
   docker-compose up

## Available Dashboards

Three pre-configured dashboards are automatically provisioned:

1. **SRE KPI Dashboard** (`sre_kpi_dashboard.json`) - Service reliability metrics
2. **Retail Sales Dashboard** (`retail_sales_dashboard.json`) - Daily sales trends, revenue analysis, conversion rates
3. **Retail Products Dashboard** (`retail_products_dashboard.json`) - Product catalog, inventory levels, stock analysis

## Sample data

Sample CSV files are provided in the `pipeline/` directory:

- `sample_kpis.csv` — SRE KPI data
- `retail_sales.csv` — Daily retail sales metrics
- `retail_products.csv` — Product catalog
- `retail_orders.csv` — Order transactions

## Pipeline

The pipeline service runs `pipeline/etl.py`, which:

1. Waits for PostgreSQL to be available
2. Creates tables dynamically based on CSV schema
3. Loads SRE KPI data from `sample_kpis.csv`
4. Loads retail data from retail_*.csv files (if `LOAD_RETAIL_DATA` is enabled)

### Pipeline Configuration

You can customize the pipeline by overriding these environment variables in `docker-compose.yml`:

- `DB_SCHEMA` — Postgres schema name (default: `public`)
- `TABLE_NAME` — target table name for SRE KPIs (default: `sre_kpis`)
- `SAMPLE_CSV_PATH` — CSV file path for SRE KPIs (default: `sample_kpis.csv`)
- `LOAD_RETAIL_DATA` — enable/disable retail data loading (default: `true`)

## Grafana provisioning

Grafana auto-provisions:

- a PostgreSQL datasource from `grafana/provisioning/datasources/datasource.yml`
- all dashboards from `grafana/provisioning/dashboards/*.json`

Open `http://localhost:3000` and browse the available dashboards.
