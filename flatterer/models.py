from datetime import datetime, date, time, timedelta

from flatterer import db

from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """Describes a user."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(20))
    password = db.Column(db.String(100))
    admin = db.Column(db.Boolean)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def is_active(self):
        return True

    def get_id(self):
        return unicode(self.id)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __init__(self, username, name, password, admin=False):
        self.username = username
        self.name = name
        self.password = generate_password_hash(password)
        self.admin = admin


class Complimentee(db.Model):
    """Describes the reciever of a compliment."""
    __tablename__ = 'complimentee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)  # Change unique to false
    url = db.Column(db.String(50), unique=True)
    greeting = db.Column(db.String(1000))
    owner = db.Column(db.Integer)  # Id for user

    def __init__(self, name, url, owner, greeting=None):
        self.name = name
        self.url = url
        self.owner = owner
        self.greeting = greeting


class Theme(db.Model):
    """Describes special elements for pages generated for individuals."""
    __tablename__ = "themes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('complimentee.id'))
    # Can be local file paths or urls
    theme_path = db.Column(db.String(255))
    song_path = db.Column(db.String(255))

    complimentee = db.relationship('Complimentee', backref='theme')

    def __init__(self, user_id, theme_path=None, song_path=None):
        self.user_id = user_id
        self.theme_path = theme_path
        self.song_path = song_path


class Gender(db.Model):
    """Describes a gender."""
    __tablename__ = 'gender'
    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.String(50), unique=True)

    def __init__(self, gender):
        self.gender = gender

    def __repr__(self):
        return '<Gender %r>' % (self.gender)


class Compliment(db.Model):
    """Describes a compliment, who it belongs too, and who recieved it."""
    __tablename__ = 'compliments'
    id = db.Column(db.Integer, primary_key=True)
    compliment = db.Column(db.String(255))
    gender = db.Column(db.String(50), db.ForeignKey('gender.gender'))
    user_id = db.Column(db.Integer, db.ForeignKey('complimentee.id'))
    approved = db.Column(db.Boolean)
    user = db.relationship("Complimentee", backref=db.backref("compliments"))

    def __init__(self, compliment, gender=None, user_id=None, approved=False):
        self.compliment = compliment
        self.gender = gender
        self.user_id = user_id
        self.approved = approved

    def __repr__(self):
        return "<Compliment('%s')>" % (self.compliment)
