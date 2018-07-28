"""
The application setup and initialization code lives here.
"""

import os
from flask import Flask
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

db = SQLAlchemy(app)
migrate = Migrate(app, db)

auth = OIDCAuthentication(app, issuer=app.config["OIDC_ISSUER"],
                          client_registration_info=app.config["OIDC_CLIENT_CONFIG"])

# pylint: disable=wrong-import-position
from . import routes
