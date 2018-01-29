import os

# Flask config
DEBUG=False
IP=os.environ.get('PACKET_IP', '0.0.0.0')
PORT=os.environ.get('PACKET_PORT', '8080')
SERVER_NAME = os.environ.get('PACKET_SERVER_NAME', 'packet-mbillow.csh.rit.edu')
SECRET_KEY = os.environ.get('PACKET_SECRET_KEY', '')

# LDAP config
LDAP_URL=os.environ.get('PACKET_LDAP_URL', 'ldaps://ldap.csh.rit.edu:636')
LDAP_BIND_DN=os.environ.get('PACKET_LDAP_BIND_DN', 'cn=packet,ou=Apps,dc=csh,dc=rit,dc=edu')
LDAP_BIND_PW=os.environ.get('PACKET_LDAP_BIND_PW', '')
LDAP_USER_OU=os.environ.get('PACKET_LDAP_USER_OU', 'ou=Users,dc=csh,dc=rit,dc=edu')

# OpenID Connect SSO config
OIDC_ISSUER = os.environ.get('PACKET_OIDC_ISSUER', 'https://sso.csh.rit.edu/realms/csh')
OIDC_CLIENT_CONFIG = {
    'client_id': os.environ.get('PACKET_OIDC_CLIENT_ID', 'packet'),
    'client_secret': os.environ.get('PACKET_OIDC_CLIENT_SECRET', ''),
    'post_logout_redirect_uris': [os.environ.get('PACKET_OIDC_LOGOUT_REDIRECT_URI',
                                                 'https://packet-mbillow.csh.rit.edu/logout')]
}
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'PACKET_DATABASE_URI',
    'sqlite:///{}'.format(os.path.join(os.getcwd(), 'data.db')))
SQLALCHEMY_TRACK_MODIFICATIONS = False

