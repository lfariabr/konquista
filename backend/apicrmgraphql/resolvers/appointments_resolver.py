# appointments resolver
# this is where we get the data

import requests
import re
from ..models import GraphQLClient
from ..token_manager import graphql_api_url, graphql_api_token

client = GraphQLClient(graphql_api_url, graphql_api_token)

def fetch_appointments(start_date, end_date):

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

    while True:
        variables = {
            'filters': {
                'startDateRange': {
                    'start': start_date,
                    'end': end_date,
                },
            },
            'pagination': {
                'currentPage': current_page,
                'perPage': 1000,
            },
        }

        try:
            response = requests.post(
                graphql_api_url,
                json={'query': query,
                      'variables': variables},
                headers=headers
            )

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

                # Se estivermos na última página, saímos do loop
                if current_page >= last_page:
                    break
                else:
                    current_page += 1  # Passa para a próxima página
            else:
                raise Exception("Ops... 'data' or 'fetchAppointments' not found in response")

        except Exception as e:
            raise Exception(f"Ops... got an error: {str(e)}")

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
