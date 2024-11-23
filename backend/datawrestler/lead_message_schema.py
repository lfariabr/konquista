import graphene
from ..config import db
from ..leadgen.models import LeadLandingPage, LeadWhatsapp
from ..apisocialhub.models import MessageLog

# Object Types for Leads
class LeadLandingPageType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    phone = graphene.String()
    created_date = graphene.String()
    store = graphene.String()
    tag = graphene.String()

class LeadWhatsappType(graphene.ObjectType):
    id = graphene.Int()
    name = graphene.String()
    phone = graphene.String()
    created_date = graphene.String()
    tag = graphene.String()
    source = graphene.String()

# Object Type for MessageLog Count
class MessageLogCountType(graphene.ObjectType):
    phone = graphene.String()
    message_count = graphene.Int()

# Queries for getting leads and message logs
class LeadMessageQuery(graphene.ObjectType):
    all_leads_landing_page = graphene.List(LeadLandingPageType)
    all_leads_whatsapp = graphene.List(LeadWhatsappType)
    count_messages_by_phone = graphene.List(MessageLogCountType)

    # Resolver para buscar todos os leads do LandingPage
    def resolve_all_leads_landing_page(self, info):
        return LeadLandingPage.query.all()

    # Resolver para buscar todos os leads do Whatsapp
    def resolve_all_leads_whatsapp(self, info):
        return LeadWhatsapp.query.all()

    # Resolver para contar as mensagens enviadas para cada lead por telefone
    def resolve_count_messages_by_phone(self, info):
        return db.session.query(
            LeadWhatsapp.phone.label('phone'),
            db.func.count(MessageLog.id).label('message_count')
        ).join(
            MessageLog, LeadWhatsapp.id == MessageLog.lead_phone_id
        ).group_by(LeadWhatsapp.phone).all()

# Definir Schema?
# schema = graphene.Schema(query=LeadMessageQuery)