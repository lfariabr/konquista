import os
import threading
from flask import Blueprint, render_template, flash, redirect, url_for, current_app, send_from_directory, request, jsonify, make_response
from flask_login import login_required, current_user
from sqlalchemy import desc, text, literal
from flask_socketio import SocketIO, emit
from datetime import datetime

from backend.config import db, app
from backend.users.models import MessageList, UserPhone
from backend.users.forms import MessageForm, UserPhoneForm
from backend.datawrestler.resolvers import run_data_wrestling
from backend.leadgen.models import LeadWhatsapp, LeadLandingPage
from backend.leadgen.forms import LeadWhatsappForm, LeadForm
from backend.apisocialhub.models import MessageLog
from werkzeug.utils import secure_filename
from flask import make_response

core_blueprint = Blueprint('core', __name__)

# Admin Dashboard Route
@core_blueprint.route('/admin')
@login_required
def index():
    return render_template('core/core.html')

####################
# MESSAGES
####################

# Route for Creating a New Message
@core_blueprint.route('/new_message', methods=['GET', 'POST'])
@login_required
def new_message():
    form = MessageForm()
    filename = None
    
    if form.validate_on_submit():
        if form.file.data and hasattr(form.file.data, 'filename'):
            filename = secure_filename(form.file.data.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.file.data.save(file_path)
        else:   
            file_path = None

        message = MessageList(
            title=form.title.data, 
            text=form.text.data, 
            interval=form.interval.data, 
            file=filename,
            user_id=current_user.id
        )

        db.session.add(message)
        db.session.commit()
        flash('Mensagem cadastrada com sucesso!')
        return redirect(url_for('core.message_list'))
    
    return render_template('core/new_message.html', form=form)

# Route for Viewing All Messages
@core_blueprint.route('/message_list', methods=['GET'])
@login_required
def message_list():
    # messages = MessageList.query.all()
    # Showing message to current user only
    messages = MessageList.query.filter_by(user_id=current_user.id).all()
    return render_template('core/message_list.html', messages=messages)

# Route for Editing a Message
@core_blueprint.route('/edit_message/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_message(id):
    message = MessageList.query.get_or_404(id)
    form = MessageForm(obj=message)

    if form.validate_on_submit():
        message.title = form.title.data
        message.text = form.text.data
        message.interval = form.interval.data

        if form.file.data and hasattr(form.file.data, 'filename'):
            filename = secure_filename(form.file.data.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])
            form.file.data.save(file_path)
            message.file = filename
        else:
            message.file = message.file

        db.session.commit()
        flash('Mensagem editada com sucesso!')
        return redirect(url_for('core.message_list'))

    return render_template('core/new_message.html', form=form, message=message)

# Route for uploading files
@core_blueprint.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

# Route for Deleting a Message
@core_blueprint.route('/delete_message/<int:id>', methods=['POST'])
@login_required
def delete_message(id):
    message = MessageList.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()
    flash('Mensagem deletada com sucesso!')
    return redirect(url_for('core.message_list'))

####################
# SENT MESSAGES 
####################

# Route for message logs with pagination
@core_blueprint.route('/message_logs', methods=['GET'])
def message_logs():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    filters = {
        'id' : request.args.get('id', type=int),
        'date_sent' : request.args.get('date_sent', type=str),
        'message_title' : request.args.get('message_title', type=str),
        'sender_phone_number' : request.args.get('sender_phone_number', type=str),
        'lead_phone_number' : request.args.get('lead_phone_number', type=str),
        'status' : request.args.get('status', type=str),
    }

    ## Building the query based on filters - old
    # query = MessageLog.query

    # Building query based on filters + user_id
    query = MessageLog.query.filter_by(user_id=current_user.id)

    for attr, value in filters.items():
        if value:
            column = getattr(MessageLog, attr, None)
            if column:
                query = query.filter(column == value)
    # Pagination

    try:
        pagination = query.order_by(
                        desc(MessageLog.id)).paginate(
                            page=page, per_page=per_page
                        )
        logs = pagination.items
        total_logs = pagination.total
    except TypeError as e:
        return "Ops.. couldn't get the logs", 500

    return render_template(
                        'core/message_logs.html', 
                        logs=logs, 
                        pagination=pagination, 
                        total_logs=total_logs
                        )

# Route to export message logs to CSV file
@core_blueprint.route('/export_message_logs', methods=['GET'])
@login_required
def export_message_logs():
    # Get all message logs for the current user
    logs = MessageLog.query.filter_by(user_id=current_user.id).all()
    
    # Create CSV content
    csv_content = "id,message_title,sender_phone_number,lead_phone_number,status,date_sent,source\n"
    for log in logs:
        csv_content += f"{log.id},{log.message_title},{log.sender_phone_number},{log.lead_phone_number},{log.status},{log.date_sent},{log.source}\n"
    
    # Create response with CSV file
    response = make_response(csv_content)
    response.headers["Content-Disposition"] = "attachment; filename=message_logs.csv"
    response.headers["Content-Type"] = "text/csv"
    
    return response

####################
# PHONES
####################

# Route for Adding new Phone
@core_blueprint.route('/new_phone', methods=['GET', 'POST'])
@login_required
def new_phone():
    form = UserPhoneForm()
    if form.validate_on_submit():
        phone = UserPhone(user_id=current_user.id,
                          phone_number=form.phone_number.data,
                          phone_token=form.phone_token.data, 
                          phone_description=form.phone_description.data)
        
        db.session.add(phone)
        db.session.commit()
        flash('Telefone cadastrado com sucesso!')
        return redirect(url_for('core.phone_list'))
    
    return render_template('core/new_phone.html', form=form)

# Route for Listing Phones
@core_blueprint.route('/phone_list', methods=['GET'])
@login_required
def phone_list():
    # phones = UserPhone.query.all()
    # Fetch phones only for the logged-in user
    phones = UserPhone.query.filter_by(user_id=current_user.id).all()
    return render_template('core/phone_list.html', phones=phones)

# Editing Phone Number
@core_blueprint.route('/edit_phone/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_phone(id):
    phone = UserPhone.query.get_or_404(id)
    form = UserPhoneForm(obj=phone)

    if form.validate_on_submit():
        phone.phone_number = form.phone_number.data
        phone.phone_token = form.phone_token.data
        phone.phone_description = form.phone_description.data
        db.session.commit()
        flash('Telefone atualizado com sucesso!')
        return redirect(url_for('core.phone_list'))

    return render_template('core/edit_phone.html', form=form, phone=phone)

# Deleting Phone Number
@core_blueprint.route('/delete_phone/<int:id>', methods=['POST'])
@login_required
def delete_phone(id):
    phone = UserPhone.query.get_or_404(id)
    db.session.delete(phone)
    db.session.commit()
    flash('Telefone deletado com sucesso!')
    return redirect(url_for('core.phone_list'))

####################
# DATA WRESTLER
####################

# Route to render the page with the button
@core_blueprint.route('/datawrestler', methods=['GET'])
def run_datawrestler_page():
    return render_template('core/messages_handler.html')

# SocketIO setup
socketio = SocketIO(app)
stop_flag = threading.Event()  # Stop flag for killing the thread

# Background task to run data wrestling
def run_data_wrestling_background(app, user_id):
    with app.app_context():
        try:
            for log in run_data_wrestling(user_id):
                if stop_flag.is_set():
                    print("")  
                    print("Data wrestling STOPPED.")
                    break 

                # Emit logs to the frontend in real-time
                socketio.emit('log_message', log)
                print(log)
        except Exception as e:
            error_msg = f"Error while running data wrestler: {e}"
            socketio.emit('log_message', error_msg)
            print(error_msg)

# Route to start the data wrestling process
@core_blueprint.route('/run_datawrestler', methods=['POST'])
def run_datawrestler_route():
    stop_flag.clear()
    # Get the current user's ID before starting the background thread
    user_id = current_user.id if current_user.is_authenticated else None
    if not user_id:
        return jsonify({"success": False, "message": "No authenticated user found."})

    # Start the data wrestling process in a background thread
    thread = threading.Thread(target=run_data_wrestling_background, args=(app, user_id))
    thread.start()
    return jsonify({"success": True, "message": "Data wrestling process started successfully"})

# Route to stop the data wrestling process
@core_blueprint.route('/stop_datawrestler', methods=['POST'])
def stop_datawrestler_route():
    print("...")
    print("STOP request received")
    stop_flag.set() 
    return jsonify({"message": "Data wrestling process stopped successfully"}), 200

####################
# LEADS
####################

# Route for viewing leads with pagination
# @core_blueprint.route('/leads_whatsapp', methods=['GET'])
# @login_required
# def view_leads_whatsapp():
#     # Pagination parameters
#     page = request.args.get('page', 1, type=int)
#     per_page = 10
#     # Collect filters from request arguments
#     filters = {
#         'name': request.args.get('name', type=str),
#         'phone': request.args.get('phone', type=str),
#         'creation_date': request.args.get('creation_date', type=str),
#         'tag': request.args.get('tag', type=str),
#         'source': request.args.get('source', type=str),
#         'unit': request.args.get('unit', type=str),
#         'region': request.args.get('region', type=str),
#         'tags': request.args.get('tags', type=str),
#     }
    
#     # Building the query based on filters
#     whatsapp = LeadWhatsapp.query
#     landingpage = LeadLandingPage.query

#     # Apply filters
#     for attr, value in filters.items():
#         if value:
#             column = getattr(LeadWhatsapp, attr, None)
#             if column:
#                 whatsapp = whatsapp.filter(column == value)
#             column = getattr(LeadLandingPage, attr, None)
#             if column:
#                 landingpage = landingpage.filter(column == value)

#     query = whatsapp.union(landingpage)
                
#     # Pagination                
#     try:
#         pagination = query.order_by(desc(LeadWhatsapp.id)).paginate(
#             page=page, per_page=per_page, error_out=False
#         )
                        
#         leads = pagination.items

#     except TypeError as e:
#         return "Ops... could not load leads!", 500

#     return render_template(
#                         'core/view_leads.html', 
#                         leads=leads, 
#                         pagination=pagination
#                         )
# ### Editing Leads
# @core_blueprint.route('/edit_leads/<int:lead_id>', methods=['GET', 'POST'])
# @login_required
# def edit_leads(lead_id):
#     lead = LeadWhatsapp.query.get_or_404(lead_id)
#     form = LeadWhatsappForm(obj=lead)
    
#     if form.validate_on_submit():
#         # Atualize os campos diretamente
#         lead.name = form.name.data
#         lead.phone = form.phone.data
#         lead.tag = form.tag.data
#         lead.source = form.source.data
#         lead.store = form.store.data
#         lead.region = form.region.data
#         lead.tags = form.tags.data

#         # Capturar a data do campo de data e definir hora como NOW
#         if form.created_date.data:
#             try:
#                 # Apenas a data fornecida, adicionando a hora atual
#                 selected_date = datetime.strptime(form.created_date.data, '%Y-%m-%d')
#                 lead.created_date = datetime.combine(selected_date, datetime.now().time())
#             except ValueError:
#                 flash('Data inválida. Use o formato do seletor de data.')
#                 return render_template('core/edit_leads.html', form=form, lead=lead)
#         else:
#             lead.created_date = datetime.now()  # Caso o usuário não insira nada

#         try:
#             db.session.commit()
#             flash('Lead editado com sucesso!')
#         except Exception as e:
#             db.session.rollback()
#             flash(f'Erro ao editar o lead: {str(e)}')
#         return redirect(url_for('core.view_leads_whatsapp'))
    
#     return render_template('core/edit_leads.html', form=form, lead=lead)

# #### Excluding Whatsapp Leads
# @core_blueprint.route('/delete_leads/<int:lead_id>', methods=['POST'])
# @login_required
# def delete_leads(lead_id):
#     lead = LeadWhatsapp.query.get_or_404(lead_id)
#     db.session.delete(lead)
#     db.session.commit()
#     flash('Lead excluído com sucesso!')
#     return redirect(url_for('core.view_leads_whatsapp'))

from sqlalchemy import literal
@core_blueprint.route('/leads_whatsapp', methods=['GET'])
@login_required
def view_leads_whatsapp():
    # Pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 10
    # Collect filters from request arguments
    filters = {
        'name': request.args.get('name', type=str),
        'phone': request.args.get('phone', type=str),
        'creation_date': request.args.get('creation_date', type=str),
        'tag': request.args.get('tag', type=str),
        'source': request.args.get('source', type=str),
        'unit': request.args.get('unit', type=str),
        'region': request.args.get('region', type=str),
        'tags': request.args.get('tags', type=str),
    }

    # Building the queries based on filters
    whatsapp = LeadWhatsapp.query
    landingpage = LeadLandingPage.query

    # Building the queries based on filters + current user id
    whatsapp = whatsapp.filter(LeadWhatsapp.user_id == current_user.id)
    landingpage = landingpage.filter(LeadLandingPage.user_id == current_user.id)

    # Apply filters
    for attr, value in filters.items():
        if value:
            column_w = getattr(LeadWhatsapp, attr, None)
            if column_w:
                whatsapp = whatsapp.filter(column_w == value)
            column_l = getattr(LeadLandingPage, attr, None)
            if column_l:
                landingpage = landingpage.filter(column_l == value)

    # Adjust queries to include 'model_type'
    whatsapp_query = whatsapp.with_entities(
        LeadWhatsapp.id.label('id'),
        LeadWhatsapp.name.label('name'),
        LeadWhatsapp.phone.label('phone'),
        LeadWhatsapp.created_date.label('created_date'),
        LeadWhatsapp.tag.label('tag'),
        LeadWhatsapp.source.label('source'),
        LeadWhatsapp.store.label('store'),
        LeadWhatsapp.region.label('region'),
        LeadWhatsapp.tags.label('tags'),
        literal('whatsapp').label('model_type')
    )

    landingpage_query = landingpage.with_entities(
        LeadLandingPage.id.label('id'),
        LeadLandingPage.name.label('name'),
        LeadLandingPage.phone.label('phone'),
        LeadLandingPage.created_date.label('created_date'),
        LeadLandingPage.tag.label('tag'),
        LeadLandingPage.source.label('source'),
        LeadLandingPage.store.label('store'),
        LeadLandingPage.region.label('region'),
        LeadLandingPage.tags.label('tags'),
        literal('landingpage').label('model_type')
    )

    # Union the queries
    query = whatsapp_query.union_all(landingpage_query)

    # Pagination
    pagination = query.order_by(desc('id')).paginate(page=page, per_page=per_page, error_out=False)
    leads = pagination.items

    return render_template('core/view_leads.html', leads=leads, pagination=pagination)

@core_blueprint.route('/edit_leads/<model_type>/<int:lead_id>', methods=['GET', 'POST'])
@login_required
def edit_leads(model_type, lead_id):
    # Validate model type
    if model_type not in ['whatsapp', 'landingpage']:
        flash('Invalid model type provided.')
        return redirect(url_for('core.view_leads_whatsapp'))

    model = LeadWhatsapp if model_type == 'whatsapp' else LeadLandingPage
    lead = model.query.get_or_404(lead_id)
    
    FormClass = LeadWhatsappForm if model_type == 'whatsapp' else LeadForm
    form = FormClass(obj=lead)

    if form.validate_on_submit():
        form.populate_obj(lead)
        try:
            db.session.commit()
            flash('Lead editado com sucesso!')
            return redirect(url_for('core.view_leads_whatsapp'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao editar o lead: {str(e)}')
    else:
        # Log form errors for debugging
        print(f"Form errors: {form.errors}")

    # Pass model_type to the template
    return render_template('core/edit_leads.html', form=form, lead=lead, model_type=model_type)

@core_blueprint.route('/delete_leads/<model_type>/<int:lead_id>', methods=['POST'])
@login_required
def delete_leads(model_type, lead_id):
    model = LeadWhatsapp if model_type == 'whatsapp' else LeadLandingPage
    lead = model.query.get_or_404(lead_id)
    try:
        db.session.delete(lead)
        db.session.commit()
        flash('Lead excluído com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir o lead: {str(e)}')
    return redirect(url_for('core.view_leads_whatsapp'))