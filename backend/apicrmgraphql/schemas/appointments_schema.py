# appointments schema 
# defining the format of the query and how it will be called upon

import graphene
from ..resolvers.appointments_resolver import fetch_appointments

class AppointmentType(graphene.ObjectType):
    id = graphene.String()
    status = graphene.String()
    store = graphene.String()
    customer = graphene.String()
    procedure = graphene.String()
    startDate = graphene.String()

class AppointQuery(graphene.ObjectType):
    appointments = graphene.List(
        AppointmentType, start_date=graphene.String(required=True),
        end_date=graphene.String(required=True)
    )

    def resolve_appointments(self, info, start_date, end_date):
        # Chamando a funão fetch_appointments com os parametros start/end date
        appointments = fetch_appointments(start_date, end_date)
        return [
            AppointmentType(
                id=appointment['id'],
                status=appointment['status']['label'],
                store=appointment['store']['name'],
                customer=appointment['customer']['name'],
                procedure=appointment['procedure']['name'],
                startDate=appointment['startDate']
            )
            for appointment in appointments
        ]

# Defining the schema
schema = graphene.Schema(query=AppointQuery)