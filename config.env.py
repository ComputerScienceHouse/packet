"""
Default configuration settings and environment variable based configuration logic
    See the readme for more information
"""

from os import environ

# Flask config
DEBUG = False
IP = environ.get("PACKET_IP", "localhost")
PORT = environ.get("PACKET_PORT", "8000")
SERVER_NAME = environ.get("PACKET_SERVER_NAME", IP + ":" + PORT)
SECRET_KEY = environ.get("PACKET_SECRET_KEY", "PLEASE_REPLACE_ME")

# Logging config
LOG_LEVEL = environ.get("PACKET_LOG_LEVEL", "INFO")
ANALYTICS_ID = environ.get("ANALYTICS_ID", "UA-134137724-9")

# OpenID Connect SSO config
REALM = environ.get("PACKET_REALM", "csh")

OIDC_ISSUER = environ.get("PACKET_OIDC_ISSUER", "https://sso.csh.rit.edu/auth/realms/csh")
OIDC_CLIENT_ID = environ.get("PACKET_OIDC_CLIENT_ID", "packet")
OIDC_CLIENT_SECRET = environ.get("PACKET_OIDC_CLIENT_SECRET", "PLEASE_REPLACE_ME")

# SQLAlchemy config
SQLALCHEMY_DATABASE_URI = environ.get("PACKET_DATABASE_URI", None)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# LDAP config
LDAP_BIND_DN = environ.get("PACKET_LDAP_BIND_DN", None)
LDAP_BIND_PASS = environ.get("PACKET_LDAP_BIND_PASS", None)

# Firebase Config
FIREBASE_API_KEY = environ.get("PACKET_FIREBASE_API_KEY", None)
FIREBASE_AUTH_DOMAIN = environ.get("PACKET_FIREBASE_AUTH_DOMAIN", None)
FIREBASE_DATABASE_URL = environ.get("PACKET_FIREBASE_DATABASE_URL", None)
FIREBASE_PROJECT_ID = environ.get("PACKET_FIREBASE_PROJECT_ID", None)
FIREBASE_STORAGE_BUCKET = environ.get("PACKET_FIREBASE_STORAGE_BUCKET", None)
FIREBASE_SENDER_ID = environ.get("PACKET_FIREBASE_SENDER_ID", None)
FIREBASE_APP_ID = environ.get("PACKET_FIREBASE_APP_ID", None)
FIREBASE_VAPID_KEY = environ.get("PACKET_FIREBASE_VAPID_KEY", None)

# Slack URL for pushing to #general
SLACK_WEBHOOK_URL = environ.get("PACKET_SLACK_URL", None)
