"""
Streamlined ETL Pipeline with Incremental Data Syncing
- Uses upserts instead of drop/recreate
- Multi-table support
- Data change tracking
"""
import csv
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from db_manager import DatabaseManager, METADATA_TABLE
from dashboard_generator import generate_dashboard_json, save_dashboard_json
from freshservice_sync import fetch_freshservice_data, save_freshservice_csv

# Configuration
AUTO_GENERATE_DASHBOARDS = os.getenv("AUTO_GENERATE_DASHBOARDS", "true").lower() == "true"
LOAD_RETAIL_DATA = os.getenv("LOAD_RETAIL_DATA", "true").lower() == "true"
LOAD_FRESHSERVICE_DATA = os.getenv("LOAD_FRESHSERVICE_DATA", "false").lower() == "true"

PIPELINE_DIR = Path(__file__).parent
DOCUMENTS_DIR = PIPELINE_DIR / "documents"
DASHBOARDS_DIR = Path("/etc/grafana/provisioning/dashboards") if os.path.exists("/etc/grafana") else PIPELINE_DIR / "dashboards"

# Ensure directories exist
DOCUMENTS_DIR.mkdir(exist_ok=True)
DASHBOARDS_DIR.mkdir(exist_ok=True, parents=True)


class ETLPipeline:
    """Handles data loading and transformation"""

    def __init__(self):
        self.db = DatabaseManager()
        self.db.wait_for_connection()
        self.db.ensure_schema()
        self.db.ensure_metadata_table()

    def load_csv_file(self, path: Path) -> List[Dict]:
        """Load CSV file into list of dictionaries"""
        if not path.exists():
            print(f"⚠️  CSV file not found: {path}")
            return []

        try:
            rows = []
            with path.open(newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = [row for row in reader]
            print(f"📥 Loaded {len(rows)} rows from {path.name}")
            return rows
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []

    def normalize_value(self, value: str, col_type):
        """Normalize value to correct Python type"""
        if value is None or value == "":
            return None

        value = str(value).strip()
        if not value:
            return None

        # Try to convert to appropriate type
        try:
            if col_type == int:
                return int(value)
            elif col_type == float:
                return float(value)
        except (ValueError, TypeError):
            pass

        return value

    def infer_column_types(self, rows: List[Dict]) -> Dict[str, type]:
        """Infer Python types from first row"""
        if not rows:
            return {}

        types = {}
        first_row = rows[0]
        
        for col_name, value in first_row.items():
            col_name = col_name.strip()
            
            if not value:
                types[col_name] = str
                continue

            value = str(value).strip()
            
            if value.isdigit():
                types[col_name] = int
            elif self._is_float(value):
                types[col_name] = float
            else:
                types[col_name] = str

        return types

    def _is_float(self, value: str) -> bool:
        """Check if string is a float"""
        try:
            float(value)
            return "." in value
        except ValueError:
            return False

    def normalize_rows(self, rows: List[Dict], col_types: Dict) -> List[Dict]:
        """Normalize all rows to correct types"""
        normalized = []
        for row in rows:
            normalized_row = {}
            for col_name, col_type in col_types.items():
                value = row.get(col_name, None)
                normalized_row[col_name] = self.normalize_value(value, col_type)
            normalized.append(normalized_row)
        return normalized

    def compute_source_hash(self, rows: List[Dict]) -> str:
        """Compute hash of source data for change detection"""
        data_str = str(sorted(str(r) for r in rows))
        return hashlib.sha256(data_str.encode()).hexdigest()

    def process_csv_file(
        self,
        table_name: str,
        csv_path: Path,
        key_columns: List[str] = None,
        generate_dashboard: bool = True,
    ):
        """Process CSV file and sync to database"""
        print(f"\n{'='*60}")
        print(f"📊 Processing: {table_name}")
        print(f"{'='*60}")

        # Load CSV
        rows = self.load_csv_file(csv_path)
        if not rows:
            print(f"⚠️  No data in {csv_path}")
            return

        # Infer types
        col_types = self.infer_column_types(rows)
        print(f"📋 Columns: {list(col_types.keys())}")

        # Convert SQLAlchemy types for table creation
        sa_col_types = {}
        for col_name, py_type in col_types.items():
            from sqlalchemy import Integer, Float, String
            if py_type == int:
                sa_col_types[col_name] = Integer
            elif py_type == float:
                sa_col_types[col_name] = Float
            else:
                sa_col_types[col_name] = String(255)

        # Create table if needed
        self.db.create_table(table_name, sa_col_types)

        # Normalize data
        normalized_rows = self.normalize_rows(rows, col_types)

        # Upsert data
        if key_columns is None:
            key_columns = ["id"] if "id" in col_types else None

        upserted = self.db.upsert_rows(table_name, normalized_rows, key_columns)

        # Update metadata with source hash
        source_hash = self.compute_source_hash(rows)
        self.db.update_metadata(table_name, source_hash)

        # Get stats
        stats = self.db.get_table_stats(table_name)
        print(f"📈 Table stats: {stats}")

        # Dashboard generation disabled - use Grafana directly for better control
        # if generate_dashboard and AUTO_GENERATE_DASHBOARDS:
        #     try:
        #         dashboard = generate_dashboard_json(table_name, sa_col_types, normalized_rows)
        #         dashboard_path = DASHBOARDS_DIR / f"{table_name}_dashboard.json"
        #         save_dashboard_json(dashboard, str(dashboard_path))
        #         print(f"📊 Dashboard saved: {dashboard_path.name}")
        #     except Exception as e:
        #         print(f"⚠️  Dashboard generation skipped: {e}")

    def process_documents_folder(self):
        """Process all CSV files in documents folder"""
        csv_files = list(DOCUMENTS_DIR.glob("*.csv"))
        
        if not csv_files:
            print(f"📁 No CSV files in {DOCUMENTS_DIR}")
            return

        print(f"\n🔄 Processing {len(csv_files)} CSV files from documents folder")
        
        for csv_file in sorted(csv_files):
            table_name = csv_file.stem.lower().replace("-", "_").replace(" ", "_")
            self.process_csv_file(table_name, csv_file)

    def load_retail_datasets(self):
        """Load pre-configured retail datasets"""
        if not LOAD_RETAIL_DATA:
            print("⏭️  Retail data loading disabled")
            return

        print(f"\n📦 Loading retail datasets...")
        
        retail_files = {
            "retail_orders": PIPELINE_DIR / "documents" / "retail_orders.csv",
            "retail_products": PIPELINE_DIR / "documents" / "retail_products.csv",
            "retail_sales": PIPELINE_DIR / "documents" / "retail_sales.csv",
        }

        for table_name, csv_path in retail_files.items():
            if csv_path.exists():
                self.process_csv_file(table_name, csv_path)
            else:
                print(f"⏭️  Skipping {table_name}: file not found")

    def load_freshservice_data(self):
        """Load Freshservice API data"""
        if not LOAD_FRESHSERVICE_DATA:
            print("⏭️  Freshservice data loading disabled")
            return

        print(f"\n🔌 Loading Freshservice data...")
        
        try:
            records = fetch_freshservice_data()
            if not records:
                print("⚠️  No Freshservice data available")
                return

            # Save to CSV
            csv_path = DOCUMENTS_DIR / "freshservice_data.csv"
            save_freshservice_csv(records, DOCUMENTS_DIR)
            
            # Load into database
            self.process_csv_file("freshservice_data", csv_path)
        except Exception as e:
            print(f"❌ Error loading Freshservice data: {e}")

    def show_database_summary(self):
        """Display summary of all tables in database"""
        print(f"\n{'='*60}")
        print("📊 DATABASE SUMMARY")
        print(f"{'='*60}")
        
        tables_info = self.db.get_tables_info()
        
        if not tables_info:
            print("No tables found")
            return

        for info in tables_info:
            print(f"\n📋 {info['table_name']}")
            print(f"   Rows: {info['row_count']}")
            print(f"   Last synced: {info['last_synced']}")
            print(f"   Schema version: {info['schema_version']}")

    def run(self):
        """Execute full ETL pipeline"""
        print("\n" + "="*60)
        print("🚀 STREAMLINED ETL PIPELINE")
        print("="*60)
        print(f"Database: {self.db.engine.url.host}:{self.db.engine.url.port}/{self.db.engine.url.database}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("="*60)

        try:
            # Load all data sources
            self.load_retail_datasets()
            self.process_documents_folder()
            self.load_freshservice_data()

            # Show summary
            self.show_database_summary()

            print(f"\n✅ ETL Pipeline completed successfully!")

        except Exception as e:
            print(f"\n❌ Pipeline error: {e}")
            raise


if __name__ == "__main__":
    pipeline = ETLPipeline()
    pipeline.run()
