from os import environ

# Flask config
DEBUG = False
IP = environ.get("PACKET_IP", "localhost")
PORT = environ.get("PACKET_PORT", "8000")
SERVER_NAME = environ.get("PACKET_SERVER_NAME", IP + ":" + PORT)
SECRET_KEY = environ.get("PACKET_SECRET_KEY", "PLEASE_REPLACE_ME")

# OpenID Connect SSO config
OIDC_ISSUER = environ.get("PACKET_OIDC_ISSUER", "https://sso.csh.rit.edu/auth/realms/csh")
OIDC_CLIENT_ID = environ.get("PACKET_OIDC_CLIENT_ID", "packet")
OIDC_CLIENT_SECRET = environ.get("PACKET_OIDC_CLIENT_SECRET", "PLEASE_REPLACE_ME")

# SAML config
SAML_METADATA_URL = environ.get("PACKET_SAML_METADATA_URL", "https://shibboleth.main.ad.rit.edu/rit-metadata.xml")

# SQLAlchemy config
SQLALCHEMY_DATABASE_URI = environ.get("PACKET_DATABASE_URI", None)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# LDAP
LDAP_BIND_DN = environ.get("LDAP_BIND_DN", "PLEASE REPLACE ME")
LDAP_BIND_PASS = environ.get("LDAP_BIND_PASS", None)
