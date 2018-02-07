import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restless import APIManager

app = Flask(__name__)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

# Create the database session and import models.
db = SQLAlchemy(app)
from packet.models import *
migrate = Migrate(app, db)

# Initialize the Restless API manager
manager = APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Freshman, methods=['GET', 'POST', 'DELETE'])
manager.create_api(Packet, methods=['GET', 'POST', 'PUT', 'DELETE'])

@app.route('/')
def hello_world():
        return 'Hello, World!'
