from models import EmailDirectory
from extensions import db
from app import app

with app.app_context():
    emails = EmailDirectory.query.all()
    print('Number of emails:', len(emails))
    for e in emails:
        print(f'ID: {e.id}, School: {e.school}, Email: {e.email}')
