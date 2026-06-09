"""
Streamlined PostgreSQL Database Manager
- Incremental syncing (upserts, not drops)
- Multi-table support with relationships
- Data change tracking
- Schema versioning
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

# Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "governance")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_SCHEMA = os.getenv("DB_SCHEMA", "public")

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

METADATA_TABLE = "data_metadata"
SCHEMA_VERSION = "1.0"


class DatabaseManager:
    """Manages PostgreSQL operations with incremental syncing"""

    def __init__(self):
        self.engine = create_engine(DATABASE_URL, echo=False)
        self.metadata = MetaData()
        self.Session = sessionmaker(bind=self.engine)

    def wait_for_connection(self, retries: int = 15, delay: int = 3):
        """Wait for PostgreSQL to be available"""
        import time

        for attempt in range(1, retries + 1):
            try:
                with self.engine.connect() as conn:
                    print(f"✅ Connected to PostgreSQL (attempt {attempt})")
                    return
            except Exception as exc:
                print(f"⏳ Postgres unavailable (attempt {attempt}/{retries}): {exc}")
                time.sleep(delay)
        raise RuntimeError("❌ Unable to connect to PostgreSQL after retries")

    def ensure_schema(self):
        """Create schema if it doesn't exist"""
        if DB_SCHEMA and DB_SCHEMA != "public":
            with self.engine.begin() as conn:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))
                print(f"✅ Schema '{DB_SCHEMA}' ready")

    def ensure_metadata_table(self):
        """Create metadata tracking table"""
        with self.engine.begin() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS "{DB_SCHEMA}"."{METADATA_TABLE}" (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(255) UNIQUE NOT NULL,
                    row_count INTEGER DEFAULT 0,
                    last_synced TIMESTAMP DEFAULT NOW(),
                    last_updated TIMESTAMP,
                    source_hash VARCHAR(64),
                    schema_version VARCHAR(20) DEFAULT '{SCHEMA_VERSION}',
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """))
            print(f"✅ Metadata table '{METADATA_TABLE}' ready")

    def infer_column_type(self, value: str):
        """Infer SQLAlchemy column type from value"""
        if value is None or value == "":
            return String(255)

        value_str = str(value).strip()
        if not value_str:
            return String(255)

        if value_str.isdigit():
            return Integer
        
        try:
            float(value_str)
            return Float
        except ValueError:
            pass

        return String(255)

    def build_table_definition(
        self, table_name: str, columns: Dict[str, Any], with_tracking: bool = True
    ) -> Table:
        """Build SQLAlchemy table definition with optional tracking columns"""
        table_columns = [
            Column("id", Integer, primary_key=True, autoincrement=True)
        ]

        # Add data columns
        for col_name, col_type in columns.items():
            if col_name == "id":
                continue
            table_columns.append(Column(col_name, col_type, nullable=True))

        # Add tracking columns
        if with_tracking:
            table_columns.extend([
                Column("created_at", DateTime, default=datetime.utcnow),
                Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
                Column("_source_hash", String(64), nullable=True),  # Track row changes
            ])

        return Table(
            table_name, self.metadata, *table_columns, schema=DB_SCHEMA
        )

    def create_table(self, table_name: str, columns: Dict[str, Any]):
        """Create table if it doesn't exist"""
        if self._table_exists(table_name):
            print(f"📋 Table '{table_name}' already exists")
            return

        table = self.build_table_definition(table_name, columns)
        self.metadata.create_all(self.engine)
        print(f"✅ Created table '{table_name}'")

    def _table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        inspector = inspect(self.engine)
        tables = inspector.get_table_names(schema=DB_SCHEMA)
        return table_name in tables

    def get_column_info(self, table_name: str) -> Dict[str, Any]:
        """Get existing table columns"""
        if not self._table_exists(table_name):
            return {}
        
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name, schema=DB_SCHEMA)
        return {col["name"]: col["type"] for col in columns}

    def upsert_rows(
        self, 
        table_name: str, 
        rows: List[Dict], 
        key_columns: Optional[List[str]] = None
    ) -> int:
        """
        Upsert rows into table (insert or update).
        
        Args:
            table_name: Target table
            rows: List of row dictionaries
            key_columns: Columns to use for matching (defaults to 'id')
        """
        if not rows:
            print(f"⚠️  No rows to upsert into '{table_name}'")
            return 0

        if key_columns is None:
            key_columns = ["id"]

        session = self.Session()
        try:
            # Get table metadata
            table = self._get_table_object(table_name)
            if table is None:
                print(f"❌ Table '{table_name}' not found")
                return 0

            # Add tracking info to rows
            for row in rows:
                if "updated_at" not in row:
                    row["updated_at"] = datetime.utcnow()
                if "created_at" not in row:
                    row["created_at"] = datetime.utcnow()

            # Use PostgreSQL upsert (INSERT ... ON CONFLICT)
            stmt = insert(table).values(rows)
            
            # Handle conflicts on key columns
            update_cols = {
                c.name: c 
                for c in table.columns 
                if c.name not in key_columns and c.name not in ["id", "created_at"]
            }
            
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=key_columns,
                set_=update_cols
            )

            session.execute(upsert_stmt)
            session.commit()
            
            print(f"✅ Upserted {len(rows)} rows into '{table_name}'")
            return len(rows)

        except Exception as e:
            session.rollback()
            print(f"❌ Error upserting rows: {e}")
            return 0
        finally:
            session.close()

    def _get_table_object(self, table_name: str) -> Optional[Table]:
        """Get SQLAlchemy table object"""
        inspector = inspect(self.engine)
        if not inspector.get_table_names(schema=DB_SCHEMA) or table_name not in inspector.get_table_names(schema=DB_SCHEMA):
            return None
        
        table = Table(
            table_name, self.metadata, autoload_with=self.engine, schema=DB_SCHEMA
        )
        return table

    def get_row_count(self, table_name: str) -> int:
        """Get row count for table"""
        session = self.Session()
        try:
            result = session.execute(
                text(f'SELECT COUNT(*) FROM "{DB_SCHEMA}"."{table_name}"')
            )
            count = result.scalar() or 0
            return count
        except Exception as e:
            print(f"⚠️  Error getting row count: {e}")
            return 0
        finally:
            session.close()

    def update_metadata(
        self,
        table_name: str,
        source_hash: Optional[str] = None,
    ):
        """Update metadata for a table"""
        session = self.Session()
        try:
            row_count = self.get_row_count(table_name)
            
            metadata_table = self._get_table_object(METADATA_TABLE)
            if metadata_table is None:
                return

            # Upsert metadata
            stmt = insert(metadata_table).values(
                table_name=table_name,
                row_count=row_count,
                last_synced=datetime.utcnow(),
                source_hash=source_hash,
            )
            
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=["table_name"],
                set_={
                    "row_count": row_count,
                    "last_synced": datetime.utcnow(),
                    "last_updated": datetime.utcnow(),
                    "source_hash": source_hash,
                }
            )
            
            session.execute(upsert_stmt)
            session.commit()
            print(f"✅ Metadata updated for '{table_name}' ({row_count} rows)")

        except Exception as e:
            session.rollback()
            print(f"⚠️  Error updating metadata: {e}")
        finally:
            session.close()

    def get_tables_info(self) -> List[Dict]:
        """Get info about all tables"""
        session = self.Session()
        try:
            result = session.execute(
                text(f'SELECT * FROM "{DB_SCHEMA}"."{METADATA_TABLE}" ORDER BY last_synced DESC')
            )
            rows = result.mappings().all()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"⚠️  Error getting tables info: {e}")
            return []
        finally:
            session.close()

    def delete_old_records(self, table_name: str, days: int = 90):
        """Delete records older than N days"""
        session = self.Session()
        try:
            session.execute(
                text(f"""
                    DELETE FROM "{DB_SCHEMA}"."{table_name}"
                    WHERE updated_at < NOW() - INTERVAL '{days} days'
                """)
            )
            session.commit()
            print(f"✅ Deleted old records from '{table_name}'")
        except Exception as e:
            session.rollback()
            print(f"⚠️  Error deleting old records: {e}")
        finally:
            session.close()

    def get_table_stats(self, table_name: str) -> Dict:
        """Get statistics for a table"""
        session = self.Session()
        try:
            result = session.execute(
                text(f"""
                    SELECT 
                        COUNT(*) as total_rows,
                        MAX(updated_at) as last_updated,
                        MIN(created_at) as first_created
                    FROM "{DB_SCHEMA}"."{table_name}"
                """)
            )
            row = result.mappings().first()
            return dict(row) if row else {}
        except Exception as e:
            print(f"⚠️  Error getting stats: {e}")
            return {}
        finally:
            session.close()
