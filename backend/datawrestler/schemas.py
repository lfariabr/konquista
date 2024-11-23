import graphene
from .lead_message_schema import LeadMessageQuery
from .appointments_schema import AppointQuery
from .lead_crm_schema import LeadCrmQuery

# Mesclando os dois schemas
class Query(LeadMessageQuery, AppointQuery, LeadCrmQuery, graphene.ObjectType):
    pass

# Definindo o schema principal
schema = graphene.Schema(query=Query)
