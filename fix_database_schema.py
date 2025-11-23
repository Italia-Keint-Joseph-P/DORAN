#!/usr/bin/env python3
"""
Database schema fix script for Railway deployment.
Adds missing columns to existing tables.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def get_database_url():
    """Get the correct database URL for Railway"""
    # Use the same logic as in app.py
    correct_db_url = 'mysql+pymysql://root:dDDFLZWyupsuUkbFDIGveYZFXxzAEIEA@mysql.railway.internal:3306/railway'
    return correct_db_url

def fix_email_directory_table(engine):
    """Add created_at column to email_directory table if it doesn't exist"""
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'email_directory'
                AND COLUMN_NAME = 'created_at'
            """))

            if not result.fetchone():
                print("Adding created_at column to email_directory table...")
                conn.execute(text("""
                    ALTER TABLE email_directory
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                conn.commit()
                print("✓ Added created_at column to email_directory table")
            else:
                print("✓ created_at column already exists in email_directory table")

    except SQLAlchemyError as e:
        print(f"Error fixing email_directory table: {e}")
        raise

def verify_tables(engine):
    """Verify that all required tables exist and have correct structure"""
    required_tables = ['faqs', 'locations', 'visuals', 'user_rules', 'guest_rules', 'email_directory', 'categories']

    try:
        with engine.connect() as conn:
            for table in required_tables:
                # Check if table exists
                result = conn.execute(text(f"""
                    SELECT TABLE_NAME
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = '{table}'
                """))

                if result.fetchone():
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' does not exist")
                    return False

            print("✓ All required tables exist")
            return True

    except SQLAlchemyError as e:
        print(f"Error verifying tables: {e}")
        return False

def main():
    """Main function to run database fixes"""
    print("Starting database schema fixes...")

    try:
        # Get database URL
        db_url = get_database_url()
        print(f"Connecting to database: {db_url.replace(db_url.split('@')[0].split('//')[1], '***:***')}")

        # Create engine with connection settings
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=30,
            pool_size=1,
            max_overflow=0,
            pool_timeout=30,
            pool_reset_on_return='rollback',
            connect_args={
                'connect_timeout': 30,
                'read_timeout': 30,
                'write_timeout': 30,
                'autocommit': True,
                'charset': 'utf8mb4',
                'init_command': 'SET SESSION sql_mode="STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO"',
            }
        )

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")

        # Verify tables exist
        if not verify_tables(engine):
            print("✗ Some required tables are missing. Please run migration first.")
            return 1

        # Fix email_directory table
        fix_email_directory_table(engine)

        print("✓ Database schema fixes completed successfully!")
        return 0

    except Exception as e:
        print(f"✗ Database schema fixes failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
