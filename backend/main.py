from flask import request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from .config import app, db
from .leadgen.models import LeadLandingPage
from .leadgen.forms import LeadForm
from .users.forms import LoginForm, RegistrationForm

# Blueprints
from .leadgen.routes import leadgen_blueprint
from .users.routes import users_blueprint
from .api.routes import api_blueprint
from .core.routes import core_blueprint
from .apicrmgraphql.routes import apicrmgraphql_blueprint
from .apisocialhub.routes import apisocialhub_blueprint
from .datawrestler.routes import datawrestler_blueprint

# APScheduler imports
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

#############

# LEAD GEN AREA
app.register_blueprint(leadgen_blueprint)

# LOGGED IN AREA
app.register_blueprint(users_blueprint, url_prefix='/users')

# CORE AREA
app.register_blueprint(core_blueprint, url_prefix='/core')

# API GRAPHQL AREA
app.register_blueprint(apicrmgraphql_blueprint, url_prefix='/apicrmgraphql')

# API SOCIAL HUB GRAPHQL AREA
app.register_blueprint(apisocialhub_blueprint, url_prefix='/apisocialhub')

# DATA WRESTLER AREA
app.register_blueprint(datawrestler_blueprint, url_prefix='/datawrestler')

# CRUD AREA
app.register_blueprint(api_blueprint)

# Home Route
@app.route('/')
def index():
    return render_template('core/index.html')

# Creating error handler
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# ------------------------------
# SCHEDULER SETUP
# ------------------------------
from .datawrestler.routes import run_datawrestler
from .datawrestler.resolvers import run_data_wrestling, get_leads_whatsapp, data_wrestling, get_message, get_phone_token, view_logs, count_sent_messages_to_lead_phone

# Função que agenda o datawrestler para rodar automaticamente
# def schedule_datawrestler():
#     with app.app_context():
#         print("DataWrestler online!!!")
#         run_data_wrestling() # run_data_wrestling

# # Configurando o scheduler
# scheduler = BackgroundScheduler()                                 # seconds=3
# scheduler.add_job(func=schedule_datawrestler, trigger="interval", minutes=60)  # minutes=1 / hours=24
# scheduler.start()

# # Garante que o scheduler desligue ao finalizar a aplicação
# atexit.register(lambda: scheduler.shutdown())

# with app.app_context():
#     db.create_all()