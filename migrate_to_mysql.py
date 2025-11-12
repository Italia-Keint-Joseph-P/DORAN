import json
import mysql.connector
import os

# Database connection
def get_db_connection():
    # Use Railway MySQL for production
    return mysql.connector.connect(
        host='trolley.proxy.rlwy.net',
        port=10349,
        user='root',
        password='smxcYzdpwUJTAiRdJWQFPJNbfsbVTAGC',
        database='railway'
    )

# Create database if not exists
def create_database():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password=''
    )
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS chatbot_db")
    conn.commit()
    cursor.close()
    conn.close()

# Create tables
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # User rules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_rules (
            id VARCHAR(255) PRIMARY KEY,
            category VARCHAR(255),
            question TEXT,
            answer TEXT,
            user_type VARCHAR(50) DEFAULT 'user'
        )
    ''')

    # Guest rules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guest_rules (
            id VARCHAR(255) PRIMARY KEY,
            category VARCHAR(255),
            question TEXT,
            answer TEXT,
            user_type VARCHAR(50) DEFAULT 'guest'
        )
    ''')

    # Locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id VARCHAR(255) PRIMARY KEY,
            questions JSON,
            urls JSON,
            description TEXT,
            user_type VARCHAR(50) DEFAULT 'both'
        )
    ''')

    # Visuals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visuals (
            id VARCHAR(255) PRIMARY KEY,
            questions JSON,
            urls JSON,
            description TEXT,
            user_type VARCHAR(50) DEFAULT 'user'
        )
    ''')

    # FAQs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faqs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT,
            answer TEXT
        )
    ''')

    # Feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255),
            message TEXT,
            timestamp DATETIME
        )
    ''')

    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255),
            description TEXT
        )
    ''')

    # Email directory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_directory (
            school VARCHAR(255),
            email VARCHAR(255)
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()

# Import user rules
def import_user_rules():
    with open('database/user_database/all_user_rules.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_db_connection()
    cursor = conn.cursor()

    if isinstance(data, dict):
        for category, rules in data.items():
            for rule in rules:
                cursor.execute('''
                    INSERT INTO user_rules (id, category, question, answer, user_type)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    category=VALUES(category), question=VALUES(question), answer=VALUES(answer)
                ''', (rule.get('id'), category, rule.get('question'), rule.get('answer'), 'user'))
    else:
        for rule in data:
            cursor.execute('''
                INSERT INTO user_rules (id, category, question, answer, user_type)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                category=VALUES(category), question=VALUES(question), answer=VALUES(answer)
            ''', (rule.get('id'), 'combined_user', rule.get('question'), rule.get('answer'), 'user'))

    conn.commit()
    cursor.close()
    conn.close()

# Import guest rules
def import_guest_rules():
    with open('database/guest_database/all_guest_rules.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_db_connection()
    cursor = conn.cursor()

    if isinstance(data, dict):
        for category, rules in data.items():
            for rule in rules:
                cursor.execute('''
                    INSERT INTO guest_rules (id, category, question, answer, user_type)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    category=VALUES(category), question=VALUES(question), answer=VALUES(answer)
                ''', (rule.get('id'), category, rule.get('question'), rule.get('answer'), 'guest'))
    else:
        for rule in data:
            cursor.execute('''
                INSERT INTO guest_rules (id, category, question, answer, user_type)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                category=VALUES(category), question=VALUES(question), answer=VALUES(answer)
            ''', (rule.get('id'), 'combined_guest', rule.get('question'), rule.get('answer'), 'guest'))

    conn.commit()
    cursor.close()
    conn.close()

# Import locations
def import_locations():
    with open('database/locations/locations.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_db_connection()
    cursor = conn.cursor()

    for entry in data:
        cursor.execute('''
            INSERT INTO locations (id, questions, urls, description, user_type)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            questions=VALUES(questions), urls=VALUES(urls), description=VALUES(description)
        ''', (entry.get('id'), json.dumps(entry.get('questions', [])), json.dumps(entry.get('urls', [])), entry.get('description'), entry.get('user_type', 'both')))

    conn.commit()
    cursor.close()
    conn.close()

# Import visuals
def import_visuals():
    with open('database/visuals/visuals.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_db_connection()
    cursor = conn.cursor()

    for entry in data:
        cursor.execute('''
            INSERT INTO visuals (id, questions, urls, description, user_type)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            questions=VALUES(questions), urls=VALUES(urls), description=VALUES(description)
        ''', (entry.get('id'), json.dumps(entry.get('questions', [])), json.dumps(entry.get('urls', [])), entry.get('description'), entry.get('user_type', 'user')))

    conn.commit()
    cursor.close()
    conn.close()

# Import FAQs
def import_faqs():
    with open('database/faqs.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_db_connection()
    cursor = conn.cursor()

    for faq in data:
        cursor.execute('''
            INSERT INTO faqs (question, answer)
            VALUES (%s, %s)
        ''', (faq.get('question'), faq.get('answer')))

    conn.commit()
    cursor.close()
    conn.close()

# Import feedback
def import_feedback():
    with open('database/feedback/feedback.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_db_connection()
    cursor = conn.cursor()

    for feedback in data:
        cursor.execute('''
            INSERT INTO feedback (id, user_id, message, timestamp)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            user_id=VALUES(user_id), message=VALUES(message), timestamp=VALUES(timestamp)
        ''', (feedback.get('id'), feedback.get('user_id'), feedback.get('message'), feedback.get('timestamp')))

    conn.commit()
    cursor.close()
    conn.close()

# Import categories
def import_categories():
    with open('database/categories.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_db_connection()
    cursor = conn.cursor()

    for category in data:
        if isinstance(category, str):
            cursor.execute('''
                INSERT INTO categories (id, name, description)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name=VALUES(name), description=VALUES(description)
            ''', (category, category, ''))
        else:
            cursor.execute('''
                INSERT INTO categories (id, name, description)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name=VALUES(name), description=VALUES(description)
            ''', (category.get('id'), category.get('name'), category.get('description')))

    conn.commit()
    cursor.close()
    conn.close()

# Import email directory (assuming it's a list of dicts)
def import_email_directory():
    # Since email_directory.py uses Flask app context, we'll skip it and use the data we already have
    # The email directory was already imported manually
    pass

if __name__ == '__main__':
    create_database()
    create_tables()
    import_user_rules()
    import_guest_rules()
    import_locations()
    import_visuals()
    import_faqs()
    import_feedback()
    import_categories()
    import_email_directory()
    print("Migration completed!")
