import requests
from ..config import db
from datetime import datetime
from sqlalchemy.orm import relationship
from ..users.models import UserPhone, MessageList
from ..leadgen.models import LeadWhatsapp, LeadLandingPage
from ..users.models import User

class MessageLog(db.Model):
    __tablename__ = 'message_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Message List
    message_id = db.Column(db.Integer, db.ForeignKey('messagelist.id'))
    message = db.relationship("MessageList")
    message_title = db.Column(db.String(64))
    
    # UserPhone
    sender_phone_id = db.Column(db.Integer, db.ForeignKey('userphones.id'))
    sender_phone = db.relationship("UserPhone")
    sender_phone_number = db.Column(db.String(20))

    # TODO: only whatsapp LeadWhatsapp
    lead_phone_id = db.Column(db.Integer, db.ForeignKey('leadwhatsapp.id'))
    lead_phone = db.relationship("LeadWhatsapp")
    lead_phone_number = db.Column(db.String(20))
    source = db.Column(db.String(50))
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)  # Data de envio
    status = db.Column(db.String(50))  # e.g., 'sent', 'failed'
    message_text = db.Column(db.String(1000))  # Campo para armazenar o texto da mensagem

    # Adding user relationship to Message Logs
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User", backref=db.backref("message_logs", lazy=True))

    def __init__(self, user_id, message_title, sender_phone_id, sender_phone_number, source, lead_phone_id, lead_phone_number, status, message_text=None, date_sent=datetime.utcnow()):

        self.message_title = message_title
        self.user_id = user_id
        self.sender_phone_id = sender_phone_id
        self.sender_phone_number = sender_phone_number
        self.source = source
        self.lead_phone_id = lead_phone_id
        self.lead_phone_number = lead_phone_number
        self.status = status
        self.message_text = message_text
        self.date_sent = date_sent
    

    def __repr__(self):
        return f"MessageLog {self.message_text}, MessageTitle {self.message_title}, SenderPhone {self.sender_phone_id}, SenderPhoneNb: {self.sender_phone_number}, Source {self.source}, LeadPhoneID {self.lead_phone_id}, LeadPhone {self.lead_phone_number}, Status {self.status}"