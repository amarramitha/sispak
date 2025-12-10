from app import app
from models import db, Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    username = "admin"
    password = "admin123"

    hashed = generate_password_hash(password)

    admin = Admin(username=username, password=hashed)
    db.session.add(admin)
    db.session.commit()

    print("Admin berhasil ditambahkan!")
