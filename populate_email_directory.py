#!/usr/bin/env python3
"""
Script to populate the email directory with sample data.
Run this after fixing the database schema.
"""

import os
import sys
from flask import Flask
from extensions import db
from models import EmailDirectory

# Create a minimal Flask app to get the database connection
app = Flask(__name__)

# Use Railway MySQL for production
railway_chatbot_db_url = 'mysql+pymysql://root:dDDFLZWyupsuUkbFDIGveYZFXxzAEIEA@mysql.railway.internal:3306/railway'

app.config['SQLALCHEMY_DATABASE_URI'] = railway_chatbot_db_url
app.config['CHATBOT_DATABASE_URI'] = railway_chatbot_db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 30,
    'pool_size': 1,
    'max_overflow': 0,
    'pool_timeout': 30,
    'connect_args': {
        'connect_timeout': 30,
        'read_timeout': 30,
        'write_timeout': 30,
        'autocommit': True,
        'charset': 'utf8mb4',
        'init_command': 'SET SESSION sql_mode="STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"',
    }
}

# Configure binds for multiple databases (same as main app)
app.config['SQLALCHEMY_BINDS'] = {
    'chatbot_db': app.config['CHATBOT_DATABASE_URI']
}

db.init_app(app)

# Sample email data - replace with actual email data as needed
sample_emails = [
    {"school": "SOICT", "email": "soict@wvsu.edu.ph"},
    {"school": "SOIT", "email": "soit@wvsu.edu.ph"},
    {"school": "SOED", "email": "soed@wvsu.edu.ph"},
    {"school": "SOBM", "email": "sobm@wvsu.edu.ph"},
    {"school": "Registrar", "email": "registrar1@wvsu.edu.ph"},
    {"school": "WVSU PC", "email": "pototan@wvsu.edu.ph"},
    {"school": "OSA", "email": "osa@wvsu.edu.ph"}
]

def populate_email_directory():
    """Populate the email directory with sample data"""
    try:
        with app.app_context():
            # Check if table already has data
            existing_count = EmailDirectory.query.count()
            if existing_count > 0:
                print(f"Email directory already has {existing_count} entries. Skipping population.")
                return

            # Add sample emails
            added_count = 0
            for email_data in sample_emails:
                # Check if email already exists
                existing = EmailDirectory.query.filter_by(email=email_data['email']).first()
                if not existing:
                    new_email = EmailDirectory(
                        school=email_data['school'],
                        email=email_data['email']
                    )
                    db.session.add(new_email)
                    added_count += 1

            db.session.commit()
            print(f"Successfully added {added_count} email entries to the directory")

    except Exception as e:
        print(f"Error populating email directory: {e}")
        db.session.rollback()
        raise

def main():
    """Main function"""
    print("Starting email directory population...")

    try:
        # Test database connection
        with app.app_context():
            db.engine.execute("SELECT 1")
        print("✓ Database connection successful")

        # Populate email directory
        populate_email_directory()

        print("✓ Email directory population completed successfully!")

    except Exception as e:
        print(f"✗ Email directory population failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
