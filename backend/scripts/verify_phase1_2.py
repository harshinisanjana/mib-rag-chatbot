import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psycopg2
from app.core.config import settings
from app.db.database import engine

def verify():
    print("1. Testing PostgreSQL connection...")
    try:
        conn = psycopg2.connect(settings.database_url)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        pg_ver = cur.fetchone()[0]
        print(f"   Connected to PostgreSQL: {pg_ver}")
        
        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        ext = cur.fetchone()
        vector_installed = bool(ext)
        print(f"   pgvector extension installed: {vector_installed}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"   Connection failed: {e}")
        return False

    print("2. Checking SQLAlchemy Models and Schema...")
    try:
        # Check if tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"   Existing tables in DB: {tables}")
    except Exception as e:
        print(f"   Table inspection failed: {e}")

    return True

if __name__ == "__main__":
    verify()
