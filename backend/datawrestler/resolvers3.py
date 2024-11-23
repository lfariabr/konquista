###########################
# 1. Libs and Logging Config
###########################

import os
import json
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import sys
import logging
from backend.config import db, app
from backend.users.models import UserPhone
from backend.leadgen.models import LeadLandingPage, LeadWhatsapp
from backend.apisocialhub.models import MessageLog, MessageList
from backend.apisocialhub.resolvers import send_message, send_message_with_file, cherry_pick_message
from backend.apicrmgraphql.resolvers.appointments_resolver import fetch_appointments, filter_and_clean_appointments
from backend.apicrmgraphql.resolvers.leads_resolver import fetch_all_leads, filter_and_clean_leads, create_lead
from sqlalchemy import desc
from sqlalchemy.sql import text

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("datawrestler.log")
    ]
)

logger = logging.getLogger(__name__)

###########################
# 2. DB Keep Alive
###########################
def keep_alive():
    try:
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        logger.info("Pinged the database to keep the connection alive.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Keep-alive failed: {e}")

#########################
# 3. Normalize Phone Support
###########################
def normalize_phone(phone):
    return ''.join(filter(str.isdigit, phone))  # Retain only numeric characters

#########################
# 4. Fetch data from Core
###########################
def fetch_leads_from_core(phone=None, offset=213, limit=120):
    if phone:
        leads_landing = LeadLandingPage.query.filter(LeadLandingPage.phone == phone)
        leads_whatsapp = LeadWhatsapp.query.filter(LeadWhatsapp.phone == phone)
    else:
        leads_landing = LeadLandingPage.query
        leads_whatsapp = LeadWhatsapp.query

    leads_landing = leads_landing.order_by(LeadLandingPage.id.desc()).limit(1).all()
    leads_whatsapp = leads_whatsapp.order_by(LeadWhatsapp.id.desc()).offset(offset).limit(limit).all()

    logger.info(f"Got {len(leads_landing)} leads from landing pages.")
    logger.info(f"Got {len(leads_whatsapp)} leads from WhatsApp.")

    return leads_landing, leads_whatsapp

#########################
# 5. Conunt Sent Messages
###########################
def count_sent_messages_to_lead_phone():
    try:
        message_counts = db.session.query(
            MessageLog.lead_phone_number, db.func.count(MessageLog.id)
        ).group_by(MessageLog.lead_phone_number).all()

        message_counts_dict = dict(message_counts)
        logger.info("Message counts retrieved successfully.")
        return message_counts_dict
    except Exception as e:
        logger.error(f"Error counting sent messages: {e}")
        return {}
    
##########################
# 6. Fetch Leads & Appointments from GraphQL
###########################

def fetch_appointments_data(start_date, end_date):
    try:
        appointments = fetch_appointments(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        logger.info(f"Fetched {len(appointments)} appointments from GraphQL.")
        return appointments
    except Exception as e:
        logger.error(f"Error fetching appointments: {e}")
        return []

def fetch_leads_data(start_date, end_date):
    try:
        leads = fetch_all_leads(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), os.getenv('GRAPHQL_API_TOKEN'))
        logger.info(f"Fetched {len(leads)} leads from GraphQL.")
        return leads
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        return []
    
#########################
# 7. Fetch Messages and Token
###########################
def get_messages():
    messages_dic = {}
    try:
        messages = MessageList.query.all()
        for item in messages:
            messages_dic[item.title] = {
                'text': item.text,
                'interval': item.interval,
                'file': item.file
            }
        logger.info(f"Fetched {len(messages)} messages from MessageList.")
        return messages_dic
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return {}

def get_phone_tokens():
    phones_dic = {}
    try:
        phone_list = UserPhone.query.all()
        for phone in phone_list:
            phones_dic[phone.phone_number] = {
                'id': phone.id,
                'phone_number': phone.phone_number,
                'phone_token': phone.phone_token,
                'phone_description': phone.phone_description
            }
        logger.info(f"Fetched tokens for {len(phones_dic)} phone numbers.")
        return phones_dic
    except Exception as e:
        logger.error(f"Error fetching phone tokens: {e}")
        return {}
    
