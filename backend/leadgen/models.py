from ..config import db
from datetime import datetime
from ..users.models import User

class LeadLandingPage(db.Model):

    __tablename__ = 'leadlandingpage'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    phone = db.Column(db.String(20))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    tag = db.Column(db.Text)
    source = db.Column(db.Text)
    store = db.Column(db.Text)
    region = db.Column(db.Text)
    tags = db.Column(db.Text)

    # Adding user relationship to Lead Landing Page
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User", backref=db.backref("leadlandingpage", lazy=True))

    def __init__(self, user_id, phone, name, created_date=None, tag='', source='unknown', store='CENTRAL', region='São Paulo', tags='SEM TAGS'):
        self.phone = phone
        self.name = name
        self.user_id = user_id
        self.created_date = created_date or datetime.utcnow()  # Usar data atual se não for fornecida
        self.tag = tag
        self.source = source
        self.store = store
        self.region = region
        self.tags = tags

    def __repr__(self):
        return '<Lead %r>' % self.name

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'created_date': self.created_date.strftime('%Y-%m-%d %H:%M:%S') if self.created_date else None,
            'tag': self.tag,
            'source': self.source,
            'store': self.store,
            'region': self.region,
            'tags': self.tags
        }
    
class LeadWhatsapp(db.Model):

    __tablename__ = 'leadwhatsapp'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)  # Data de criação com valor padrão
    tag = db.Column(db.String(64), nullable=True, default='')  # Tag opcional com valor padrão vazio
    source = db.Column(db.String(64), nullable=True, default='unknown')  # Fonte com valor padrão "unknown"
    store = db.Column(db.String(64), nullable=True, default='CENTRAL')  # Loja com valor padrão vazio
    region = db.Column(db.String(64), nullable=True, default='São Paulo')  # Região com valor padrão vazio
    tags = db.Column(db.String(64), nullable=True, default='SEM TAGS')  # Tag opcional com valor padrão vazio

    # Adding user relationship to LeadWhatsapp
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User", backref=db.backref("leadwhatsapp", lazy=True))
    
    def __init__(self, user_id, phone, name, created_date=None, tag='', source='unknown', store='CENTRAL', region='São Paulo', tags='SEM TAGS'):
        self.phone = phone
        self.user_id = user_id
        self.name = name
        self.created_date = created_date or datetime.utcnow()  # Usar data atual se não for fornecida
        self.tag = tag
        self.source = source
        self.store = store
        self.region = region
        self.tags = tags

    def __repr__(self):
        return '<Lead %r>' % self.name

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'created_date': self.created_date.strftime('%Y-%m-%d %H:%M:%S') if self.created_date else None,
            'tag': self.tag,
            'source': self.source,
            'store': self.store,
            'region': self.region,
            'tags': self.tags
        }