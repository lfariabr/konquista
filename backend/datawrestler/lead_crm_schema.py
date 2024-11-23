import graphene
from ..config import db
from ..apicrmgraphql.resolvers.leads_resolver import fetch_leads, fetch_leads, filter_and_clean_leads
from ..apicrmgraphql.schemas.leads_schema import LeadType

class LeadCrmQuery(graphene.ObjectType):

    leads = graphene.List(
        LeadType, start_date=graphene.String(required=True),
        end_date=graphene.String(required=True)
    )

    def resolve_leads(self, info, start_date, end_date):
        # Chamando a função fetch_leads com os parâmetros start/end date
        leads_filtered = filter_and_clean_leads(fetch_leads(start_date, end_date))
        return leads_filtered