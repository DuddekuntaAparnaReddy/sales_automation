"""
Migration: Create tables for surveys, survey_questions, survey_responses, and survey_insights.
Safe to run multiple times.
"""
import psycopg2

conn = psycopg2.connect(
    host='localhost', database='sales_automation_db',
    user='postgres', password='Aparna@123'
)
conn.autocommit = True
cur = conn.cursor()

def table_exists(table):
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name = %s
        );
    """, (table,))
    return cur.fetchone()[0]

# 1. Create surveys table
if not table_exists('surveys'):
    cur.execute("""
        CREATE TABLE surveys (
            id SERIAL PRIMARY KEY,
            title VARCHAR(150) NOT NULL,
            description TEXT,
            category VARCHAR(100),
            expiry_date DATE,
            created_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  + Created surveys table")
else:
    print("  . surveys table already exists")

# 2. Create survey_questions table
if not table_exists('survey_questions'):
    cur.execute("""
        CREATE TABLE survey_questions (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
            question_text TEXT NOT NULL,
            question_type VARCHAR(50) NOT NULL
        );
    """)
    print("  + Created survey_questions table")
else:
    print("  . survey_questions table already exists")

# 3. Create survey_responses table
if not table_exists('survey_responses'):
    cur.execute("""
        CREATE TABLE survey_responses (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER REFERENCES surveys(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
            response_data JSONB NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  + Created survey_responses table")
else:
    print("  . survey_responses table already exists")

# 4. Create survey_insights table
if not table_exists('survey_insights'):
    cur.execute("""
        CREATE TABLE survey_insights (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER UNIQUE REFERENCES surveys(id) ON DELETE CASCADE,
            top_interests JSONB,
            common_issues JSONB,
            sentiment VARCHAR(50),
            recommendations JSONB,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("  + Created survey_insights table")
else:
    print("  . survey_insights table already exists")

cur.close()
conn.close()
print("\nSurvey Database Migration complete.")
