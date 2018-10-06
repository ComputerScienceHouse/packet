"""
The application setup and initialization code lives here.
"""

import os
from logging.config import dictConfig
import logging

import csh_ldap
from flask import Flask
from flask_migrate import Migrate
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_sqlalchemy import SQLAlchemy

from ._version import __version__

# Logger configuration
dictConfig({
    "version": 1,
    "formatters": {"default": {
        "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    }},
    "handlers": {"packet": {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
        "level": "DEBUG",
        "formatter": "default"
    }},
    "root": {
        "level": "DEBUG",
        "handlers": ["packet"]
    }
})

app = Flask(__name__)

# Load default configuration and any environment variable overrides
app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

# Load file based configuration overrides if present
if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))

app.config["VERSION"] = __version__
logging.getLogger().setLevel(app.config["LOG_LEVEL"])

# Initialize the extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

auth = OIDCAuthentication(app, issuer=app.config["OIDC_ISSUER"], client_registration_info={
    "client_id": app.config["OIDC_CLIENT_ID"],
    "client_secret": app.config["OIDC_CLIENT_SECRET"],
    "post_logout_redirect_uris": "/logout/"
})

# LDAP
_ldap = csh_ldap.CSHLDAP(app.config["LDAP_BIND_DN"], app.config["LDAP_BIND_PASS"])

app.logger.info("DB and LDAP configured")

# pylint: disable=wrong-import-position
from . import models
from . import context_processors
from . import commands
from .routes import api, shared

if app.config["REALM"] == "csh":
    from .routes import upperclassmen
else:
    from .routes import freshmen

app.logger.info("Routes registered")
