# Enhanced SRE KPI Dashboard with Dynamic CSV Processing

## Overview

This enhanced version adds powerful features for dynamic dashboard generation, CSV data processing, and Freshservice API integration.

## 🆕 New Features

### 1. **Automatic Dashboard Generation**
- Dashboards are automatically generated for each CSV file
- Includes:
  - Table panels showing recent records
  - Stat panels for numeric metrics
  - Time series charts for temporal data
  - Auto-discovery of data types (integers, floats, timestamps)

### 2. **Document Folder Processing**
Drop any CSV file in `pipeline/documents/` folder and the system will:
- ✅ Automatically create a database table
- ✅ Load the data into PostgreSQL
- ✅ Generate a Grafana dashboard
- ✅ Make it available for visualization immediately

### 3. **Multiple Dashboard Support**
Create unlimited dashboards based on your CSV data:
- Each CSV generates a unique dashboard
- Dashboards are tagged and organized in Grafana
- Support for different data types and structures

### 4. **Freshservice API Integration**
Fetch data directly from Freshservice:
- Fetch tickets, incidents, problems, and changes
- Automatically store in PostgreSQL
- Generate dashboards for support metrics

## 📁 File Structure

```
pipeline/
├── etl_enhanced.py           # Main ETL pipeline (new)
├── dashboard_generator.py    # Dashboard JSON generator (new)
├── freshservice_sync.py      # Freshservice API client (new)
├── documents/                # Drop your CSVs here (new)
│   └── (your CSV files)
├── etl.py                    # Original pipeline (kept for reference)
├── requirements.txt          # Updated dependencies
├── sample_kpis.csv          # Sample SRE data
├── retail_orders.csv        # Sample retail data
├── retail_products.csv      # Sample retail data
├── retail_sales.csv         # Sample retail data
└── Dockerfile
```

## 🚀 Quick Start

### 1. Start the Stack

```bash
docker-compose up --build
```

### 2. Access Grafana

- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: admin

### 3. View Auto-Generated Dashboards

All dashboards generated from:
- Sample SRE KPIs
- Retail data (orders, products, sales)
- Any CSVs you drop in `pipeline/documents/`

## 📊 Creating Custom Dashboards

### Option A: Drop CSV in Documents Folder

1. Prepare your CSV file with headers
   ```csv
   date,revenue,customers,region
   2026-01-01,50000,150,North
   2026-01-02,55000,160,North
   ```

2. Copy to documents folder:
   ```bash
   cp my_data.csv pipeline/documents/
   ```

3. Run the pipeline:
   ```bash
   docker-compose up
   ```

4. Grafana automatically creates a dashboard at:
   - Dashboard name: `My Data Dashboard`
   - Table with all records
   - Average metrics for numeric columns
   - Time series charts for temporal data

### Option B: Programmatic Dashboard Creation

Use the `dashboard_generator.py` to create dashboards:

```python
from dashboard_generator import generate_dashboard_json, save_dashboard_json

columns = {
    'timestamp': 'TIMESTAMP',
    'cpu_usage': 'Float',
    'memory_usage': 'Float',
    'service_name': 'String'
}

rows = [
    {'timestamp': '2026-01-01T00:00:00Z', 'cpu_usage': 45.2, 'memory_usage': 72.1, 'service_name': 'api-server'},
    # ... more rows
]

dashboard = generate_dashboard_json('system_metrics', columns, rows)
save_dashboard_json(dashboard, 'system_metrics_dashboard.json')
```

## 🔌 Freshservice Integration

### Setup

Set environment variables in `docker-compose.yml`:

```yaml
environment:
  LOAD_FRESHSERVICE_DATA: "true"
  FRESHSERVICE_API_KEY: "your-api-key-here"
  FRESHSERVICE_DOMAIN: "your-domain"
```

### Features

Once enabled, the pipeline will fetch:
- **Tickets**: Support tickets with status, priority, timestamps
- **Incidents**: Service incidents with metadata
- **Problems**: Known issues and root causes
- **Changes**: Change request records

Data is automatically:
1. Stored in `freshservice_data` table
2. Visualized in a dedicated Grafana dashboard
3. Updated on each pipeline run

### Data Available

| Field | Type | Description |
|-------|------|-------------|
| id | String | Record ID |
| type | String | ticket, incident, problem, or change |
| subject | String | Title/Subject |
| status | Integer | Current status |
| priority | Integer | Priority level (1-4) |
| created_at | Timestamp | Creation timestamp |
| updated_at | Timestamp | Last update time |
| resolved_at | Timestamp | Resolution time (if applicable) |

## 🔧 Configuration

### Environment Variables

