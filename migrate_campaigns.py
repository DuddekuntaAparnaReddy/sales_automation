"""
Migration: Add missing columns to campaigns and email_logs tables.
Safe to run multiple times (checks existence before altering).
"""
import psycopg2

conn = psycopg2.connect(
    host='localhost', database='sales_automation_db',
    user='postgres', password='Aparna@123'
)
conn.autocommit = True
cur = conn.cursor()

def column_exists(table, column):
    cur.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s AND column_name=%s
    """, (table, column))
    return cur.fetchone() is not None

# --- campaigns table ---
campaign_columns = [
    ("product_name",    "VARCHAR(150)"),
    ("offer_details",   "TEXT"),
    ("target_audience", "VARCHAR(100)"),
    ("start_date",      "DATE"),
    ("end_date",        "DATE"),
    ("status",          "VARCHAR(30) DEFAULT 'Active'"),
    ("created_by",      "INTEGER"),
    ("created_at",      "TIMESTAMP DEFAULT NOW()"),
    ("ai_title",        "VARCHAR(255)"),
    ("ai_subject",      "VARCHAR(255)"),
    ("ai_body",         "TEXT"),
    ("ai_cta",          "VARCHAR(100)"),
]

print("Migrating campaigns table...")
for col, coltype in campaign_columns:
    if not column_exists('campaigns', col):
        cur.execute(f'ALTER TABLE campaigns ADD COLUMN {col} {coltype};')
        print(f"  + Added campaigns.{col}")
    else:
        print(f"  . campaigns.{col} already exists")

# --- email_logs table ---
if not column_exists('email_logs', 'campaign_id'):
    cur.execute('ALTER TABLE email_logs ADD COLUMN campaign_id INTEGER;')
    print("  + Added email_logs.campaign_id")
else:
    print("  . email_logs.campaign_id already exists")

cur.close()
conn.close()
print("\nMigration complete.")
