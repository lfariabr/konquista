import os
import pandas as pd
import logging
from backend.config import db
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_user, logout_user, login_required, current_user
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from .data_cleaner import process_csv_files # triggered on line 122 *task* highlight

# Absolute imports
from backend.leadgen.models import LeadLandingPage, LeadWhatsapp
from backend.leadgen.forms import LeadForm, LeadWhatsappForm

leadgen_blueprint = Blueprint('leadgen', __name__)

@leadgen_blueprint.route('/botox', methods=['GET', 'POST'])
def botox():
    
    form = LeadForm()
    if form.validate_on_submit():
        try:
            name = form.name.data
            phone = form.phone.data
            store = form.store.data
            
            # Define static values for this form submission context
            source = 'landing page'
            tag = 'botox'

            # Create the lead
            lead = LeadLandingPage(
                            name=name,
                            phone=phone,
                            store=store,
                            tag=tag,
                            source=source,
                            region='São Paulo',
                            tags='landing page')        
            db.session.add(lead)
            db.session.commit()
            flash('Obrigado, recebemos o seu cadastro!')

            return render_template('botox.html', form=form)
        except SQLAlchemyError as e:
                db.session.rollback()  # Explicit rollback in case of error
                print("Database error occurred:", str(e))  # Log the error to the console or a file
                flash('Houve um erro ao processar seu cadastro. Por favor, tente novamente.')
    else:
        print("Erros de validação: ", form.errors)  # Log form validation errors

    return render_template('botox.html', form=form)

####### IMPORT CSV
# Defining upload folder - local
# upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
# os.makedirs(upload_folder, exist_ok=True)

allowed_extensions = {'csv', 'xlsx'}  

# Test Vercel
upload_folder = '/tmp/uploads'
os.makedirs(upload_folder, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@leadgen_blueprint.route('/upload_csv', methods=['GET', 'POST'])
@login_required
def upload():
    logging.info("Entrou na rota de upload CSV")
    if request.method == 'POST':
        # used to capture the date within the form
        # that comes from the website managed by user
        # manually importing contacts from csv file
        # if it's empty, set it to current date
        date_str = request.form.get('date')
        if not date_str:
            created_date = datetime.now()  
        else:
            try:
                # Convert to datetime because dealing with 
                # dates and times is DELICATE/DELICIOUS
                created_date = datetime.strptime(date_str, '%Y-%m-%d')  
            except ValueError:
                flash('Ops... Wrong date format!')
                logging.error("Ops... Wrong date format!")
                return redirect(url_for('leadgen.upload'))
        logging.info(f"Data recebida: {date_str}")

        # Grab the uploaded files *task*
        # an improvement could be make them not mandatory
        # for example user might upload only 1 file    
        botox_file = request.files.get('botox_file')
        preenchimento_file = request.files.get('preenchimento_file')
        logging.info(f"Arquivos recebidos - Botox: {botox_file}, Preenchimento: {preenchimento_file}")

        if not botox_file and not preenchimento_file:
            flash('Nenhum arquivo selecionado')
            return redirect(url_for('leadgen.upload'))
        
        botox_file_path = None
        preenchimento_file_path = None

        if botox_file and allowed_file(botox_file.filename):
            botox_filename = secure_filename(botox_file.filename)
            botox_file_path = os.path.join(upload_folder, botox_filename)
            botox_file.save(botox_file_path)
            flash('Arquivo de Botox enviado com sucesso!')

        if preenchimento_file and allowed_file(preenchimento_file.filename):
            preenchimento_filename = secure_filename(preenchimento_file.filename)
            preenchimento_file_path = os.path.join(upload_folder, preenchimento_filename)
            preenchimento_file.save(preenchimento_file_path)
            flash('Arquivo de Preenchimento enviado com sucesso!')

        # Processar os arquivos enviados
        if botox_file or preenchimento_file:
            df_leads_whatsapp = process_csv_files(
                                    botox_file_path, 
                                    preenchimento_file_path
                                )

            # Iterando sobre as linhas do DataFrame e salvando no banco
            for index, row in df_leads_whatsapp.iterrows():
                try:
                    name = str(row['Nome'])
                    phone = str(row['Whatsapp'])

                    if not name or not phone:
                        continue
                    # Defining the tag on the database to be according to the filename
                    tag = 'Preenchimento' if 'preenchimento' in row['filename'] else 'Botox'

                    # Preparing the data for the database
                    lead = LeadWhatsapp(
                                    name=row['Nome'],
                                    phone=row['Whatsapp'],
                                    created_date=created_date,  # Usando a data selecionada no front-end
                                    tag=tag,
                                    source='Whatsapp',
                                    #store=row['Unidade'],
                                    #region=row['Região'],
                                    #tags=row['Tags']
                                    store=row.get('Unidade', 'CENTRAL'),
                                    region=row.get('Região', 'São Paulo'),
                                    tags=row.get('Tags', 'SEM TAGS'),
                                    user_id=current_user.id
                                )
                    db.session.add(lead)
                    db.session.commit()
                
                except Exception as e:
                    print(f"Erro ao adicionar lead: {e}, Linha: {index}")
                    continue
        flash('Leads adicionados ao banco de dados com sucesso!')
        return redirect(url_for('core.view_leads_whatsapp'))

    return render_template('core/upload.html')