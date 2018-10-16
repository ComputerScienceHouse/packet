"""
The application setup and initialization code lives here
"""

import os
import logging
import json

import csh_ldap
from flask import Flask
from flask_migrate import Migrate
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Load default configuration and any environment variable overrides
_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
app.config.from_pyfile(os.path.join(_root_dir, "config.env.py"))

# Load file based configuration overrides if present
_pyfile_config = os.path.join(_root_dir, "config.py")
if os.path.exists(_pyfile_config):
    app.config.from_pyfile(_pyfile_config)

# Fetch the version number from the npm package file
with open(os.path.join(_root_dir, "package.json")) as package_file:
    app.config["VERSION"] = json.load(package_file)["version"]

# Logger configuration
logging.getLogger().setLevel(app.config["LOG_LEVEL"])
app.logger.info("Launching packet v" + app.config["VERSION"])
app.logger.info("Using the {} realm".format(app.config["REALM"]))

# Initialize the extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.logger.info("SQLAlchemy pointed at " + repr(db.engine.url))

auth = OIDCAuthentication(app, issuer=app.config["OIDC_ISSUER"], client_registration_info={
    "client_id": app.config["OIDC_CLIENT_ID"],
    "client_secret": app.config["OIDC_CLIENT_SECRET"],
    "post_logout_redirect_uris": "/logout/"
})

# LDAP
_ldap = csh_ldap.CSHLDAP(app.config["LDAP_BIND_DN"], app.config["LDAP_BIND_PASS"])

app.logger.info("OIDCAuth and LDAP configured")

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