########################
# 8. Data Processing 
###########################
def process_data(leads_landing, leads_whatsapp, appointments, message_counts, leads):
    df_leads_receive_message = leads_whatsapp + leads_landing
    sent_messages_phones = message_counts  # Already a dictionary

    leads_phones = {lead['telephone'] for lead in leads if lead['telephone']}
    appointment_phones = {appointment['telephones'][0] for appointment in appointments if appointment['telephones']}

    leads_df = []
    for lead in df_leads_receive_message:
        phone = lead.phone.strip()
        logger.debug(f"Processing phone: {phone}")
        sent_message_count = sent_messages_phones.get(phone, 0)
        logger.debug(f"Message count for this phone: {sent_message_count}")

        has_appointment = phone in appointment_phones
        has_lead = phone in leads_phones

        store = getattr(lead, 'store', 'CENTRAL')
        region = getattr(lead, 'region', 'São Paulo')
        tags = getattr(lead, 'tags', 'SEM TAGS')

        leads_df.append({
            'phone': phone,
            'created_date': lead.created_date,
            'source': lead.source,
            'name': lead.name,
            'tag': lead.tag,
            'sent_message_count': sent_message_count,
            'has_appointment': has_appointment,
            'has_lead': has_lead,
            'store': store,
            'region': region,
            'tags': tags,
        })

    df = pd.DataFrame(leads_df)
    logger.info(f"Processed data into DataFrame with {len(df)} records.")
    return df

#########################
# 9. Message Sending Function
###########################
def send_messages(leads_df, messages_dic, phones_dic):
    for index, cliente in leads_df.iterrows():
        phone = cliente['phone']
        contador = cliente['sent_message_count']
        source = cliente['source']
        has_appointment = cliente['has_appointment']
        has_lead = cliente['has_lead']
        store = cliente['store']
        region = cliente['region']
        tags = cliente['tags']

        name = cliente['name']
        tag = cliente['tag']
        dias_depois_da_conversa = (datetime.now() - cliente['created_date']).days

        message_key = None

        logger.debug("Ready to oblige conditions (has appointment | lead && src whatsapp)!")

        # Process leads without appointments, leads and source Whatsapp
        if not has_appointment and not has_lead and source == "Whatsapp":

            if tag == "Botox":
                campaign = "Botox"
                phone_description = "Botox"

            elif tag == "Preenchimento":
                campaign = "Preenchimento"
                phone_description = "Preenchimento"
            else:
                logger.warning(f"Ops... {tag} not mapped.")
                continue

            # Defining message based on conditions
            if contador == 0:
                message_key = f"{campaign.lower()}d1"
            elif contador == 1:
                message_key = f"{campaign.lower()}d2"
            elif contador == 2:
                message_key = f"{campaign.lower()}d3"

            # Creating lead in CRM
            elif contador == 3:
                email = "campanha@whatsapp.com"
                message = f"Lead da campanha {campaign}"
                response = create_lead(name, phone, email, message, store, region)
                # Correctly handle response checking if createdLead exists
                if 'data' in response and 'createLead' in response['data']:
                    logger.info(f"Lead {phone} criado com sucesso!")

                try:
                    # Re-fetch the lead to ensure it's in the database
                    lead = db.session.query(LeadWhatsapp).filter_by(phone=cliente['phone']).first()
                    if lead is None:
                        logger.error(f"Failed to find lead with phone {cliente['phone']}")
                        continue  # Skip logging if no lead found
                    log = MessageLog(
                        sender_phone_id=None,  # No sender phone since it's lead creation
                        sender_phone_number="N/A",  # Assuming this is allowed in your schema
                        source="CRM",
                        lead_phone_id=lead.id if lead else None,
                        lead_phone_number=cliente['phone'],
                        status="lead_created",
                        message_title=f"Lead criado para {campaign}",
                        message_text=message,
                        date_sent=datetime.now()
                    )
                    db.session.add(log)
                    db.session.commit()
                    logger.info(f"Logged lead creation for {phone}.")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Failed to log lead creation. Error: {e}")
                # Adding the timer after lead creation
                logger.info("Waiting 1 minute before processing the next lead...")
                time.sleep(60)
                continue  # Skip message sending...

            # Extra additions    
            elif contador == 4 and dias_depois_da_conversa >= 7:
                message_key = "pesquisad7"
            elif contador == 5 and dias_depois_da_conversa >= 30:
                message_key = "botox30d"
            else:
                logger.warning(f"Contador {contador} não mapeado para uma mensagem.")
                continue

            # Fetching appropriate message and file from dic
            mensagem = messages_dic.get(message_key, {}).get("text")
            file = messages_dic.get(message_key, {}).get("file")
            if not mensagem:
                logger.warning(f"Mensagem para o contador {contador} não encontrada. Mensagem: {message_key}")
                continue

            # Get the sender phone data based on phone descr
            sender_phone_data = next(
                (data for data in phones_dic.values() if data.get('phone_description') == phone_description),
                None
            )
            if not sender_phone_data:
                logger.error(f"Erro ao buscar phone_description: {phone_description}")
                continue

            # Fetching appropriate phone token
            api_token = sender_phone_data.get("phone_token")
            if not api_token:
                logger.error(f"Erro ao buscar phone_token for sender: {sender_phone_data}")
                continue

            ## Sending the message with cherry pick update
            try:
                if file:
                    response = cherry_pick_message(phone, mensagem, api_token, file)
                    logger.debug("Sent message with file.")
                else:
                    response = cherry_pick_message(phone, mensagem, api_token)
                    logger.debug("Sent message without file.")
                time.sleep(10)
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                continue

            # Handling response and logging
            status_envio = response.get("success", False)

            if status_envio:
                try:
                    lead = db.session.query(LeadWhatsapp).filter_by(phone=cliente['phone']).first()
                    if not lead:
                        logger.error(f"Failed to find lead after sending message to {phone}.")
                        continue
                    log = MessageLog(
                        sender_phone_id=sender_phone_data['id'],
                        sender_phone_number=sender_phone_data['phone_number'],  # Now logging the number
                        source="Whatsapp",
                        lead_phone_id=lead.id,
                        lead_phone_number=cliente['phone'],
                        status="sent",
                        message_title=message_key,  # Add this if it's the message ID
                        message_text=mensagem,
                        date_sent=datetime.now()
                    )
                    db.session.add(log)
                    db.session.commit()
                    logger.info(f"Sent and logged message '{message_key}' to: {phone}")
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Failed to log sent message: {e}")

