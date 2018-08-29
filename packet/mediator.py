from . import ldap

def get_upperclassmen_signatures():
    upperclassmen = ldap.ldap_get_active_members()
    return upperclassmen

