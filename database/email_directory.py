import mysql.connector
import os
from urllib.parse import urlparse

def get_db_config():
    """
    Get database configuration from environment variables.
    Prioritizes MYSQL_URL if available, otherwise uses individual vars.
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
        return {
            'host': os.environ.get('MYSQLHOST'),
            'port': int(os.environ.get('MYSQLPORT', 3306)),
            'user': os.environ.get('MYSQLUSER'),
            'password': os.environ.get('MYSQLPASSWORD'),
            'database': os.environ.get('MYSQLDATABASE', 'railway')
        }

def get_all_emails():
    """
    Get all emails using direct MySQL connection (no Flask context required).
    """
    try:
        config = get_db_config()
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, school, email FROM email_directory")
        emails = cursor.fetchall()
        cursor.close()
        conn.close()
        return emails
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return []

def add_email(school, email):
    try:
        host = os.environ.get('MYSQLHOST', 'localhost')
        port = int(os.environ.get('MYSQLPORT', 3306))
        user = os.environ.get('MYSQLUSER', 'root')
        password = os.environ.get('MYSQLPASSWORD', '')
        database = os.environ.get('MYSQLDATABASE', 'chatbot_db')
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        cursor.execute("INSERT INTO email_directory (school, email) VALUES (%s, %s)", (school, email))
        conn.commit()
        email_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return email_id
    except Exception as e:
        print(f"Error adding email: {e}")
        raise e

def update_email(id, school, email):
    try:
        config = get_db_config()
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("UPDATE email_directory SET school = %s, email = %s WHERE id = %s", (school, email, id))
        conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return success
    except Exception as e:
        print(f"Error updating email: {e}")
        raise e

def delete_email(id):
    try:
        config = get_db_config()
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM email_directory WHERE id = %s", (id,))
        conn.commit()
        success = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return success
    except Exception as e:
        print(f"Error deleting email: {e}")
        raise e
