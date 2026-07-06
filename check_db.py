import psycopg2

conn = psycopg2.connect(host='localhost', database='sales_automation_db', user='postgres', password='Aparna@123')
cur = conn.cursor()

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='campaigns' ORDER BY ordinal_position;")
print('CAMPAIGNS TABLE COLUMNS:')
for row in cur.fetchall():
    print(' ', row)

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
print('\nALL TABLES:')
for row in cur.fetchall():
    print(' ', row)

conn.close()
print('Done.')
