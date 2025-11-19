import mysql.connector
import os
from urllib.parse import urlparse
from chatbot_models import EmailDirectory
from extensions import db

def get_db_config():
    """
    Get database configuration from environment variables.
    Prioritizes MYSQL_URL if available, otherwise uses Railway defaults.
    """
    mysql_url = os.environ.get('MYSQL_URL')
    if mysql_url and mysql_url.startswith('mysql://'):
        parsed = urlparse(mysql_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 3306,
            'user': parsed.username,
            'password': parsed.password,
            'database': parsed.path.lstrip('/')
        }
    else:
        # Use Railway defaults if individual vars not set
        return {
            'host': os.environ.get('MYSQLHOST', 'mysql.railway.internal'),
            'port': int(os.environ.get('MYSQLPORT', 3306)),
            'user': os.environ.get('MYSQLUSER', 'root'),
            'password': os.environ.get('MYSQLPASSWORD', 'dDDFLZWyupsuUkbFDIGveYZFXxzAEIEA'),
            'database': os.environ.get('MYSQLDATABASE', 'railway')
        }

def get_all_emails():
    """
    Get all emails using SQLAlchemy (requires Flask context).
    """
    try:
        emails = EmailDirectory.query.all()
        return [{'id': e.id, 'school': e.school, 'email': e.email} for e in emails]
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []

def add_email(school, email):
    try:
        new_email = EmailDirectory(school=school, email=email)
        db.session.add(new_email)
        db.session.commit()
        return new_email.id
    except Exception as e:
        print(f"Error adding email: {e}")
        db.session.rollback()
        raise e

def update_email(id, school, email):
    try:
        email_entry = EmailDirectory.query.get(id)
        if email_entry:
            email_entry.school = school
            email_entry.email = email
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Error updating email: {e}")
        db.session.rollback()
        raise e

def delete_email(id):
    try:
        email_entry = EmailDirectory.query.get(id)
        if email_entry:
            db.session.delete(email_entry)
            db.session.commit()
            return True
        return False
    except Exception as e:
        print(f"Error deleting email: {e}")
        db.session.rollback()
        raise e
