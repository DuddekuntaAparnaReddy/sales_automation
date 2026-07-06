import psycopg2
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Credentials
DB_USER = "postgres"
DB_PASSWORD = "Aparna@123"
DB_HOST = "localhost"
DB_NAME = "sales_automation_db"

import urllib.parse
DATABASE_URL = f"postgresql://{DB_USER}:{urllib.parse.quote_plus(DB_PASSWORD)}@{DB_HOST}/{DB_NAME}"

def get_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    return conn