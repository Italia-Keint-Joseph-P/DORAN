from models import EmailDirectory
from extensions import db

def get_all_emails():
    emails = EmailDirectory.query.all()
    return [{"id": e.id, "school": e.school, "email": e.email} for e in emails]

def add_email(school, email):
    try:
        new_email = EmailDirectory(school=school, email=email)
        db.session.add(new_email)
        db.session.commit()
        return new_email.id
    except Exception as e:
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
        db.session.rollback()
        raise e
