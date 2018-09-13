from os import environ

# Flask config
DEBUG = False
IP = environ.get("PACKET_IP", "localhost")
PORT = environ.get("PACKET_PORT", "8000")
SERVER_NAME = environ.get("PACKET_SERVER_NAME", IP + ":" + PORT)
SECRET_KEY = environ.get("PACKET_SECRET_KEY", "PLEASE_REPLACE_ME")

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
