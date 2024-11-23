# lead resolver
# this is where we get the data

import requests
import re
import json
import time
import logging
from ..models import GraphQLClient
from ..token_manager import graphql_api_url, graphql_api_token
from backend.apicrmgraphql.dicts import dic_store_ident, dic_region_ident, stores, region_map
from requests.exceptions import RequestException
from datetime import datetime, timedelta


client = GraphQLClient(graphql_api_url, graphql_api_token)
logging.basicConfig(level=logging.DEBUG)

def query_leads(current_page, start_date, end_date, token):
    url = 'https://open-api.eprocorpo.com.br/graphql'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    payload = {
        'query': '''query ($filters: LeadFiltersInput, $pagination: PaginationInput) {
                    fetchLeads(filters: $filters, pagination: $pagination) {
                        data {
                            createdAt
                            id
                            source {
                                title
                            }
                            store {
                                name
                            }
                            status {
                                label
                            }
                            customer {
                                id
                                name
                            }
                            name
                            telephone
                            email
                        }
                        meta {
                            currentPage
                            lastPage
                        }
                    }
                }''',
        'variables': {
            'filters': {
                'createdAtRange': {
                    'start': start_date,
                    'end': end_date,
                },
            },
            'pagination': {
                'currentPage': current_page,
                'perPage': 200,  # Reduce the number of items per page
            },
        },
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def fetch_all_leads(start_date, end_date, token):
    current_page = 1
    all_leads = []

    while True:
        try:
            data = query_leads(current_page, start_date, end_date, token)
            leads_data = data['data']['fetchLeads']['data']
            all_leads.extend(leads_data)

            meta = data['data']['fetchLeads']['meta']
            if current_page >= meta['lastPage']:
                break
            
            # Prints para depuração
            last_page = data['data']['fetchLeads']['meta']['lastPage']

            print(f"Página {current_page} de {last_page}")
            print(f"Fetching leads between {start_date} - {end_date}")

            current_page += 1
            time.sleep(5)  # Small Delay
                        
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")
            time.sleep(30)  # Wait longer if an error occurs before retrying
            continue  # Retry the loop

    return all_leads

def fetch_leads(start_date, end_date):
    return fetch_all_leads(start_date, end_date, graphql_api_token)

# Example filter and cleaning function
def filter_and_clean_leads(leads):
    store_exclusive = r'HOMA|PLÁSTICA|PRAIA GRANDE'

    # Exclude specific stores and clean phone data
    leads_filtered = [
        lead for lead in leads
        if 'store' in lead and 'name' in lead['store'] and not re.search(store_exclusive, lead['store']['name'], re.IGNORECASE)
    ]

    for lead in leads_filtered:
        if 'phone' in lead:
            cleaned_phone = re.sub(r'\D', '', lead['phone'])
            lead['phone'] = cleaned_phone.strip()

        if 'email' in lead:
            lead['email'] = lead['email'].strip()

    return leads_filtered
    
    # return fetch_leads(start_date, end_date)

def create_lead(name, telephone, email, message, unidade, region):

    source_identifier = "662bf789-d04c-4ccf-8424-26b92595060c"

    region_identifier = dic_region_ident[region]
    store_identifier = dic_store_ident[unidade]

    telephone = str(telephone)

    query = """
    mutation ($data: CreateLeadInput!) {
        createLead(
            data: $data
        ) {
            email
            name
            message
            region {
                identifier
            }
            source {
                identifier
            }
            store {
                identifier
            }
            telephone
        }
    }
    """

    variables = {
        "data": {
            "email": email,
            "message": message,
            "name": name,
            "regionIdentifier": region_identifier,
            "sourceIdentifier": source_identifier,
            "storeIdentifier": store_identifier,
            "telephone": telephone
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {graphql_api_token}'
    }

    response = requests.post(graphql_api_url, json={'query': query, 'variables': variables}, headers=headers)
    response_data = response.json()

    if response.status_code == 200:
        print("Lead created successfully:", response_data)
    else:
        print("Failed to create lead:", response_data)

    return response_data