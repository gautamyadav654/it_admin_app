from flask_sqlalchemy import SQLAlchemy
from models import db

def init_app(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    return db