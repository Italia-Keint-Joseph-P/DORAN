import os
import json
from flask import Flask
from extensions import db
from chatbot_models import Faq

# Create a minimal Flask app to get the database connection
app = Flask(__name__)

# Use the same database config as the main app
mysql_url = os.environ.get('MYSQL_URL')
if mysql_url and mysql_url.startswith('mysql://'):
    mysql_url = mysql_url.replace('mysql://', 'mysql+pymysql://', 1)

local_user_db_url = 'mysql+pymysql://root:@localhost/doran'
railway_user_db_url = 'mysql+pymysql://root:smxcYzdpwUJTAiRdJWQFPJNbfsbVTAGC@trolley.proxy.rlwy.net:10349/doran_db'

local_chatbot_db_url = 'mysql+pymysql://root:@localhost/chatbot_db'
railway_chatbot_db_url = 'mysql+pymysql://root:smxcYzdpwUJTAiRdJWQFPJNbfsbVTAGC@trolley.proxy.rlwy.net:10349/chatbot_db'

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or mysql_url or local_user_db_url
app.config['CHATBOT_DATABASE_URI'] = os.environ.get('CHATBOT_DATABASE_URL') or local_chatbot_db_url

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 1,
    'max_overflow': 2,
    'pool_timeout': 10,
    'connect_args': {
        'connect_timeout': 5,
        'read_timeout': 10,
        'write_timeout': 10,
    }
}

app.config['SQLALCHEMY_BINDS'] = {
    'chatbot_db': app.config['CHATBOT_DATABASE_URI']
}

db.init_app(app)

def migrate_faqs():
    with app.app_context():
        # Check if FAQs already exist
        existing_faqs = Faq.query.count()
        if existing_faqs > 0:
            print(f"FAQs already exist in database ({existing_faqs} records). Skipping migration.")
            return

        # Load FAQs from JSON
        faqs_path = os.path.join(os.path.dirname(__file__), 'database', 'faqs.json')
        try:
            with open(faqs_path, 'r', encoding='utf-8') as f:
                faqs = json.load(f)
        except Exception as e:
            print(f"Failed to load FAQs from JSON: {e}")
            return

        # Migrate to MySQL
        for faq in faqs:
            new_faq = Faq(question=faq['question'], answer=faq['answer'])
            db.session.add(new_faq)

        try:
            db.session.commit()
            print(f"Successfully migrated {len(faqs)} FAQs to MySQL")
        except Exception as e:
            db.session.rollback()
            print(f"Failed to migrate FAQs: {e}")

if __name__ == '__main__':
    migrate_faqs()
