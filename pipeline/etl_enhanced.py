"""
Enhanced ETL pipeline with CSV monitoring, dynamic dashboards, and Freshservice integration
"""
import csv
import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    TEXT,
    Float,
    Integer,
    String,
    Table,
    Column,
    MetaData,
    create_engine,
    text,
    inspect,
)
from sqlalchemy.orm import sessionmaker

from dashboard_generator import generate_dashboard_json, save_dashboard_json
from freshservice_sync import fetch_freshservice_data, save_freshservice_csv

# Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "governance")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")
TABLE_NAME = os.getenv("TABLE_NAME", "sre_kpis")
SAMPLE_CSV_PATH = Path(os.getenv("SAMPLE_CSV_PATH", "sample_kpis.csv"))
LOAD_RETAIL_DATA = os.getenv("LOAD_RETAIL_DATA", "true").lower() == "true"
LOAD_FRESHSERVICE_DATA = os.getenv("LOAD_FRESHSERVICE_DATA", "false").lower() == "true"
AUTO_GENERATE_DASHBOARDS = os.getenv("AUTO_GENERATE_DASHBOARDS", "true").lower() == "true"

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

metadata = MetaData()
PIPELINE_DIR = Path(__file__).parent
DOCUMENTS_DIR = PIPELINE_DIR / "documents"
DASHBOARDS_DIR = Path("/etc/grafana/provisioning/dashboards") if os.path.exists("/etc/grafana") else PIPELINE_DIR / "dashboards"

# Ensure directories exist
DOCUMENTS_DIR.mkdir(exist_ok=True)
DASHBOARDS_DIR.mkdir(exist_ok=True, parents=True)

DEFAULT_SAMPLE_ROWS = [
    {
        "service_name": "auth-service",
        "metric_name": "error_rate",
        "metric_value": 0.72,
        "collected_at": "2026-05-27T13:00:00Z",
        "status": "ok",
    },
    {
        "service_name": "payment-service",
        "metric_name": "p95_latency_ms",
        "metric_value": 185.0,
        "collected_at": "2026-05-27T13:00:00Z",
        "status": "warning",
    },
    {
        "service_name": "search-service",
        "metric_name": "availability_pct",
        "metric_value": 99.92,
        "collected_at": "2026-05-27T13:00:00Z",
        "status": "ok",
    },
]


def infer_type(value: str):
    """Infer SQL column type from value"""
    if value is None or value == "":
        return String(255)

    value = value.strip()
    if value == "":
        return String(255)

    if value.isdigit():
        return Integer

    try:
        float(value)
        return Float
    except ValueError:
        pass

    if any(key in value.lower() for key in ["z", "t", "date", "time"]):
        try:
            parse_datetime(value)
            return TIMESTAMP
        except ValueError:
            pass

    return String(255)


def parse_datetime(value: str):
    """Parse ISO format datetime"""
    if not value:
        raise ValueError("Empty datetime")

    text_value = value.strip()
    if text_value.endswith("Z"):
        text_value = text_value[:-1] + "+00:00"
    return datetime.fromisoformat(text_value)


def normalize_value(value: str, column_type):
    """Normalize value to correct type"""
    if value is None:
        return None

    raw = value.strip()
    if raw == "":
        return None

    if column_type is Integer:
        return int(raw)
    if column_type is Float:
        return float(raw)
    if column_type is TIMESTAMP:
        return parse_datetime(raw)
    if column_type is JSON:
        return raw

    return raw


def build_table(table_name: str, columns: Dict):
    """Build SQLAlchemy table definition"""
    table_columns = [Column("id", Integer, primary_key=True, autoincrement=True)]
    for name, column_type in columns.items():
        if name == "id":
            continue
        if column_type is TIMESTAMP:
            table_columns.append(Column(name, TIMESTAMP, nullable=True))
        elif column_type is Integer:
            table_columns.append(Column(name, Integer, nullable=True))
        elif column_type is Float:
            table_columns.append(Column(name, Float, nullable=True))
        else:
            table_columns.append(Column(name, String(255), nullable=True))

    return Table(table_name, metadata, *table_columns, schema=DB_SCHEMA)


def wait_for_postgres(engine, retries=15, delay=3):
    """Wait for PostgreSQL to be available"""
    for attempt in range(1, retries + 1):
        try:
            with engine.connect():
                print("Connected to PostgreSQL on attempt %s." % attempt)
                return
        except Exception as exc:
            print(f"Postgres unavailable (attempt {attempt}/{retries}): {exc}")
            time.sleep(delay)
    raise RuntimeError("Unable to connect to PostgreSQL after retries")


def create_schema(engine):
    """Create schema if it doesn't exist"""
    if DB_SCHEMA and DB_SCHEMA != "public":
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))
            print(f"Created schema '{DB_SCHEMA}' if not exists.")


def load_csv_rows(path: Path) -> List[Dict]:
    """Load CSV file into memory"""
    if not path.exists():
        return []

    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [row for row in reader]
    print(f"Loaded {len(rows)} rows from {path}")
    return rows


def build_columns_from_rows(rows: List[Dict]) -> Dict:
    """Infer column types from CSV rows"""
    if not rows:
        return {}

    columns = {}
    first_row = rows[0]
    for name, value in first_row.items():
        columns[name.strip()] = infer_type(value)
    return columns


def prepare_rows(rows: List[Dict], columns: Dict) -> List[Dict]:
    """Normalize row values to correct types"""
    results = []
    for row in rows:
        record = {}
        for name, column_type in columns.items():
            raw_value = row.get(name, None)
            record[name] = normalize_value(raw_value, column_type)
        results.append(record)
    return results


