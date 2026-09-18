import psycopg2

# Your exact Neon connection string
neon_url = 'postgresql://neondb_owner:npg_3RWMSgYNLvd5@ep-sparkling-recipe-aev1us5v-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

conn = psycopg2.connect(neon_url)
cursor = conn.cursor()

# This renames the table to match your app.py code
cursor.execute("ALTER TABLE predection RENAME TO predictions;")
conn.commit()

print("Table renamed successfully!")

cursor.close()
conn.close()