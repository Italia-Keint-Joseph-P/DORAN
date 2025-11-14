import os
import json
import pymysql
from datetime import datetime

def create_mysql_tables():
    """Create MySQL tables for chatbot data"""
    conn = pymysql.connect(host='localhost', user='root', database='chatbot_db')
    cursor = conn.cursor()

    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create email_directory table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_directory (
            id INT AUTO_INCREMENT PRIMARY KEY,
            school VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create faqs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faqs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create feedback table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create guest_rules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guest_rules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(255) DEFAULT 'guest',
            keywords TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id VARCHAR(255) PRIMARY KEY,
            questions JSON NOT NULL,
            description TEXT NOT NULL,
            user_type VARCHAR(50) DEFAULT 'both',
            urls JSON,
            url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create user_rules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_rules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(255) DEFAULT 'soict',
            keywords TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create visuals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS visuals (
            id VARCHAR(255) PRIMARY KEY,
            questions JSON NOT NULL,
            description TEXT NOT NULL,
            user_type VARCHAR(50) DEFAULT 'both',
            urls JSON,
            url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    print("MySQL tables created successfully")
    return conn, cursor

def migrate_categories(cursor, base_path):
    """Migrate categories.json to MySQL"""
    categories_path = os.path.join(base_path, 'categories.json')
    if os.path.exists(categories_path):
        with open(categories_path, 'r', encoding='utf-8') as f:
            categories = json.load(f)

        for category in categories:
            cursor.execute('INSERT IGNORE INTO categories (name) VALUES (%s)', (category,))
        print(f"Migrated {len(categories)} categories")

def migrate_email_directory(cursor, base_path):
    """Migrate email_directory.py to MySQL"""
    email_dir_path = os.path.join(base_path, 'email_directory.py')
    if os.path.exists(email_dir_path):
        # Read the Python file and extract the data
        with open(email_dir_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract the emails list from the Python file
        import ast
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'emails':
                    if isinstance(node.value, ast.List):
                        emails_data = []
                        for item in node.value.elts:
                            if isinstance(item, ast.Dict):
                                email_dict = {}
                                for key, value in zip(item.keys, item.values):
                                    if isinstance(key, ast.Str) and isinstance(value, ast.Str):
                                        email_dict[key.s] = value.s
                                emails_data.append(email_dict)

                        for email_data in emails_data:
                            cursor.execute('INSERT IGNORE INTO email_directory (school, email) VALUES (%s, %s)',
                                         (email_data.get('school', ''), email_data.get('email', '')))
                        print(f"Migrated {len(emails_data)} email entries")

def migrate_faqs(cursor, base_path):
    """Migrate faqs.json to MySQL"""
    faqs_path = os.path.join(base_path, 'faqs.json')
    if os.path.exists(faqs_path):
        with open(faqs_path, 'r', encoding='utf-8') as f:
            faqs = json.load(f)

        for faq in faqs:
            cursor.execute('INSERT INTO faqs (question, answer) VALUES (%s, %s)',
                         (faq.get('question', ''), faq.get('answer', '')))
        print(f"Migrated {len(faqs)} FAQs")

def migrate_locations(cursor, base_path):
    """Migrate locations.json to MySQL"""
    locations_path = os.path.join(base_path, 'locations', 'locations.json')
    if os.path.exists(locations_path):
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)

        for location in locations:
            cursor.execute('''INSERT INTO locations (id, questions, description, user_type, urls, url)
                            VALUES (%s, %s, %s, %s, %s, %s)''',
                         (location.get('id', ''),
                          json.dumps(location.get('questions', [])),
                          location.get('description', ''),
                          location.get('user_type', 'both'),
                          json.dumps(location.get('urls', [])),
                          location.get('url', '')))
        print(f"Migrated {len(locations)} locations")

def migrate_visuals(cursor, base_path):
    """Migrate visuals.json to MySQL"""
    visuals_path = os.path.join(base_path, 'visuals', 'visuals.json')
    if os.path.exists(visuals_path):
        with open(visuals_path, 'r', encoding='utf-8') as f:
            visuals = json.load(f)

        for visual in visuals:
            cursor.execute('''INSERT INTO visuals (id, questions, description, user_type, urls, url)
                            VALUES (%s, %s, %s, %s, %s, %s)''',
                         (visual.get('id', ''),
                          json.dumps(visual.get('questions', [])),
                          visual.get('description', ''),
                          visual.get('user_type', 'both'),
                          json.dumps(visual.get('urls', [])),
                          visual.get('url', '')))
        print(f"Migrated {len(visuals)} visuals")

def migrate_rules(cursor, base_path):
    """Migrate user and guest rules from JSON files to MySQL"""
    # Migrate user rules
    user_db_path = os.path.join(base_path, 'user_database')
    if os.path.exists(user_db_path):
        rules_file = os.path.join(user_db_path, 'all_user_rules.json')
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                user_rules = json.load(f)

            for rule in user_rules:
                cursor.execute('INSERT INTO user_rules (category, keywords, response) VALUES (%s, %s, %s)',
                             (rule.get('category', 'soict'),
                              json.dumps(rule.get('keywords', [])),
                              rule.get('response', '')))
            print(f"Migrated {len(user_rules)} user rules")

    # Migrate guest rules
    guest_db_path = os.path.join(base_path, 'guest_database')
    if os.path.exists(guest_db_path):
        rules_file = os.path.join(guest_db_path, 'all_guest_rules.json')
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                guest_rules = json.load(f)

            for rule in guest_rules:
                cursor.execute('INSERT INTO guest_rules (category, keywords, response) VALUES (%s, %s, %s)',
                             (rule.get('category', 'guest'),
                              json.dumps(rule.get('keywords', [])),
                              rule.get('response', '')))
            print(f"Migrated {len(guest_rules)} guest rules")

def main():
    """Main migration function"""
    base_path = 'database'

    print("Starting JSON to MySQL migration...")

    # Create tables
    conn, cursor = create_mysql_tables()

    try:
        # Migrate data
        migrate_categories(cursor, base_path)
        migrate_email_directory(cursor, base_path)
        migrate_faqs(cursor, base_path)
        migrate_locations(cursor, base_path)
        migrate_visuals(cursor, base_path)
        migrate_rules(cursor, base_path)

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {str(e)}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
