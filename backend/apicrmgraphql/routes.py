# graphql -> __init__.py

from flask_graphql import GraphQLView
from .schemas import appointments_schema, leads_schema # sales_schema
from flask import Blueprint

# For the fact we don't want to have circular import issues
# we'are going to crate blueprints for each schema
# so we can register routes without importing the app

apicrmgraphql_blueprint = Blueprint('apicrmgraphql', __name__)

# Registering appoint schema http://127.0.0.1:5000/apicrmgraphql/appoint_graphql
apicrmgraphql_blueprint.add_url_rule(
    '/appoint_graphql',  # <-- Adding the 'rule' argument here
    view_func=GraphQLView.as_view(
        'appoint_schema',
        schema=appointments_schema.schema,
        graphiql=True,
    )
)

# Registering lead schema http://127.0.0.1:5000/apicrmgraphql/lead_graphql?
apicrmgraphql_blueprint.add_url_rule(
    '/lead_graphql',
    view_func=GraphQLView.as_view(
        'lead_schema',
        schema=leads_schema.schema,
        graphiql=True
    )
)

# Later on, when it's time to do leads, I just change appoint_graphql to leads_graphql
# and appoint_schemma to lead_schema