# leads schema 
# defining the format of the query and how it will be called upon

import graphene
from ..resolvers.leads_resolver import fetch_leads, fetch_all_leads, filter_and_clean_leads
import logging

class LeadType(graphene.ObjectType):
    id = graphene.String()
    name = graphene.String()
    email = graphene.String()
    phone = graphene.String()
    source = graphene.String()
    store = graphene.String()
    date = graphene.String()

class LeadQuery(graphene.ObjectType):
    leads = graphene.List(
        LeadType, start_date=graphene.String(required=True),
        end_date=graphene.String(required=True)
    )

    def resolve_leads(self, info, start_date, end_date):
        leads = filter_and_clean_leads(fetch_leads(start_date, end_date))  # Certificando que a função fetch_leads é chamada e então os leads são filtrados e limpos.
        logging.debug(f"Fetched leads in resolver: {leads}")

        leads_list = []

        for data_row in leads:
            formatted_row = {
                'createdAt': data_row.get('createdAt'),
                'id': data_row.get('id'),
                'source': data_row.get('source', {}).get('title'),
                'store': data_row.get('store', {}).get('name') if data_row.get('store') else None,
                'status': data_row.get('status', {}).get('label'),
                'customer_id': data_row.get('customer', {}).get('id') if data_row.get('customer') else None,
                'customer_name': data_row.get('customer', {}).get('name') if data_row.get('customer') else None,
                'telephone': data_row.get('telephone'),
                'email': data_row.get('email'),
                'name': data_row.get('name'),
            }
            leads_list.append(formatted_row)

        # Create LeadType instances from the formatted data
        return [
            LeadType(
                id=lead.get('id', ''),
                name=lead.get('customer_name') or lead.get('name', ''),
                email=lead.get('email', ''),
                phone=lead.get('telephone', ''),
                source=lead.get('source', ''),
                store=lead.get('store', ''),
                date=lead.get('createdAt', '')
            )
            for lead in leads_list  # Correção: Certificar que estamos iterando sobre leads_list.
        ]

# Defining the schema
schema = graphene.Schema(query=LeadQuery)