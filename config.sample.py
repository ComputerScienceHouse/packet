P = '127.0.0.1'
PORT = '8080'
SERVER_NAME = 'localhost:8080'
SECRET_KEY = ''

# LDAP config
LDAP_URL = 'ldaps://ldap.csh.rit.edu:636'
LDAP_BIND_DN = 'cn=packet,ou=Apps,dc=csh,dc=rit,dc=edu'
LDAP_BIND_PW = ''
LDAP_USER_OU = 'ou=Users,dc=csh,dc=rit,dc=edu'

# OpenID Connect SSO config
OIDC_ISSUER = 'https://sso.csh.rit.edu/realms/csh'
OIDC_CLIENT_CONFIG = {
    'client_id': 'packet',
    'client_secret': '',
    'post_logout_redirect_uris': ['http://localhost:8080/logout']
}
