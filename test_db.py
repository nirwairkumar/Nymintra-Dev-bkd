import os
import sys
from sqlalchemy import create_engine, inspect

# Use the URL from .env
db_url = "postgresql://postgres:Nymintra-neo@db.biuqtilnapacxzqdpgfo.supabase.co:5432/postgres"

try:
    engine = create_engine(db_url, connect_args={"connect_timeout": 5})
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("CONNECTION SUCCESSFUL")
    print("TABLES:", tables)
except Exception as e:
    print("CONNECTION FAILED")
    print(str(e))
