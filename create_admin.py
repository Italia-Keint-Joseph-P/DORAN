from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = Admin.query.filter_by(email='admin@wvsu.edu.ph').first()
    if not admin:
        admin = Admin(email='admin@wvsu.edu.ph')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin created")
    else:
        print("Admin already exists")
