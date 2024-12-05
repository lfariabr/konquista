import sys
sys.path.append('/Users/luisfaria/Library/CloudStorage/GoogleDrive-lfariabr@gmail.com/My Drive/LUIS/WORK/18digital/pro-corpo/Lab Programação/dev/_working/konquista_flaskk')

# send_messages.py
from resolvers import send_message_to_all_leads_from_json, app, db, LeadsHandler
import json

with app.app_context():
    # Get leads from LeadsHandler table
    leads = db.session.query(LeadsHandler).all()
    
    # Convert to list of dicts with all the fields we need
    leads_list = []
    for lead in leads:
        leads_list.append({
            'phone': lead.phone,
            'created_date': lead.created_date,
            'source': lead.source,
            'name': lead.name,
            'tag': lead.tag,
            'sent_message_count': lead.sent_message_count,
            'has_appointment': lead.has_appointment,
            'has_lead': lead.has_lead,
            'store': 'CENTRAL',  # Default value as in original code
            'region': 'São Paulo',  # Default value as in original code
            'tags': 'SEM TAGS',  # Default value as in original code
            'user_id': lead.user_id
        })
    
    # Convert to JSON
    leads_json = json.dumps(leads_list, default=str)
    
    # Provide the user_id when calling the function
    user_id = 1  # Replace with the actual user_id you want to use
    send_message_to_all_leads_from_json(leads_json, user_id)