import os
import json
import pandas as pd
import time
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
from backend.config import db, app
from backend.users.models import UserPhone
from backend.leadgen.models import LeadLandingPage, LeadWhatsapp
from backend.apisocialhub.models import MessageLog, MessageList
from backend.apisocialhub.resolvers import send_message, send_message_with_file, cherry_pick_message
from backend.apicrmgraphql.resolvers.appointments_resolver import fetch_appointments, filter_and_clean_appointments
from backend.apicrmgraphql.resolvers.leads_resolver import fetch_all_leads, filter_and_clean_leads, create_lead
from .models import LeadsHandler
from sqlalchemy import desc
from sqlalchemy.sql import text
import threading
load_dotenv()

# Import stop flag from app
stop_flag = threading.Event()
def keep_alive():
    try:
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        print("Pinged the database to keep the connection alive.")
    except Exception as e:
        db.session.rollback()
        print(f"Keep-alive failed: {e}")
# Funções para obter e processar dados

def get_leads_from_core(phone=None):
    if phone:
        leads_landing = LeadLandingPage.query.filter(LeadLandingPage.phone == phone)
        leads_whatsapp = LeadWhatsapp.query.filter(LeadWhatsapp.phone == phone)
    else:
        leads_landing = LeadLandingPage.query
        leads_whatsapp = LeadWhatsapp.query

    # Order by created_date in descending order to get the most recent first
    leads_landing = leads_landing.order_by(LeadLandingPage.id.desc()).limit(1).all()
    leads_whatsapp = leads_whatsapp.order_by(LeadWhatsapp.id.desc()).limit(700).all()
    # leads_whatsapp = leads_whatsapp.order_by(LeadWhatsapp.id.desc()).offset(213).limit(120).all()

    print(f"Got {len(leads_landing)} leads from landing pages.")
    print(f"Got {len(leads_whatsapp)} leads from WhatsApp.")

    return leads_landing, leads_whatsapp

def get_leads_landing():
    return LeadLandingPage.query.all()

def get_leads_whatsapp():
    # leads = LeadWhatsapp.query.all() # instead we limited!
    leads = LeadWhatsapp.query.order_by(desc(LeadWhatsapp.id)).limit(250).all()
    print(f"Retrieved {len(leads)} leads from WhatsApp.")
    return leads

def count_sent_messages_to_lead_phone():
    return db.session.query(
        MessageLog.lead_phone_number, db.func.count(MessageLog.id)
    ).group_by(MessageLog.lead_phone_number).all()

def get_appointments(start_date, end_date):
    return fetch_appointments(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))

def get_leads(start_date, end_date):
    return fetch_all_leads(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), os.getenv('GRAPHQL_API_TOKEN'))

def get_message():
    messages_dic = {}
    try:
        # Fetching all messages from MessageList table
        messages = MessageList.query.all()  # Adjust limit if necessary for testing, e.g., query.limit(10)
        for item in messages:
            type_of_message = item.title
            messages_dic[type_of_message] = {
                'text': item.text,
                'interval': item.interval,
                'file': item.file
            }
        return messages_dic
    except Exception as e:
        print(f"Error while fetching messages: {e}")
        return {}

def get_phone_token():
    # Creating an empty dic to be filled upon a query
    phones_dic = {}
    phone_list = UserPhone.query.all()

    # For to retrieve each individual phone (id, number and token)
    for phone in phone_list:
        phones_dic[phone.phone_number] = {
            'id': phone.id, 
            'phone_number': phone.phone_number,
            'phone_token': phone.phone_token, 
            'phone_description': phone.phone_description
        }
    return phones_dic

def data_wrestling(leads_landing, leads_whatsapp, appointments, count_messages_by_phone, leads, user_id):
    
    df_leads_receive_message = leads_whatsapp + leads_landing
    sent_messages_phones = {row[0]: row[1] for row in count_messages_by_phone}

    leads_phones = {
                lead['telephone'] for lead 
                    in leads if lead['telephone']
                    }  
    appointment_phones = {
                        appointment['telephones'][0] for appointment
                          in appointments if appointment['telephones']
                          }

    leads_df = []
    for lead in df_leads_receive_message:
        phone = lead.phone.strip()
        print(f"Processing phone: {phone}")
        print(f"Message count for this phone: {sent_messages_phones.get(phone, 'Not found')}")  # Debug print

        sent_message_count = sent_messages_phones.get(phone, 0)
        has_appointment = phone in appointment_phones
        has_lead = phone in leads_phones

        # Getting attributes with default values
        store = getattr(lead, 'store', 'CENTRAL')
        region = getattr(lead, 'region', 'São Paulo')
        tags = getattr(lead, 'tags', 'SEM TAGS')

        leads_df.append({
            'phone': phone,
            'created_date': lead.created_date,
            'source': lead.source,
            'name': lead.name,
            'tag': lead.tag, # para usar no token
            'sent_message_count': sent_message_count,
            'has_appointment': has_appointment,
            'has_lead': has_lead,
            'store': store,
            'region': region,
            'tags': tags,
            'user_id': user_id
        })

        # Storage this leads temporarily on the LeadsToReceiveMessage table
        lead_to_receive_message = LeadsHandler(
            phone=phone,
            created_date=lead.created_date,
            source=lead.source,
            name=lead.name,
            tag=lead.tag,
            sent_message_count=sent_message_count,
            has_appointment=has_appointment,
            has_lead=has_lead,
            user_id=user_id
        )
        db.session.add(lead_to_receive_message)
    db.session.commit()

    return pd.DataFrame(leads_df)

