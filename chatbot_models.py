from extensions import db

# Chatbot data models for chatbot_db database
class Category(db.Model):
    __tablename__ = 'categories'
    __bind_key__ = 'chatbot_db'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class Faq(db.Model):
    __tablename__ = 'faqs'
    __bind_key__ = 'chatbot_db'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class Location(db.Model):
    __tablename__ = 'locations'
    __bind_key__ = 'chatbot_db'
    id = db.Column(db.String(255), primary_key=True)
    questions = db.Column(db.JSON, nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_type = db.Column(db.String(50), nullable=False, default='both')
    urls = db.Column(db.JSON, nullable=True)
    url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class Visual(db.Model):
    __tablename__ = 'visuals'
    __bind_key__ = 'chatbot_db'
    id = db.Column(db.String(255), primary_key=True)
    questions = db.Column(db.JSON, nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_type = db.Column(db.String(50), nullable=False, default='both')
    urls = db.Column(db.JSON, nullable=True)
    url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

class UserRule(db.Model):
    __tablename__ = 'user_rules'
    __bind_key__ = 'chatbot_db'
    id = db.Column(db.String(255), primary_key=True)
    category = db.Column(db.String(255), nullable=True)
    question = db.Column(db.Text, nullable=True)
    answer = db.Column(db.Text, nullable=True)
    user_type = db.Column(db.String(50), nullable=True, default='user')

class GuestRule(db.Model):
    __tablename__ = 'guest_rules'
    __bind_key__ = 'chatbot_db'
    id = db.Column(db.String(255), primary_key=True)
    category = db.Column(db.String(255), nullable=True)
    question = db.Column(db.Text, nullable=True)
    answer = db.Column(db.Text, nullable=True)
    user_type = db.Column(db.String(50), nullable=True, default='guest')
