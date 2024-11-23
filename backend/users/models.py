from ..config import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(db.Model,UserMixin):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(256))
    profile_image = db.Column(db.String(64), nullable=True, default='default_profile.jpg')

    # # Relações inversas
    # leadlandingpages = db.relationship('LeadLandingPage', backref='user', lazy='dynamic')
    # userphones = db.relationship('UserPhone', backref='user', lazy='dynamic')
    # messagelist = db.relationship('MessageList', backref='user', lazy='dynamic')
    # message_logs = db.relationship('MessageLog', backref='user', lazy='dynamic')

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password_hash = generate_password_hash(password)
    
    def check_password(self,password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"Username {self.username}"

class UserPhone(db.Model):

    __tablename__ = 'userphones'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    phone_number = db.Column(db.String(20))
    phone_token = db.Column(db.String(256))
    phone_description = db.Column(db.String(256))  # Novo campo adicionado

    # Foreign key linking to User model
    # This establishes that each UserPhone entry is linked to a specific user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship back to the User model
    user = db.relationship("User", backref=db.backref("userphones", lazy=True))
    # Allows Flask-SQLAlchemy to automatically provide access to all phones associated with an User
    # So we when querying a user, we can access user.userphones

    # Relationship back to the User model (without backref for multiple phones)
    # user = db.relationship('User', uselist=False)  # uselist=False to enforce 1-to-1
    
    def __init__(self, user_id, phone_number, phone_token, phone_description=None):
        self.user_id = user_id
        self.phone_number = phone_number
        self.phone_token = phone_token
        self.phone_description = phone_description  # Novo campo no init
    
    def __repr__(self):
        return f"Phone {self.phone_number}, Token {self.phone_token}, Phone_description {self.phone_description}"

class MessageList(db.Model):

    __tablename__ = 'messagelist'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    text = db.Column(db.Text)
    interval = db.Column(db.Integer) # days or hours between messages
    file = db.Column(db.String(256)) # photo, video,ls migrations/versions/ audio, etc

    # Foreign key linking to User model
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship back to the User model
    user = db.relationship("User", backref=db.backref("messagelist", lazy=True))
    
    # Método para converter a instância em um dicionário
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'text': self.text,
            'interval': self.interval,
            'file': self.file
        }

    def __repr__(self):
        return f"Title {self.title}, Text {self.text}, Interval {self.interval}, File {self.file}"

