# Routes para integrar datawrestler no projeto
# e poder usar tudo isso em testes

from flask import Blueprint, jsonify
from flask_graphql import GraphQLView
from .schemas import schema
from .resolvers import get_leads_from_core, get_appointments, count_sent_messages_to_lead_phone, get_leads, data_wrestling
from datetime import datetime, timedelta

# Criando o Blueprint para o graphQL que construímos
datawrestler_blueprint = Blueprint('datawrestler', __name__)

# Configurando a rota para o acesso via browser
# Adicionando a inetrface GraphiQL
datawrestler_blueprint.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True
    )
)

# Se eu quiser chamar no na URL...
@datawrestler_blueprint.route('/run-datawrestler', methods=['GET'])
def run_datawrestler():
    # Definir o intervalo de datas
    start_date = datetime.now() - timedelta(days=0)
    end_date = datetime.now() + timedelta(days=0)
    
    # Puxar dados usando as funções auxiliares
    leads_landing, leads_whatsapp = get_leads_from_core()
    appointments_data = get_appointments(start_date, end_date)
    df_count_messages_by_phone = count_sent_messages_to_lead_phone()
    leads_data = get_leads(start_date, end_date)
    
    # Chamar a função de processamento dos dados
    leads_df = data_wrestling(leads_landing, leads_whatsapp, appointments_data, df_count_messages_by_phone, leads_data)

    # Retornar um status ou resultado da execução como JSON
    return jsonify({"status": "Success", "message": "Data wrestling completed", "total_leads": len(leads_df)})

# http://127.0.0.1:5000/datawrestler/graphql

# query {
#   allLeadsLandingPage {
#     id
#     name
#     phone
#     createdDate
#     store
#     tag
#   }
# }

# query {
#   allLeadsWhatsapp {
#     id
#     name
#     phone
#     createdDate
#     tag
#     source
#   }
# }

# query {
#   countMessagesByPhone {
#     phone
#     messageCount
#   }
# }

# query {
#   leads(startDate: "2024-09-21", endDate: "2024-09-21") {
#     name
#     phone
#     source
#     store
#   }
# }

# query {

#   appointments(startDate: "2024-09-21", endDate: "2024-09-21") {
#     id
#     status
#     procedure
#     startDate
#     store
#   }
# }