"""
The application setup and initialization code lives here.
"""

import os

import csh_ldap
from flask import Flask
from flask_migrate import Migrate
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from flask_sqlalchemy import SQLAlchemy

from ._version import __version__

app = Flask(__name__)

# Load default configuration and any environment variable overrides
app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

# Load file based configuration overrides if present
if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))

app.config["VERSION"] = __version__

# Initialize the extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

APP_CONFIG = ProviderConfiguration(issuer=app.config["OIDC_ISSUER"],
                          client_metadata=ClientMetadata(app.config["OIDC_CLIENT_ID"],
                                                            app.config["OIDC_CLIENT_SECRET"]))

auth = OIDCAuthentication({'app': APP_CONFIG}, app)

# LDAP
_ldap = csh_ldap.CSHLDAP(app.config["LDAP_BIND_DN"], app.config["LDAP_BIND_PASS"])

# pylint: disable=wrong-import-position
from . import models
from . import context_processors
from . import commands
from .routes import api, shared

if app.config["REALM"] == "csh":
    from .routes import upperclassmen
else:
    from .routes import freshmen
