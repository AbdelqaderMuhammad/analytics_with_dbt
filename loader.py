"""
Loads raw_data/*.csv (produced by generate_data.py) into Snowflake as raw
source tables, standing in for an ingestion tool like Airbyte/Fivetran.

Every table is fully overwritten on each run because generate_data.py always
writes the complete current state (dims) or full history (facts, since
'increment' mode appends to the existing CSV before rewriting it). That
keeps this loader simple and idempotent: run it after 'init' and after every
'increment' with no special-casing.

Env vars expected (matching your dbt dev profile):
    SNOWFLAKE_ACCOUNT     e.g. SOVARHJ-YK46801
    SNOWFLAKE_USER        e.g. dbt_dev_user
    SNOWFLAKE_PASSWORD
    SNOWFLAKE_ROLE        e.g. dbt_dev_role
    SNOWFLAKE_WAREHOUSE   e.g. dev_wh
    SNOWFLAKE_DATABASE    e.g. analytics_dev
    SNOWFLAKE_SCHEMA      defaults to 'raw'

Usage:
    python load_to_snowflake.py
    python load_to_snowflake.py --raw-dir raw_data --schema raw
"""

import argparse
import os
import sys

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

FILE_TO_TABLE = {
    "customers.csv": "customers",
    "products.csv": "products",
    "orders.csv": "orders",
    "order_items.csv": "order_items",
    "payments.csv": "payments",
    "support_tickets.csv": "support_tickets",
    "marketing_spend.csv": "marketing_spend",
}


def get_connection():
    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD",
                "SNOWFLAKE_ROLE", "SNOWFLAKE_WAREHOUSE", "SNOWFLAKE_DATABASE"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        sys.exit(f"Missing required env vars: {', '.join(missing)}")

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
    )


def load_file(conn, path, table_name, schema, database):
    df = pd.read_csv(path)
    # Snowflake convention: uppercase unquoted identifiers. write_pandas
    # will create the table with uppercase columns unless quote_identifiers
    # is handled explicitly — normalize here so schema.yml sources match
    # what actually lands in Snowflake.
    df.columns = [c.upper() for c in df.columns]

    success, n_chunks, n_rows, _ = write_pandas(
        conn,
        df,
        table_name=table_name.upper(),
        database=database,
        schema=schema.upper(),
        auto_create_table=True,
        overwrite=True,
        quote_identifiers=False,
    )
    status = "OK" if success else "FAILED"
    print(f"  [{status}] {table_name}: {n_rows} rows in {n_chunks} chunk(s)")
    return success


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="raw_data")
    parser.add_argument("--schema", default=os.environ.get("SNOWFLAKE_SCHEMA", "raw"))
    args = parser.parse_args()

    conn = get_connection()
    database = os.environ["SNOWFLAKE_DATABASE"]

    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {database}.{args.schema}")

        print(f"Loading into {database}.{args.schema} ...")
        all_ok = True
        for fname, table in FILE_TO_TABLE.items():
            path = os.path.join(args.raw_dir, fname)
            if not os.path.exists(path):
                print(f"  [SKIP] {fname} not found in {args.raw_dir}/")
                continue
            ok = load_file(conn, path, table, args.schema, database)
            all_ok = all_ok and ok

        if not all_ok:
            sys.exit(1)
        print("Done.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()