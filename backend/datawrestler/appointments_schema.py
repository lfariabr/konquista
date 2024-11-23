import graphene
from ..apicrmgraphql.resolvers.appointments_resolver import fetch_appointments
from ..apicrmgraphql.schemas.appointments_schema import AppointmentType

class AppointQuery(graphene.ObjectType):

    appointments = graphene.List(
        AppointmentType, start_date=graphene.String(required=True),
        end_date=graphene.String(required=True)
    )

    def resolve_appointments(self, info, start_date, end_date):
        # Chamando a função fetch_appointments com os parâmetros start/end date
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