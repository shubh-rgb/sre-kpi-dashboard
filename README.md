# SRE KPI Dashboard with Retail Analytics & Dynamic Dashboard Generation

This repository contains a local stack for building multi-purpose dashboards using:

- **PostgreSQL** as the data storage backend
- **Grafana** for visualization
- **Python ETL pipeline** to ingest KPI and retail data into PostgreSQL
- **🆕 Automatic Dashboard Generation** from CSV files
- **🆕 Freshservice API Integration** for support metrics

## 🚀 Quick Start

### 1. Run Setup
```bash
bash setup.sh
```

### 2. Start the Stack
```bash
docker-compose up --build
```

### 3. Access Grafana
- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: admin

### 4. Add Custom Data
Simply drop a CSV file in `pipeline/documents/` and the system will:
- ✅ Create a database table automatically
- ✅ Generate a Grafana dashboard
- ✅ Start visualizing your data

Example:
```bash
cp my_analysis.csv pipeline/documents/
docker-compose restart pipeline
```

## 📊 What's New (Enhanced Version)

### ✨ Automatic Dashboard Generation
- Drop any CSV in `pipeline/documents/`
- Instant database table creation
- Auto-generated Grafana dashboards with:
  - Data tables
  - Metric gauges
  - Time series charts
  - Automatic data type detection

### 🔌 Freshservice Integration (Optional)
Connect to your Freshservice account to visualize:
- Support tickets
- Incidents
- Problems
- Change requests

[See full feature guide →](FEATURES.md)

## Running as a Normal User

1. Add your user to the docker group:
   ```bash
   sudo usermod -aG docker $USER
   ```

2. Log out and log back in (or reboot) for the change to take effect.

3. Run docker-compose commands as your normal user:
   ```bash
   docker-compose up
   ```

## 📋 Available Dashboards

### Pre-configured Dashboards
1. **SRE KPI Dashboard** (`sre_kpi_dashboard.json`) - Service reliability metrics
2. **Retail Sales Dashboard** (`retail_sales_dashboard.json`) - Daily sales trends, revenue analysis, conversion rates
3. **Retail Products Dashboard** (`retail_products_dashboard.json`) - Product catalog, inventory levels, stock analysis

### Auto-Generated Dashboards
Any CSV in `pipeline/documents/` gets its own dashboard:
- **System Metrics Dashboard** (example: `example_system_metrics.csv`)
- **Regional Sales Dashboard** (example: `example_regional_sales.csv`)
- **Your Custom Dashboards** (add more CSVs!)

## 📁 Sample Data

Sample CSV files are provided in the `pipeline/` directory:

- `sample_kpis.csv` — SRE KPI data
- `retail_sales.csv` — Daily retail sales metrics
- `retail_products.csv` — Product catalog
- `retail_orders.csv` — Order transactions
- `documents/example_system_metrics.csv` — CPU/Memory metrics example
- `documents/example_regional_sales.csv` — Regional sales example

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
