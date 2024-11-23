import graphene
from ..config import db
from .models import MessageLog as MessageLogModel, MessageList as MessageListModel
from .resolvers import message_handler

# GraphQL Object Type para MessageList
class MessageType(graphene.ObjectType):
    id = graphene.Int()
    title = graphene.String()
    text = graphene.String()
    content_type = graphene.String()

# GraphQL Object Type para MessageLog
class MessageLogType(graphene.ObjectType):
    id = graphene.Int()
    lead_phone = graphene.String()  # Alterado para lead_phone
    sender_phone_id = graphene.Int()
    status = graphene.String()
    date_sent = graphene.String()

# Definir as Queries para consultar mensagens e logs
class Query(graphene.ObjectType):
    all_messages = graphene.List(MessageType)
    message_logs = graphene.List(MessageLogType)

    # Resolver com todas as mensagens disponíveis
    def resolve_all_messages(self, info):
        return db.session.query(MessageListModel).all()

    # Resolver com logs de mensagens enviadas
    def resolve_message_logs(self, info):
        return db.session.query(MessageLogModel).all()

# Mutation para enviar mensagem
class SendMessage(graphene.Mutation):
    class Arguments:
        leadPhone = graphene.String(required=True)  # Telefone do lead (cliente)
        messageId = graphene.Int(required=True)
        senderPhoneId = graphene.Int(required=True)  # ID do telefone do disparador

    status = graphene.String()

    def mutate(self, info, leadPhone, messageId, senderPhoneId):
        # Usar a função message_handler do resolvers para enviar a mensagem e registrar o log
        response = message_handler(leadPhone, messageId, senderPhoneId)

        # Retornar o status da operação
        return SendMessage(status=response.get('success', 'failed'))

# Definir Schema e Mutations
class Mutation(graphene.ObjectType):
    sendMessage = SendMessage.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)