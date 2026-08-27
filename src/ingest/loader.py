import logging
import os
import sys

import duckdb
import pandas as pd

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

def load_data_to_local_db(
    input_file: str = "data/mock_information_schema_jobs.jsonl",
    db_file: str = "data/local_warehouse.duckdb",
    table_name: str = "raw_information_schema_jobs"
) -> None:
    """
    Loads mock JSONL data into a local DuckDB database to simulate BigQuery's 
    information_schema without incurring cloud costs.
    """
    try:
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            raise FileNotFoundError(f"Missing input file: {input_file}")
            
        logger.info(f"Reading mock data from {input_file}")
        
        # Read JSONL into pandas
        # Using pandas first allows us to handle any complex nested dicts (like referenced_tables) 
        # as JSON strings if needed by DuckDB, but DuckDB handles pandas DataFrames natively.
        df = pd.read_json(input_file, lines=True)
        
        # Convert nested dict/lists to string representations for simpler local querying 
        # (BigQuery uses STRUCT/ARRAY, DuckDB supports JSON but string is easier for this mock)
        df['referenced_tables'] = df['referenced_tables'].apply(lambda x: str(x) if isinstance(x, list) else x)
        
        logger.info(f"Loaded {len(df)} rows into memory. Connecting to DuckDB at {db_file}")
        
        # Connect to DuckDB
        conn = duckdb.connect(db_file)
        
        # Create table (idempotent: we overwrite it for simplicity in dev)
        # In a real BQ ingestion script, we'd use MERGE or append-only with deduplication.
        logger.info(f"Writing to table {table_name}")
        conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
        
        logger.info("Successfully loaded mock data into local database.")
        
    except Exception as e:
        logger.exception("Failed to load data into local database.")
        raise e
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    load_data_to_local_db()
