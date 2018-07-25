from os import environ

# Flask config
DEBUG = False
IP = environ.get("PACKET_IP", "localhost")
PORT = environ.get("PACKET_PORT", "8000")
SERVER_NAME = environ.get("PACKET_SERVER_NAME", IP + ":" + PORT)
SECRET_KEY = environ.get("PACKET_SECRET_KEY", "PLEASE_REPLACE_ME")

# OpenID Connect SSO config
OIDC_ISSUER = environ.get("PACKET_OIDC_ISSUER", "https://sso.csh.rit.edu/auth/realms/csh")
OIDC_CLIENT_CONFIG = {
    "client_id": environ.get("PACKET_OIDC_CLIENT_ID", "packet"),
    "client_secret": environ.get("PACKET_OIDC_CLIENT_SECRET", "PLEASE_REPLACE_ME"),
    "post_logout_redirect_uris": [environ.get("PACKET_OIDC_LOGOUT_REDIRECT_URI", "https://" + SERVER_NAME + "/logout")]
}

# SQLAlchemy config
SQLALCHEMY_DATABASE_URI = environ.get("PACKET_DATABASE_URI", None)
SQLALCHEMY_TRACK_MODIFICATIONS = False