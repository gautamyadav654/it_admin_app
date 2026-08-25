import psycopg2

# Use the Neon DATABASE_URL
url = 'postgresql://neondb_owner:npg_YM6EZfua5SsN@ep-odd-wildflower-axi2nay7-pooler.c-4.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require'

conn = psycopg2.connect(url)
conn.autocommit = True
cur = conn.cursor()

# Get all tables
cur.execute("""
    SELECT tablename FROM pg_tables 
    WHERE schemaname = 'public'
""")
tables = cur.fetchall()

print(f'Found {len(tables)} tables:')
for t in tables:
    print(f'  Dropping {t[0]}...')
    cur.execute(f'DROP TABLE IF EXISTS "{t[0]}" CASCADE;')

print('All tables dropped!')
cur.close()
conn.close()