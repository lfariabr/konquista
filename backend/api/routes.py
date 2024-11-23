from flask import Blueprint, request, jsonify, json
from backend.config import db

# Absolute imports
from backend.users.models import User  
from backend.users.forms import LoginForm, RegistrationForm
from backend.leadgen.models import LeadLandingPage

api_blueprint = Blueprint('api', __name__)

#############
# GET
#############
@api_blueprint.route('/leads', methods=['GET'])
def get_leads():

    leads = LeadLandingPage.query.all() #however they're python objects
    json_leads = list(map(lambda x: x.to_json(), leads))
    return jsonify({"leads": json_leads})

#############
# CREATE
#############
@api_blueprint.route('/create_lead', methods=['POST'])
def create_lead():
    name = request.json.get("name")
    phone = request.json.get("phone")
    tags = request.json.get("tags")

    if not name or not phone or not tags:
        return (
            jsonify({"message": "name, phone, tags"}),
            400
        )
    
    lead = LeadLandingPage(name=name, phone=phone, tags=tags)

    try:
        db.session.add(lead) # Staging area
        db.session.commit() # Actually write it into database

    except Exception as e:
        return jsonify({"message": str(e)}), 400
    
    return jsonify({"message": "lead created"}), 200

#############
# UPDATE
#############

@api_blueprint.route('/update_lead/<int:lead_id>', methods=['PATCH'])
def update_lead(lead_id):
    lead = LeadLandingPage.query.get(lead_id)

    if not lead:
        return jsonify({"message": "lead not found"}), 404
    
    data = request.json
    lead.name = data.get("name", lead.name)
    lead.phone = data.get("phone", lead.phone)
    lead.tags = data.get("tags", lead.tags)

    db.session.commit()
    return jsonify({"message": "lead updated"}), 200

#############
# DELETE
#############

@api_blueprint.route('/delete_lead/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    lead = LeadLandingPage.query.get(lead_id)

    if not lead:
        return jsonify({"message": "lead not found"}), 404
    
    db.session.delete(lead)
    db.session.commit()
    return jsonify({"message": "lead deleted"}), 200