```yaml
# Database
DB_HOST: postgres
DB_PORT: 5432
DB_NAME: governance
DB_USER: postgres
DB_PASSWORD: admin
DB_SCHEMA: public

# SRE KPI Settings
TABLE_NAME: sre_kpis
SAMPLE_CSV_PATH: sample_kpis.csv

# Feature Flags
LOAD_RETAIL_DATA: "true"           # Load sample retail data
AUTO_GENERATE_DASHBOARDS: "true"   # Generate dashboards automatically
LOAD_FRESHSERVICE_DATA: "false"    # Fetch from Freshservice API

# Freshservice Settings
FRESHSERVICE_API_KEY: ""           # Your Freshservice API key
FRESHSERVICE_DOMAIN: ""            # Your Freshservice domain
```

## 📈 Available Dashboards

### Pre-configured Dashboards

1. **SRE KPI Dashboard** (`sre_kpi_dashboard.json`)
   - Service reliability metrics
   - Error rates, latency, availability
   - Status indicators

2. **Retail Sales Dashboard** (`retail_sales_dashboard.json`)
   - Daily sales trends
   - Revenue analysis
   - Conversion rates

3. **Retail Products Dashboard** (`retail_products_dashboard.json`)
   - Product catalog
   - Inventory levels
   - Stock analysis

### Auto-Generated Dashboards

For each CSV in `documents/` folder:
- Dashboard name: `{table_name} Dashboard`
- Includes data tables, metrics, and charts
- Located in Grafana's "auto-generated" tag

## 🗄️ Database Schema

Tables are created automatically with:
- Auto-incrementing `id` primary key
- Columns inferred from CSV headers
- Type inference for integers, floats, timestamps, and strings
- Nullable columns for missing data

Example generated table:

```sql
CREATE TABLE public.my_data (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP,
    revenue FLOAT,
    customers INTEGER,
    region VARCHAR(255)
);
```

## 🔍 Data Type Inference

The system automatically detects:

| Sample Value | Detected Type |
|--------------|---------------|
| `45` | Integer |
| `45.5` | Float |
| `2026-01-01T00:00:00Z` | TIMESTAMP |
| `hello` | String(255) |

## 📝 Sample CSV Format

```csv
timestamp,metric_name,value,status,service
2026-05-27T13:00:00Z,error_rate,0.72,ok,auth-service
2026-05-27T14:00:00Z,error_rate,0.65,ok,auth-service
2026-05-27T13:00:00Z,latency_ms,185,warning,payment-service
```

## 🚨 Troubleshooting

### Dashboard Not Appearing

1. Check logs:
   ```bash
   docker-compose logs pipeline
   ```

2. Verify CSV is in `pipeline/documents/`

3. Check table was created:
   ```bash
   docker exec governance-postgres psql -U postgres -d governance -c "\dt"
   ```

### Data Not Loading

1. Validate CSV format (headers required)
2. Ensure CSV has data rows
3. Check file permissions
4. Review PostgreSQL logs:
   ```bash
   docker exec governance-postgres psql -U postgres -d governance -c "SELECT * FROM your_table LIMIT 5;"
   ```

### Freshservice Data Not Syncing

1. Verify API credentials in docker-compose.yml
2. Check API key has proper permissions
3. Verify network access to Freshservice
4. Review logs for API errors

## 🔐 Security Notes

### Current Setup (Development)

⚠️ **WARNING**: Default credentials are hardcoded. For development only.

```yaml
GF_SECURITY_ADMIN_USER: admin
GF_SECURITY_ADMIN_PASSWORD: admin
POSTGRES_PASSWORD: admin
```

### Production Recommendations

1. Use environment files with secrets:
   ```bash
   docker-compose --env-file .env up
   ```

2. Use Docker secrets or HashiCorp Vault

3. Rotate credentials regularly

4. Restrict network access

5. Enable SSL/TLS for API connections

## 📚 API Reference

### FreshserviceClient

```python
from freshservice_sync import FreshserviceClient

client = FreshserviceClient(api_key, domain)

# Get tickets
tickets = client.get_tickets(page=1, per_page=100)

# Get incidents
incidents = client.get_incidents(page=1, per_page=100)

# Get problems
problems = client.get_problems(page=1, per_page=100)

# Get changes
changes = client.get_changes(page=1, per_page=100)
```

### Dashboard Generator

```python
from dashboard_generator import generate_dashboard_json

dashboard = generate_dashboard_json(
    table_name='my_table',
    columns={'col1': 'Float', 'col2': 'String'},
    rows=[{'col1': 1.5, 'col2': 'value'}]
)
```

## 🔄 Workflow Example

1. **Prepare Data**
   ```bash
   # Create sample_metrics.csv
   timestamp,cpu,memory,disk
   2026-01-01T00:00:00Z,45.2,72.1,82.3
   2026-01-01T01:00:00Z,48.5,75.2,83.1
   ```

2. **Upload to Documents**
   ```bash
   cp sample_metrics.csv pipeline/documents/
   ```

3. **Run Pipeline**
   ```bash
   docker-compose up --build
   ```

4. **View in Grafana**
   - Navigate to http://localhost:3000
   - Find "Sample Metrics Dashboard"
   - View table, metrics, and time series

## 📞 Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify CSV format
3. Ensure database connectivity
4. Review environment variables

## 📄 License

Same as parent project

