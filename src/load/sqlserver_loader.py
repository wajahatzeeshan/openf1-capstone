import pyodbc
import pandas as pd
import numpy as np
import json

class SQLServerLoader:
    def __init__(self, server="WZNITRO\WZDEVMSSQLSERVER", database="OpenF1"):
        self.conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
        )
        self.cursor = self.conn.cursor()

    def _clean_value(self, value):
        """Convert any Pandas/Numpy/Python object into a SQL-safe Python type."""

        # 1. Handle lists/arrays BEFORE checking for NaN
        if isinstance(value, (list, tuple, np.ndarray)):
            return json.dumps([self._clean_value(v) for v in value])

        # 2. Handle dictionaries
        if isinstance(value, dict):
            return json.dumps(value)

        # 3. Handle missing values (only for scalars)
        try:
            if value is None or pd.isna(value):
                return None
        except Exception:
            pass  # value is not NA-compatible

        # 4. Convert numpy types to Python types
        if isinstance(value, (np.generic,)):
            return value.item()

        # 5. Convert timestamps to string
        if isinstance(value, (pd.Timestamp,)):
            return str(value)

        # 6. Convert booleans
        if isinstance(value, (np.bool_, bool)):
            return bool(value)

        # 7. Everything else stays as-is
        return value

    def write_df(self, df: pd.DataFrame, table_name: str, mode="overwrite"):
        # Create table if not exists
        columns = ", ".join([f"[{col}] NVARCHAR(MAX)" for col in df.columns])
        create_sql = f"""
        IF NOT EXISTS (
            SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U'
        )
        CREATE TABLE {table_name} ({columns});
        """
        self.cursor.execute(create_sql)
        self.conn.commit()

        # Insert rows
        for _, row in df.iterrows():
            clean_row = [self._clean_value(v) for v in row.values]

            placeholders = ", ".join(["?"] * len(clean_row))
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"

            self.cursor.execute(insert_sql, clean_row)

        self.conn.commit()