import pyodbc
import pandas as pd
import numpy as np
import json
from typing import List


class SQLServerLoader:
    def __init__(self, server="WZNITRO\\WZDEVMSSQLSERVER", database="OpenF1"):
        self.conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
        )
        self.cursor = self.conn.cursor()

    # -----------------------------
    # Value cleaning
    # -----------------------------
    def _clean_value(self, value):
        """Convert any Pandas/Numpy/Python object into a SQL-safe Python type."""

        if isinstance(value, (list, tuple, np.ndarray)):
            return json.dumps([self._clean_value(v) for v in value])

        if isinstance(value, dict):
            return json.dumps(value)

        try:
            if value is None or pd.isna(value):
                return None
        except Exception:
            pass

        if isinstance(value, np.generic):
            return value.item()

        if isinstance(value, pd.Timestamp):
            return str(value)

        if isinstance(value, (np.bool_, bool)):
            return bool(value)

        return value

    # -----------------------------
    # Table creation
    # -----------------------------
    
    def _table_exists(self, table_name: str) -> bool:
        query = """
         SELECT 1
         FROM INFORMATION_SCHEMA.TABLES
         WHERE TABLE_NAME = ?
        """
        self.cursor.execute(query, (table_name,))
        return self.cursor.fetchone() is not None
    
    def _create_table_if_missing(self, df: pd.DataFrame, table_name: str):
                     
        # Skip if DataFrame has no columns
        if df.empty or len(df.columns) == 0:
            print(f"Warning: DataFrame for table {table_name} has no columns. Skipping table creation.")
            return
        
        columns = ", ".join([f"[{col}] NVARCHAR(MAX)" for col in df.columns])
        create_sql = f"""
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U'
        )
        CREATE TABLE {table_name} ({columns});
        """
        self.cursor.execute(create_sql)
        self.conn.commit()

    # -----------------------------
    # Main write method
    # -----------------------------
    def write_df(self, df: pd.DataFrame, table_name: str, mode="append", batch_size=500):
        df = df.copy()

        # 1. Create table if needed
        self._create_table_if_missing(table_name, df)

        # 2. If empty, stop here (no inserts, no truncate)
        if df.empty or len(df.columns) == 0:
            print(f"Warning: DataFrame for table {table_name} is empty. No rows inserted.")
            return

        # 3. If overwrite, truncate AFTER table exists
        if mode == "overwrite":
            self.cursor.execute(f"TRUNCATE TABLE {table_name}")
            self.conn.commit()

        # 4. Prepare insert
        placeholders = ", ".join(["?"] * len(df.columns))
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

        # Batch insert
        batch: List[List] = []

        for _, row in df.iterrows():
            clean_row = [self._clean_value(v) for v in row.values]
            batch.append(clean_row)

            if len(batch) >= batch_size:
                self.cursor.executemany(insert_sql, batch)
                batch = []

        # Insert remaining rows
        if batch:
            self.cursor.executemany(insert_sql, batch)

        self.conn.commit()

    # -----------------------------
    # Cleanup
    # -----------------------------
    def close(self):
        self.cursor.close()
        self.conn.close()