# Main function to process all the data we have carefully gathered
def run_data_wrestling(user_id):
    try:
        load_dotenv() 

        print("Printing Start DataWrestler")
        app.logger.info("log starting data wrestling")
        if stop_flag.is_set():
            print("Stopping data wrestling process.")
            yield "Stopping data wrestling process.\n"
            return
        
        start_date = datetime.now() - timedelta(days=15)
        end_date = datetime.now() + timedelta(days=15)
        today = datetime.now().strftime("%d/%m/%Y")

        yield f"Starting to wrestle data from {start_date} till {end_date}\n"

        # DATA GATHERING        
        print("Loading leads from core")
        yield "Loading leads from core."
        keep_alive()
        leads_landing, leads_whatsapp = get_leads_from_core()
        if stop_flag.is_set():
            print("Stopping data wrestling process.")
            yield "Stopping data wrestling process."
            return
        
        print("Loading sent message from core")
        yield "Loading sent message from core."
        keep_alive() 
        df_count_messages_by_phone = count_sent_messages_to_lead_phone()
        if stop_flag.is_set():
            print("Stopping data wrestling process.")
            yield "Stopping data wrestling process."
            return
        print("Loading leads from graphQL")
        yield "Loading leads from graphQL. It might take 15-20min..."
        keep_alive() 
        leads_data = get_leads(start_date, end_date)
         # Stop check
        if stop_flag.is_set():
            print("Stopping data wrestling process.")
            yield "Stopping data wrestling process."
            return
        yield "Leads are ready...."

        print("Loading appointments from graphQL")
        yield "Loading appointments from graphQL. It might take 15-20min..."
        keep_alive() 
        appointments_data = get_appointments(start_date, end_date)
        if stop_flag.is_set():
            print("Stopping data wrestling process.")
            yield "Stopping data wrestling process."
            return
        yield "Appointments are ready...."

        # DATA PROCESSING
        # maybe change individually to get_leads_landing e #get_leads_whatsapp
        leads_df = data_wrestling(leads_landing, leads_whatsapp, appointments_data, df_count_messages_by_phone, leads_data, user_id)
        yield "Data processing done.\n"
        
        # DATA DELIVERY
        # Convert the DataFrame to a list of dictionaries
        # This is the dataframe that will serve the for loop down below
        leads_list = leads_df.to_dict(orient='records')
        leads_json = json.dumps(leads_list, default=str, ensure_ascii=False, indent=4)
        print(leads_json)
        if stop_flag.is_set():
            print("Stopping data wrestling process.")
            yield "Stopping data wrestling process.\n"
            return
        
        keep_alive() 
        # Total time to sleep
        total_time = 1 * 60 * 180  #+ (15 * 60) # 1 hour + 15m
        interval = 60
        display_interval = 1  # countdown
        # Loop that sleeps until time to go
        for remaining_time in range(int(total_time), 0, -interval):
            time.sleep(interval)
            if remaining_time % (display_interval * 60) == 0:
                remaining_minutes = remaining_time // 60
                print(f"Time left: {remaining_minutes} minutes")
        print("Finished waiting.. ready for next")
        print("resting 30s at message and phones dictionaries")
        yield "log at messages and phones dic. Waiting 30s\n"
        time.sleep(30)
        if stop_flag.is_set():
            print("Stopping data wrestling process.")
            yield "Stopping data wrestling process.\n"
            return
        messages_dic = get_message()
        phones_dic = get_phone_token()

        print("Entering the for loop")
        keep_alive() 
        if stop_flag.is_set():
            print("Stopping data wrestling process.")
            yield "Stopping data wrestling process.\n"
            return
        # Send messages based on processed leads
        for index, cliente in leads_df.iterrows():
            phone = cliente['phone']
            contador = cliente['sent_message_count']
            source = cliente['source']
            has_appointment = cliente['has_appointment']
            has_lead = cliente['has_lead']
            store = cliente['store']
            region = cliente['region']
            tags = cliente['tags']
            
            # Flag - check dic phones to match token
            name = cliente['name']
            tag = cliente['tag']
            dias_depois_da_conversa = (datetime.now() - cliente['created_date']).days
            
            message_key = None
            
            print("Ready to oblige conditions (has appointment | lead && src whatsapp)!")

            # Process leads without appointments, leads and source Whatsapp
            if not has_appointment and not has_lead and source == "Whatsapp":

                if tag == "Botox":
                    campaign = "Botox"
                    phone_description = "Botox"

                elif tag == "Preenchimento":
                    campaign = "Preenchimento"
                    phone_description = "Preenchimento"
                else:
                    print(f"Ops... {tag} not mapped.")
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
                    
                    try:
                    # Create lead in CRM
                        response = create_lead(name, phone, email, message, store, region)
                        if 'data' in response and 'createLead' in response['data']:
                            print(f"Lead {phone} criado com sucesso!")
                        else:
                            print(f"Error creating lead: {response}")
                        
                        # Rest for a minute before processing the next lead
                        print(f"Waiting 1 minute before processing the next lead...")
                        time.sleep(60)
                        
                        # Log lead creation
                        try:
                            lead = db.session.query(LeadWhatsapp).filter_by(phone=cliente['phone']).first()
                            if lead is None:
                                print(f"Failed to find lead with phone {cliente['phone']}")
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
                                date_sent=datetime.now(),
                                user_id=user_id
                            )
                            db.session.add(log)
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                            print(f"Error logging lead creation: {str(e)}")
                    except Exception as e:
                        print(f"Error processing lead: {str(e)}")
                    
                # Extra additions    
                elif contador == 4 and dias_depois_da_conversa >= 7:
                    message_key = "pesquisad7"
                elif contador == 5 and dias_depois_da_conversa >= 30:
                    message_key = "botox30d"
                else:
                    print(f"Contador {contador} não mapeado para uma mensagem.")
                    continue

                # Fetching appropriate message and file from dic
                mensagem = messages_dic.get(message_key, {}).get("text", None)
                file = messages_dic.get(message_key, {}).get("file", None)
                if not mensagem:
                    print(f"Mensagem para o contador {contador} não encontrada. Mensagem: {message_key}")
                    continue

                # Get the sender phone data based on phone descr
                sender_phone_data = next(
                    (data for data in phones_dic.values() if data.get('phone_description') == phone_description),
                    None
                )
                if not sender_phone_data:
                    print(f"Erro ao buscar phone_description: {phone_description}")
                    continue

                # Fetching appropriate phone token
                api_token = sender_phone_data.get("phone_token", None)
                if not api_token:
                    print(f"Erro ao buscar phone_token for sender: {sender_phone_data}")
                    continue
                
                ## Sending the message with cherry pick update
                # *task* check if we really need this IF here
                if file:
                    response = cherry_pick_message(phone, mensagem, api_token, file)
                    time.sleep(10)
                    print("Taking a 10s breath yes file...")
                else:
                    response = cherry_pick_message(phone, mensagem, api_token)
                    time.sleep(10)
                    print("Taking a 10s breath no file...")

                # Handling response and logging
                status_envio = response.get("success", False)
                            
                if status_envio:
                    lead = db.session.query(LeadWhatsapp).filter_by(phone=cliente['phone']).first()
                    print(f"{message_key} enviada para: {phone}")
                    log = MessageLog(
                                sender_phone_id=sender_phone_data['id'],
                                sender_phone_number=sender_phone_data['phone_number'],  # Agora registrando o número
                                source="Whatsapp",
                                lead_phone_id=lead.id,
                                lead_phone_number=cliente['phone'],
                                status="sent",
                                message_title=message_key,  # Add this if it's the message ID
                                message_text=mensagem,
                                date_sent=datetime.now(),
                                user_id=user_id
                            )
                    try:
                        db.session.add(log)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        print(f"Failed to log message: {str(e)}")
            pass
        print("Finished loop!")
        yield "Finished loop!"
    except Exception as e:
        app.logger.error(f"Error while running datawrestler: {e}")

def view_logs():
    logs = MessageLog.query.all()
    for log in logs:
        print(f"ID: {log.lead_phone_id}, "
              f"LeadPhone: {log.lead_phone_number}, "
              f"Message ID: {log.message_id}, "
              f"Status: {log.status}, "
              f"Sender PhoneNb: {log.sender_phone_number}, "
              f"Date Sent: {log.date_sent}")

# Execute only if we call directly from resolvers.py
# not in use!
# if __name__ == "__main__":
#     with app.app_context():
#         run_data_wrestling()