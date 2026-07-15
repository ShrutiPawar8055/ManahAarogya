import os
from sqlmodel import Session, create_engine, text
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("No DATABASE_URL found.")
    exit(1)

engine = create_engine(db_url)

commands = [
    # Therapist
    "ALTER TABLE therapist ADD COLUMN IF NOT EXISTS user_id INTEGER",
    "ALTER TABLE therapist ADD COLUMN IF NOT EXISTS session_duration INTEGER DEFAULT 60",
    "ALTER TABLE therapist ADD COLUMN IF NOT EXISTS google_calendar_token_json VARCHAR",
    
    # Appointment
    "ALTER TABLE appointment ADD COLUMN IF NOT EXISTS therapist_id INTEGER",
    "ALTER TABLE appointment ADD COLUMN IF NOT EXISTS start_time VARCHAR",
    "ALTER TABLE appointment ADD COLUMN IF NOT EXISTS end_time VARCHAR",
    "ALTER TABLE appointment ADD COLUMN IF NOT EXISTS therapist_notes VARCHAR",
    "ALTER TABLE appointment ADD COLUMN IF NOT EXISTS google_event_id VARCHAR",
    
    # Making some fields nullable
    "ALTER TABLE appointment ALTER COLUMN counselor_name DROP NOT NULL",
    "ALTER TABLE appointment ALTER COLUMN preferred_slot DROP NOT NULL",
    "ALTER TABLE appointment ALTER COLUMN status SET DEFAULT 'pending'",
]

with Session(engine) as session:
    for cmd in commands:
        try:
            print(f"Running: {cmd}")
            session.exec(text(cmd))
            session.commit()
            print("Success.")
        except Exception as e:
            print(f"Failed or already exists: {e}")
            session.rollback()

print("Migration completed.")
