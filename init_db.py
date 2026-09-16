import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
db_url=os.getenv("DATABASE_URL")
conn=psycopg2.connect(db_url)
cursor=conn.cursor()

Create_table_query="""
CREATE TABLE IF NOT EXISTS
device_stats(device_id VARCHAR PRIMARY KEY, Transaction_count INT DEFAULT 0);

CREATE TABLE IF NOT EXISTS 
ip_state (ip_address VARCHAR PRIMARY KEY, transaction_count INT DEFAULT 0);

CREATE TABLE IF NOT EXISTS
card_state (card_id VARCHAR PRIMARY KEY, total_amount FLOAT DEFAULT 0.0);
"""
cursor.execute(Create_table_query)
conn.commit()
cursor.close()
conn.close()

print("Table Created Successfully")