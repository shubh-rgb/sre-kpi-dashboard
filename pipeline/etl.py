import csv
import os
import time
from datetime import datetime
from pathlib import Path

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
)
from sqlalchemy.orm import sessionmaker

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "governance")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")
TABLE_NAME = os.getenv("TABLE_NAME", "sre_kpis")
SAMPLE_CSV_PATH = Path(os.getenv("SAMPLE_CSV_PATH", "sample_kpis.csv"))

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

metadata = MetaData()

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
    if not value:
        raise ValueError("Empty datetime")

    text_value = value.strip()
    if text_value.endswith("Z"):
        text_value = text_value[:-1] + "+00:00"
    return datetime.fromisoformat(text_value)


def normalize_value(value: str, column_type):
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


def build_table(columns):
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

    return Table(TABLE_NAME, metadata, *table_columns, schema=DB_SCHEMA)


def wait_for_postgres(engine, retries=15, delay=3):
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
    if DB_SCHEMA and DB_SCHEMA != "public":
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))
            print(f"Created schema '{DB_SCHEMA}' if not exists.")


def load_csv_rows(path: Path):
    if not path.exists():
        return []

    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = [row for row in reader]
    print(f"Loaded {len(rows)} rows from {path}")
    return rows


def build_columns_from_rows(rows):
    if not rows:
        return {}

    columns = {}
    first_row = rows[0]
    for name, value in first_row.items():
        columns[name.strip()] = infer_type(value)
    return columns


def prepare_rows(rows, columns):
    results = []
    for row in rows:
        record = {}
        for name, column_type in columns.items():
            raw_value = row.get(name, None)
            record[name] = normalize_value(raw_value, column_type)
        results.append(record)
    return results


def insert_rows(session, table, rows):
    if not rows:
        print("No rows to insert.")
        return
    session.execute(table.insert(), rows)
    session.commit()
    print(f"Inserted {len(rows)} rows into {DB_SCHEMA}.{TABLE_NAME}.")


def generate_fallback_rows():
    rows = []
    for sample in DEFAULT_SAMPLE_ROWS:
        record = {
            key: normalize_value(str(value), infer_type(str(value)))
            for key, value in sample.items()
        }
        rows.append(record)
    return rows


def main():
    print("Connecting to PostgreSQL at %s" % DATABASE_URL)
    engine = create_engine(DATABASE_URL, echo=False)

    wait_for_postgres(engine)
    create_schema(engine)

    csv_rows = load_csv_rows(SAMPLE_CSV_PATH)
    if csv_rows:
        columns = build_columns_from_rows(csv_rows)
        table = build_table(columns)
        metadata.create_all(engine)
        prepared_rows = prepare_rows(csv_rows, columns)
    else:
        print(f"CSV not found at {SAMPLE_CSV_PATH}; using built-in sample rows.")
        columns = build_columns_from_rows([DEFAULT_SAMPLE_ROWS[0]])
        table = build_table(columns)
        metadata.create_all(engine)
        prepared_rows = generate_fallback_rows()

    Session = sessionmaker(bind=engine)
    with Session() as session:
        insert_rows(session, table, prepared_rows)

    print("ETL pipeline finished.")


if __name__ == "__main__":
    main()
