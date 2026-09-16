import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")

try:
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    print("Connection successful! PostgreSQL version:")
    print(db_version[0])
    cursor.close()
    conn.close()
except Exception as e:
    print("Database connection failed:", e)
