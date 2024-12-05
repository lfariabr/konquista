# appointments resolver
# this is where we get the data

import requests
import re
from ..models import GraphQLClient
from ..token_manager import graphql_api_url, graphql_api_token
import time
import random
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

client = GraphQLClient(graphql_api_url, graphql_api_token)

def fetch_appointments(start_date, end_date, max_retries=10, base_retry_delay=5):

    query = '''
    query ($filters: AppointmentFiltersInput, $pagination: PaginationInput) {
        fetchAppointments(filters: $filters, pagination: $pagination) {
            data {
                id
                status {
                    label
                }
                store {
                    name
                }
                customer {
                    id
                    name
                    telephones {
                        number
                    }
                }
                procedure {
                    name
                }
                startDate
            }
            meta {
                currentPage
                lastPage
            }
        }
    }
    '''
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {graphql_api_token}',
    }

    # Variáveis de paginação
    current_page = 1
    all_appointments = []

    # Create a session for connection pooling
    session = requests.Session()
    session.headers.update(headers)

    while True:
        retry_count = 0
        while retry_count < max_retries:
            try:
                # Simple fixed retry delay
                retry_delay = base_retry_delay
                
                variables = {
                    'filters': {
                        'startDateRange': {
                            'start': start_date,
                            'end': end_date,
                        },
                    },
                    'pagination': {
                        'currentPage': current_page,
                        'perPage': 200,  # Reduced from 500 to lower server load
                    },
                }

                response = session.post(
                    graphql_api_url,
                    json={'query': query,
                          'variables': variables},
                    timeout=30
                )

                if response.status_code in [502, 503, 504]:
                    retry_count += 1
                    if retry_count < max_retries:
                        error_body = response.text[:200]
                        logger.warning(f"Received {response.status_code}, body: {error_body}")
                        logger.info(f"Retrying in {retry_delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        # Create new session with fresh connection
                        session = requests.Session()
                        session.headers.update(headers)
                        continue
                    else:
                        logger.warning(f"Failed to fetch page {current_page} after {max_retries} attempts")
                        if len(all_appointments) > 0:
                            logger.info(f"Returning partial results with {len(all_appointments)} appointments")
                            break
                        else:
                            raise Exception("Failed to fetch any appointments")

                response.raise_for_status()
                result = response.json()

                # Verifica se há dados na resposta
                if 'data' in result and 'fetchAppointments' in result['data']:
                    appointments = result['data']['fetchAppointments']['data']
                    all_appointments.extend(appointments)

                    # Pega informações de paginação
                    current_page = result['data']['fetchAppointments']['meta']['currentPage']
                    last_page = result['data']['fetchAppointments']['meta']['lastPage']
                    
                    # Prints para depuração
                    print(f"Página {current_page} de {last_page}")
                    print(f"Fetching appointments between {start_date} - {end_date}")

                    # Fixed delay between requests for rate limiting
                    time.sleep(base_retry_delay)
                    
                    # Se estivermos na última página, saímos do loop
                    if current_page >= last_page:
                        return filter_and_clean_appointments(all_appointments)  # Return directly when we reach the last page
                    current_page += 1  # Passa para a próxima página
                    break  # Break the retry loop on success
                else:
                    raise Exception("Ops... 'data' or 'fetchAppointments' not found in response")

            except requests.Timeout:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Request timed out, retrying in {retry_delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to fetch page {current_page} after {max_retries} attempts, skipping...")
                    current_page += 1
                    break
                    
            except Exception as e:
                if retry_count < max_retries - 1:
                    retry_count += 1
                    print(f"Error occurred: {str(e)}, retrying in {retry_delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to fetch page {current_page} after {max_retries} attempts with error: {str(e)}")
                    raise
        
        if current_page > last_page:
            break

    # Filtra e limpa os appointments após coletar todos
    filtered_appointments = filter_and_clean_appointments(all_appointments)
    return filtered_appointments
    
  
def filter_and_clean_appointments(appointments):
    # Regex patterns to filter appointments
    regex_proced_avaliacao = r'AVALIAÇÃO'  # Regex pattern to match "AVALIAÇÃO"
    valid_status = {'Agendado', 'Atendido', 'Confirmado', 'Falta', 'Cancelado'}
    unidade_exclusiva = r'HOMA|PLÁSTICA'

    # Filter by status
    appointments_filtered = [
    appointment for appointment in appointments
    if 'status' in appointment and 'label' in appointment['status'] and appointment['status']['label'] in valid_status
]

    # Filter by procedure name
    appointments_filtered = [
        appointment for appointment in appointments_filtered
        if 'procedure' in appointment and 'name' in appointment['procedure'] and re.search(regex_proced_avaliacao, appointment['procedure']['name'], re.IGNORECASE)
    ]

    # Exclude specific stores
    appointments_filtered = [
        appointment for appointment in appointments_filtered
        if 'store' in appointment and 'name' in appointment['store'] and not re.search(unidade_exclusiva, appointment['store']['name'], re.IGNORECASE)
    ]

    # Clean phone data
    for appointment in appointments_filtered:
        if 'customer' in appointment and 'telephones' in appointment['customer']:
            telephones = appointment['customer']['telephones']
            cleaned_telephones = [tel['number'].strip() for tel in telephones if 'number' in tel]
            appointment['telephones'] = cleaned_telephones
        else:
            appointment['telephones'] = []

    return appointments_filtered

def appointments_to_check(filter_and_clean_appointments):
    pass
