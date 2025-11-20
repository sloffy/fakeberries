from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash
from datetime import datetime
from decimal import Decimal
from flask import current_app
import os

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(120), nullable=False, default='Администратор')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='catalog')  # catalog | basket
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f'<Product {self.name}>'

    def price_as_decimal(self) -> Decimal:
        return Decimal(self.price or 0)

    def delete_image(self) -> None:
        filename = self.image_filename
        if not filename:
            return
        upload_dir = None
        try:
            upload_dir = current_app.config.get('UPLOAD_FOLDER')
        except Exception:
            upload_dir = None
        file_path = os.path.join(upload_dir or 'instance/uploads', filename)
        if os.path.exists(file_path):
            os.remove(file_path)


def create_default_admin() -> None:
    """Создаёт единственного пользователя admin, если он отсутствует."""
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', display_name='Администратор FakeBerries')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()