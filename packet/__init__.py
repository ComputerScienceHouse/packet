"""
The application setup and initialization code lives here
"""

import json
import logging
import os

import csh_ldap
import onesignal
from flask import Flask
from flask_gzip import Gzip
from flask_migrate import Migrate
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
from flask_pyoidc.provider_configuration import ProviderConfiguration, ClientMetadata
from flask_sqlalchemy import SQLAlchemy

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

app = Flask(__name__)
gzip = Gzip(app)

# Load default configuration and any environment variable overrides
_root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
app.config.from_pyfile(os.path.join(_root_dir, 'config.env.py'))

# Load file based configuration overrides if present
_pyfile_config = os.path.join(_root_dir, 'config.py')
if os.path.exists(_pyfile_config):
    app.config.from_pyfile(_pyfile_config)

# Fetch the version number from the npm package file
with open(os.path.join(_root_dir, 'package.json')) as package_file:
    app.config['VERSION'] = json.load(package_file)['version']

# Logger configuration
logging.getLogger().setLevel(app.config['LOG_LEVEL'])
app.logger.info('Launching packet v' + app.config['VERSION'])
app.logger.info('Using the {} realm'.format(app.config['REALM']))

# Initialize the extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.logger.info('SQLAlchemy pointed at ' + repr(db.engine.url))

APP_CONFIG = ProviderConfiguration(issuer=app.config['OIDC_ISSUER'],
                          client_metadata=ClientMetadata(app.config['OIDC_CLIENT_ID'],
                                                            app.config['OIDC_CLIENT_SECRET']))

# Initialize Onesignal Notification apps
csh_onesignal_client = onesignal.Client(user_auth_key=app.config['ONESIGNAL_USER_AUTH_KEY'],
                                    app_auth_key=app.config['ONESIGNAL_CSH_APP_AUTH_KEY'],
                                    app_id=app.config['ONESIGNAL_CSH_APP_ID'])

intro_onesignal_client = onesignal.Client(user_auth_key=app.config['ONESIGNAL_USER_AUTH_KEY'],
                                    app_auth_key=app.config['ONESIGNAL_INTRO_APP_AUTH_KEY'],
                                    app_id=app.config['ONESIGNAL_INTRO_APP_ID'])

# OIDC Auth
auth = OIDCAuthentication({'app': APP_CONFIG}, app)

# Sentry
sentry_sdk.init(
    dsn=app.config['SENTRY_DSN'],
    integrations=[FlaskIntegration(), SqlalchemyIntegration()]
)

app.logger.info('OIDCAuth and LDAP configured')

# pylint: disable=wrong-import-position
from .ldap import ldap
from . import models
from . import context_processors
from . import commands
from .routes import api, shared

if app.config['REALM'] == 'csh':
    from .routes import upperclassmen
    from .routes import admin
else:
    from .routes import freshmen

app.logger.info('Routes registered')
