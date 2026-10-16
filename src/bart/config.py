import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "ridership"
PARQUET = ROOT / "data" / "parquet"
OD = PARQUET / "od"
MARTS = ROOT / "data" / "marts"
FEATURES = ROOT / "data" / "features"
OUT = ROOT / "outputs"
FIG = OUT / "figures"
TAB = OUT / "tables"
MODELS = OUT / "models"
LOGS = OUT / "logs"

# i9-13900H: 6 P-cores (12 threads) + 8 E-cores = 20 logical CPUs; 32 GB DDR5.
cpu_count = os.cpu_count()
if cpu_count is None:
    THREADS = 20
else:
    THREADS = cpu_count

DUCKDB_MEMORY_LIMIT = "20GB"
DUCKDB_TEMP = PARQUET / ".duckdb_tmp"

folders = [PARQUET, MARTS, FEATURES, FIG, TAB, MODELS, LOGS, DUCKDB_TEMP]
for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)


def duck():
    con = duckdb.connect()
    con.execute(f"SET threads = {THREADS}")
    con.execute(f"SET memory_limit = '{DUCKDB_MEMORY_LIMIT}'")
    con.execute(f"SET temp_directory = '{DUCKDB_TEMP}'")
    con.execute("SET preserve_insertion_order = false")
    return con


MART_NAMES = ["stations", "calendar", "station_hour", "station_day", "system_hour", "od_month", "month_days"]


def create_views(con):
    con.execute(f"CREATE OR REPLACE VIEW od AS SELECT * FROM read_parquet('{OD}/*/*.parquet')")
    for name in MART_NAMES:
        path = MARTS / f"{name}.parquet"
        con.execute(f"CREATE OR REPLACE VIEW {name} AS SELECT * FROM read_parquet('{path}')")


def fetch_row(con, query):
    row = con.sql(query).fetchone()
    if row is None:
        raise ValueError(f"query returned no rows: {query}")
    return row


def fetch_value(con, query):
    row = fetch_row(con, query)
    return row[0]
