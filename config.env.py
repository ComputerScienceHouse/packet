"""
Default configuration settings and environment variable based configuration logic
    See the readme for more information
"""
from distutils.util import strtobool
from os import environ, path, getcwd

# Flask config
DEBUG = False
IP = environ.get("PACKET_IP", "localhost")
PORT = environ.get("PACKET_PORT", "8000")
PROTOCOL = environ.get("PACKET_PROTOCOL", "https://")
SERVER_NAME = environ.get("PACKET_SERVER_NAME", IP + ":" + PORT)
SECRET_KEY = environ.get("PACKET_SECRET_KEY", "PLEASE_REPLACE_ME")

# Logging config
LOG_LEVEL = environ.get("PACKET_LOG_LEVEL", "INFO")
ANALYTICS_ID = environ.get("ANALYTICS_ID", "UA-420696-9")

# OpenID Connect SSO config
REALM = environ.get("PACKET_REALM", "csh")

OIDC_ISSUER = environ.get("PACKET_OIDC_ISSUER", "https://sso.csh.rit.edu/auth/realms/csh")
OIDC_CLIENT_ID = environ.get("PACKET_OIDC_CLIENT_ID", "packet")
OIDC_CLIENT_SECRET = environ.get("PACKET_OIDC_CLIENT_SECRET", "PLEASE_REPLACE_ME")

# SQLAlchemy config
SQLALCHEMY_DATABASE_URI = environ.get("PACKET_DATABASE_URI", "postgresql://postgres:mysecretpassword@localhost:5432/postgres")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# LDAP config
LDAP_BIND_DN = environ.get("PACKET_LDAP_BIND_DN", None)
LDAP_BIND_PASS = environ.get("PACKET_LDAP_BIND_PASS", None)
LDAP_MOCK_MEMBERS = [
        {'uid':'evals', 'groups': ['eboard', 'eboard-evaluations', 'active']},
        {'uid':'imps-3da', 'groups': ['eboard', 'eboard-imps', '3da', 'active']},
        {
            'uid':'rtp-cm-webs-onfloor',
            'groups': ['active-rtp', 'rtp', 'constitutional_maintainers', 'webmaster', 'active', 'onfloor'],
            'room_number': 1024
        },
        {'uid':'misc-rtp', 'groups': ['rtp']},
        {'uid':'onfloor', 'groups': ['active', 'onfloor'], 'room_number': 1024},
        {'uid':'active-offfloor', 'groups': ['active']},
        {'uid':'alum', 'groups': ['member']},
    ]

# Mail Config
MAIL_PROD = strtobool(environ.get("PACKET_MAIL_PROD", "False"))
MAIL_SERVER = environ.get("PACKET_MAIL_SERVER", "thoth.csh.rit.edu")
MAIL_USERNAME = environ.get("PACKET_MAIL_USERNAME", "packet@csh.rit.edu")
MAIL_PASSWORD = environ.get("PACKET_MAIL_PASSWORD", None)
MAIL_USE_TLS = strtobool(environ.get("PACKET_MAIL_TLS", "True"))

# OneSignal Config
ONESIGNAL_USER_AUTH_KEY = environ.get("PACKET_ONESIGNAL_USER_AUTH_KEY", None)
ONESIGNAL_CSH_APP_AUTH_KEY = environ.get("PACKET_ONESIGNAL_CSH_APP_AUTH_KEY", None)
ONESIGNAL_CSH_APP_ID = environ.get("PACKET_ONESIGNAL_CSH_APP_ID", "6eff123a-0852-4027-804e-723044756f00")
ONESIGNAL_INTRO_APP_AUTH_KEY = environ.get("PACKET_ONESIGNAL_INTRO_APP_AUTH_KEY", None)
ONESIGNAL_INTRO_APP_ID = environ.get("PACKET_ONESIGNAL_INTRO_APP_ID", "6eff123a-0852-4027-804e-723044756f00")

# Sentry Config
SENTRY_DSN = environ.get("PACKET_SENTRY_DSN", "")

# Slack URL for pushing to #general
SLACK_WEBHOOK_URL = environ.get("PACKET_SLACK_URL", None)

# Packet Config
PACKET_UPPER = environ.get("PACKET_UPPER", "packet.csh.rit.edu")
PACKET_INTRO = environ.get("PACKET_INTRO", "freshmen-packet.csh.rit.edu")
