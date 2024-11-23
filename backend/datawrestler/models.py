from datetime import datetime
from ..config import db

class LeadsHandler(db.Model):
    __tablename__ = 'leadshandler'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone = db.Column(db.String(20), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(64), nullable=True, default='unknown')
    name = db.Column(db.String(255), nullable=True, default='')
    tag = db.Column(db.String(64), nullable=True, default='')
    sent_message_count = db.Column(db.Integer, default=0)
    has_appointment = db.Column(db.Boolean, default=False)
    has_lead = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_leadshandler_user_id'), nullable=True)
    user = db.relationship("User", backref=db.backref("leads_handler", lazy=True))

    def __init__(self, phone, created_date=None, source='unknown', name='', tag='', 
                 sent_message_count=0, has_appointment=False, has_lead=False, user_id=None):
        self.phone = phone
        self.created_date = created_date or datetime.utcnow()
        self.source = source
        self.name = name
        self.tag = tag
        self.sent_message_count = sent_message_count
        self.has_appointment = has_appointment
        self.has_lead = has_lead
        self.user_id = user_id

    def to_json(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'created_date': self.created_date.strftime('%Y-%m-%d %H:%M:%S'),
            'source': self.source,
            'name': self.name,
            'tag': self.tag,
            'sent_message_count': self.sent_message_count,
            'has_appointment': self.has_appointment,
            'has_lead': self.has_lead,
            'user_id': self.user_id
        }