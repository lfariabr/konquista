# Routes para integrar graphql no projeto
# e poder usar tudo isso em testes

from flask import Blueprint
from flask_graphql import GraphQLView
from .schemas import schema

# Criando o Blueprint para o graphQL que construímos
apisocialhub_blueprint = Blueprint('apisocialhub', __name__)

# Configurando a rota para o acesso via browser
# Adicionando a inetrface GraphiQL
apisocialhub_blueprint.add_url_rule(
    '/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=schema,
        graphiql=True
    )
)

