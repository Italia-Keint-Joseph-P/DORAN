import os
import json
import ast
from datetime import datetime
from flask import Flask
from extensions import db
from chatbot_models import Category, Faq, Location, Visual, UserRule, GuestRule, EmailDirectory

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

def retry_db_operation(operation, max_retries=3, delay=1):
    """
    Retry a database operation with exponential backoff.
    """
    import time
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Database operation failed (attempt {attempt + 1}): {str(e)}")
                time.sleep(delay * (2 ** attempt))
            else:
                print(f"Database operation failed after {max_retries} attempts: {str(e)}")
                raise

def create_sqlalchemy_tables():
    """Create tables using SQLAlchemy for Railway MySQL"""
    try:
        with app.app_context():
            # Create tables for all binds
            db.create_all()
        print("Tables created successfully using SQLAlchemy")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

def migrate_categories(base_path):
    """Migrate categories.json to database"""
    def migrate_categories_operation():
        categories_path = os.path.join(base_path, 'categories.json')
        if os.path.exists(categories_path):
            with open(categories_path, 'r', encoding='utf-8') as f:
                categories = json.load(f)

            for category in categories:
                # Check if category already exists
                existing = Category.query.filter_by(name=category).first()
                if not existing:
                    new_cat = Category(name=category)
                    db.session.add(new_cat)
            db.session.commit()
            print(f"Migrated {len(categories)} categories")

    with app.app_context():
        retry_db_operation(migrate_categories_operation)

def migrate_email_directory(base_path):
    """Migrate email_directory.py to database"""
    email_dir_path = os.path.join(base_path, 'email_directory.py')
    if os.path.exists(email_dir_path):
        # Read the Python file and extract the data
        with open(email_dir_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract the emails list from the Python file
        tree = ast.parse(content)
        emails_data = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'emails':
                    if isinstance(node.value, ast.List):
                        for item in node.value.elts:
                            if isinstance(item, ast.Dict):
                                email_dict = {}
                                for key, value in zip(item.keys, item.values):
                                    if isinstance(key, ast.Str) and isinstance(value, ast.Str):
                                        email_dict[key.s] = value.s
                                emails_data.append(email_dict)

        with app.app_context():
            for email_data in emails_data:
                # Check if email already exists
                existing = EmailDirectory.query.filter_by(school=email_data.get('school', ''), email=email_data.get('email', '')).first()
                if not existing:
                    new_email = EmailDirectory(school=email_data.get('school', ''), email=email_data.get('email', ''))
                    db.session.add(new_email)
            db.session.commit()
        print(f"Migrated {len(emails_data)} email entries")

def migrate_faqs(base_path):
    """Migrate faqs.json to database, avoiding duplicates"""
    def migrate_faqs_operation():
        faqs_path = os.path.join(base_path, 'faqs.json')
        if os.path.exists(faqs_path):
            with open(faqs_path, 'r', encoding='utf-8') as f:
                faqs = json.load(f)

            migrated_count = 0
            for faq in faqs:
                # Check if FAQ already exists
                existing = Faq.query.filter_by(question=faq.get('question', ''), answer=faq.get('answer', '')).first()
                if not existing:
                    new_faq = Faq(question=faq.get('question', ''), answer=faq.get('answer', ''))
                    db.session.add(new_faq)
                    migrated_count += 1
            db.session.commit()
            print(f"Migrated {migrated_count} new FAQs (skipped {len(faqs) - migrated_count} duplicates)")

    with app.app_context():
        retry_db_operation(migrate_faqs_operation)

def migrate_locations(base_path):
    """Migrate locations.json to database"""
    locations_path = os.path.join(base_path, 'locations', 'locations.json')
    if os.path.exists(locations_path):
        with open(locations_path, 'r', encoding='utf-8') as f:
            locations = json.load(f)

        with app.app_context():
            for location in locations:
                new_loc = Location(
                    id=location.get('id', ''),
                    questions=location.get('questions', []),
                    description=location.get('description', ''),
                    user_type=location.get('user_type', 'both'),
                    urls=location.get('urls', []),
                    url=location.get('url', '')
                )
                db.session.add(new_loc)
            db.session.commit()
        print(f"Migrated {len(locations)} locations")

def migrate_visuals(base_path):
    """Migrate visuals.json to database"""
    def migrate_visuals_operation():
        visuals_path = os.path.join(base_path, 'visuals', 'visuals.json')
        if os.path.exists(visuals_path):
            with open(visuals_path, 'r', encoding='utf-8') as f:
                visuals = json.load(f)

            for visual in visuals:
                new_vis = Visual(
                    id=visual.get('id', ''),
                    questions=visual.get('questions', []),
                    description=visual.get('description', ''),
                    user_type=visual.get('user_type', 'both'),
                    urls=visual.get('urls', []),
                    url=visual.get('url', '')
                )
                db.session.add(new_vis)
            db.session.commit()
            print(f"Migrated {len(visuals)} visuals")

    with app.app_context():
        retry_db_operation(migrate_visuals_operation)

def migrate_rules(base_path):
    """Migrate user and guest rules from JSON files to database"""
    # Migrate user rules
    user_db_path = os.path.join(base_path, 'user_database')
    if os.path.exists(user_db_path):
        rules_file = os.path.join(user_db_path, 'all_user_rules.json')
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                user_rules_data = json.load(f)

            with app.app_context():
                total_user_rules = 0
                for category, rules_list in user_rules_data.items():
                    for rule in rules_list:
                        new_rule = UserRule(
                            category=category.lower(),
                            question=rule.get('question', ''),
                            answer=rule.get('answer', ''),
                            user_type='user'
                        )
                        db.session.add(new_rule)
                        total_user_rules += 1
                db.session.commit()
            print(f"Migrated {total_user_rules} user rules")

    # Migrate guest rules
    guest_db_path = os.path.join(base_path, 'guest_database')
    if os.path.exists(guest_db_path):
        rules_file = os.path.join(guest_db_path, 'all_guest_rules.json')
        if os.path.exists(rules_file):
            with open(rules_file, 'r', encoding='utf-8') as f:
                guest_rules_data = json.load(f)

            with app.app_context():
                total_guest_rules = 0
                for category, rules_list in guest_rules_data.items():
                    for rule in rules_list:
                        new_rule = GuestRule(
                            category=category.lower(),
                            question=rule.get('question', ''),
                            answer=rule.get('answer', ''),
                            user_type='guest'
                        )
                        db.session.add(new_rule)
                        total_guest_rules += 1
                db.session.commit()
            print(f"Migrated {total_guest_rules} guest rules")

def main():
    """Main migration function using SQLAlchemy"""
    base_path = 'database'

    print("Starting JSON to Railway MySQL database migration...")

    # Create tables
    create_sqlalchemy_tables()

    try:
        # Migrate data
        migrate_categories(base_path)
        migrate_email_directory(base_path)
        migrate_faqs(base_path)
        migrate_locations(base_path)
        migrate_visuals(base_path)
        migrate_rules(base_path)

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed: {str(e)}")
        with app.app_context():
            db.session.rollback()

if __name__ == '__main__':
    main()
