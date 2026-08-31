import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_db():
    conn = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="root123",
        host="localhost",
        port="5432"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'mib_rag_chatbot'")
    if not cur.fetchone():
        cur.execute("CREATE DATABASE mib_rag_chatbot")
        print("Database 'mib_rag_chatbot' created successfully.")
    else:
        print("Database 'mib_rag_chatbot' already exists.")
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    init_db()