##################################
# Main Function: Data Wrestling
##################################

def run_data_wrestling():
    try:
        load_dotenv()  # Load environment variables

        logger.info("Starting DataWrestling process.")

        # Define date range
        start_date = datetime.now() - timedelta(days=10)
        end_date = datetime.now() + timedelta(days=10)
        logger.info(f"Start date: {start_date}, End date: {end_date}")

        # DATA GATHERING
        logger.info("Loading leads from core.")
        keep_alive()
        leads_landing, leads_whatsapp = fetch_leads_from_core()

        logger.info("Counting sent messages.")
        keep_alive()
        message_counts = count_sent_messages_to_lead_phone()

        logger.info("Loading leads from GraphQL.")
        keep_alive()
        leads_data = fetch_leads_data(start_date, end_date)

        logger.info("Loading appointments from GraphQL.")
        keep_alive()
        appointments_data = fetch_appointments_data(start_date, end_date)

        # DATA PROCESSING
        logger.info("Processing data.")
        leads_df = process_data(leads_landing, leads_whatsapp, appointments_data, message_counts, leads_data)

        # DATA DELIVERY
        logger.info("Converting DataFrame to JSON.")
        leads_list = leads_df.to_dict(orient='records')
        leads_json = json.dumps(leads_list, default=str, ensure_ascii=False, indent=4)
        logger.debug(f"Leads JSON: {leads_json}")

        logger.info("Fetching messages and phone tokens.")
        keep_alive()
        messages_dic = get_messages()
        phones_dic = get_phone_tokens()

        logger.info("Sending messages based on processed leads.")
        keep_alive()
        send_messages(leads_df, messages_dic, phones_dic)

        logger.info("DataWrestling process completed successfully.")

    except Exception as e:
        logger.error(f"Error while running DataWrestling: {e}")