def insert_rows(session, table, rows: List[Dict]):
    """Insert rows into table"""
    if not rows:
        print("No rows to insert.")
        return
    session.execute(table.insert(), rows)
    session.commit()
    print(f"Inserted {len(rows)} rows into {DB_SCHEMA}.{table.name}.")


def table_exists(engine, table_name: str) -> bool:
    """Check if table already exists"""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names(schema=DB_SCHEMA)
    return table_name in existing_tables


def load_and_process_csv(engine, session, table_name: str, csv_path: Path, create_dashboard: bool = True):
    """Load CSV and create table and dashboard"""
    print(f"\n--- Processing CSV: {table_name} ---")
    
    csv_rows = load_csv_rows(csv_path)
    if not csv_rows:
        print(f"No data found in {csv_path}")
        return

    columns = build_columns_from_rows(csv_rows)
    
    # Check if table exists, if so, drop it to allow updates
    if table_exists(engine, table_name):
        print(f"Table {table_name} already exists, updating...")
        with engine.begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{DB_SCHEMA}"."{table_name}" CASCADE'))

    # Create table
    table = build_table(table_name, columns)
    metadata.create_all(engine)
    
    # Insert data
    prepared_rows = prepare_rows(csv_rows, columns)
    insert_rows(session, table, prepared_rows)

    # Generate dashboard
    if create_dashboard and AUTO_GENERATE_DASHBOARDS:
        dashboard = generate_dashboard_json(table_name, columns, prepared_rows)
        dashboard_path = DASHBOARDS_DIR / f"{table_name}_dashboard.json"
        save_dashboard_json(dashboard, str(dashboard_path))
        print(f"Generated dashboard at {dashboard_path}")


def generate_fallback_rows():
    """Generate fallback sample rows"""
    rows = []
    for sample in DEFAULT_SAMPLE_ROWS:
        record = {
            key: normalize_value(str(value), infer_type(str(value)))
            for key, value in sample.items()
        }
        rows.append(record)
    return rows


def load_retail_data(engine, session):
    """Load retail datasets from CSV files"""
    retail_files = {
        "retail_orders": PIPELINE_DIR / "retail_orders.csv",
        "retail_products": PIPELINE_DIR / "retail_products.csv",
        "retail_sales": PIPELINE_DIR / "retail_sales.csv",
    }
    
    for table_name, csv_path in retail_files.items():
        if csv_path.exists():
            load_and_process_csv(engine, session, table_name, csv_path, create_dashboard=True)
        else:
            print(f"Skipping {table_name}: CSV not found at {csv_path}")


def process_documents_folder(engine, session):
    """Process all CSV files in the documents folder"""
    if not DOCUMENTS_DIR.exists():
        return

    csv_files = list(DOCUMENTS_DIR.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in documents folder")
        return

    print(f"\n=== Processing {len(csv_files)} CSV files from documents folder ===")
    
    for csv_file in csv_files:
        # Use filename (without extension) as table name
        table_name = csv_file.stem.lower().replace("-", "_").replace(" ", "_")
        load_and_process_csv(engine, session, table_name, csv_file, create_dashboard=True)


def load_freshservice_data_integration(engine, session):
    """Fetch and load Freshservice data"""
    print("\n=== Loading Freshservice Data ===")
    
    records = fetch_freshservice_data()
    if not records:
        print("No Freshservice data available")
        return

    # Save to CSV in documents folder
    csv_path = DOCUMENTS_DIR / "freshservice_data.csv"
    save_freshservice_csv(records, DOCUMENTS_DIR)

    # Load into database
    load_and_process_csv(engine, session, "freshservice_data", csv_path, create_dashboard=True)


def main():
    """Main ETL pipeline"""
    print("=" * 60)
    print("Enhanced ETL Pipeline with Dynamic Dashboards")
    print("=" * 60)
    print(f"Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    print(f"Schema: {DB_SCHEMA}")
    print(f"Documents Folder: {DOCUMENTS_DIR}")
    print(f"Dashboards Output: {DASHBOARDS_DIR}")
    print("=" * 60)

    engine = create_engine(DATABASE_URL, echo=False)
    wait_for_postgres(engine)
    create_schema(engine)

    Session = sessionmaker(bind=engine)

    # Load SRE KPI data
    print("\n=== Loading SRE KPI Data ===")
    csv_rows = load_csv_rows(SAMPLE_CSV_PATH)
    if csv_rows:
        columns = build_columns_from_rows(csv_rows)
        table = build_table(TABLE_NAME, columns)
        metadata.create_all(engine)
        prepared_rows = prepare_rows(csv_rows, columns)
    else:
        print(f"CSV not found at {SAMPLE_CSV_PATH}; using built-in sample rows.")
        columns = build_columns_from_rows([DEFAULT_SAMPLE_ROWS[0]])
        table = build_table(TABLE_NAME, columns)
        metadata.create_all(engine)
        prepared_rows = generate_fallback_rows()

    with Session() as session:
        insert_rows(session, table, prepared_rows)

        # Generate dashboard for SRE KPIs
        if AUTO_GENERATE_DASHBOARDS:
            dashboard = generate_dashboard_json(TABLE_NAME, columns, prepared_rows)
            dashboard_path = DASHBOARDS_DIR / f"{TABLE_NAME}_dashboard.json"
            save_dashboard_json(dashboard, str(dashboard_path))

    # Load Retail data
    if LOAD_RETAIL_DATA:
        print("\n=== Loading Retail Data ===")
        with Session() as session:
            load_retail_data(engine, session)

    # Process documents folder
    with Session() as session:
        process_documents_folder(engine, session)

    # Load Freshservice data if configured
    if LOAD_FRESHSERVICE_DATA:
        with Session() as session:
            load_freshservice_data_integration(engine, session)

    print("\n" + "=" * 60)
    print("ETL pipeline finished successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
