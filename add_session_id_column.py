from extensions import db
from app import app
from sqlalchemy import text, inspect

with app.app_context():
    # Check if session_id column exists
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns('chat_messages')]

    if 'session_id' not in columns:
        # Add session_id column to chat_messages table
        db.session.execute(text('ALTER TABLE chat_messages ADD COLUMN session_id VARCHAR(36) NOT NULL DEFAULT "default-session"'))
        db.session.commit()
        print("Added session_id column to chat_messages table")
    else:
        print("session_id column already exists in chat_messages table")
