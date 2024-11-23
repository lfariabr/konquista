import os
import logging
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager
from logging.handlers import RotatingFileHandler
from markupsafe import Markup
from sqlalchemy import event, Engine

load_dotenv()
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')     
CORS(app)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Vercel
app.instance_path = '/tmp/instance'

# Sending Message with File
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'users', 'messages', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

######################
## DATABASE dev | lines 31 & 32
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db' # for local dev
# db = SQLAlchemy(app)

# #####################
# DATABASE prod | lines 36 - 57
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') + "&connect_timeout=300"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy optimizations for connection handling
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_size': 5,  # Adjust as per your needs, smaller pools can reduce initialization time.
    'max_overflow': 10,  # Number of connections exceeding the pool size.
    'pool_timeout': 30,  # Timeout for getting a connection from the pool.
    'pool_recycle': 1800  # Recycle connections every 30 minutes.
}

# Set the statement timeout to 20 minutes (1,200,000 ms)
@event.listens_for(Engine, "connect")
def set_timeout(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("SET statement_timeout = 1200000;")  # 20 minutes
    cursor.close()
#####################
#####################
db = SQLAlchemy(app, session_options={"autocommit": False, "autoflush": False})

######################
## MIGRATE / LOGIN / LOGS
######################
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'users.login'

@login_manager.user_loader
def load_user(user_id):
    from .users.models import User
    return User.query.get(user_id)

# Adjust logging to reduce verbosity and log to a writable location
log_file_path = "/tmp/app.log"
error_file_path = "/tmp/errors.log"


# Logs
logging.basicConfig(level=logging.DEBUG,
                    handlers=[
                                # logging.FileHandler("app.log"),
                            #   logging.FileHandler("errors.log"),
                              RotatingFileHandler(log_file_path, maxBytes=10240, backupCount=3),
                                RotatingFileHandler(error_file_path, maxBytes=10240, backupCount=3),
                              logging.StreamHandler()  # Uncomment to log to console
                    ], 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.INFO)
logging.getLogger('werkzeug').setLevel(logging.DEBUG)

# Custom filter to replace newlines with <br> tags
def nl2br(value):
    if value is None:
        value = ''  # If value is None, set it to an empty string

    # Replace consecutive newlines (\n\n) with <br><br> (paragraph break)
    value = value.replace("\n\n", "<br><br>")

    # Replace single newlines (\n) with a space, avoiding extra <br> tags
    value = value.replace("\n", " ")

    return Markup(value)

# Registering custom filter with the Flask app
app.jinja_env.filters['nl2br'] = nl2br