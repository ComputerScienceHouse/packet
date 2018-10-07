"""
Helper functions for working with the csh_ldap library
"""

from functools import lru_cache

from packet import _ldap


def _ldap_get_group_members(group):
    return _ldap.get_group(group).get_members()


def _ldap_is_member_of_group(member, group):
    group_list = member.get("memberOf")
    for group_dn in group_list:
        if group == group_dn.split(",")[0][3:]:
            return True
    return False


# Getters

@lru_cache(maxsize=256)
def ldap_get_member(username):
    return _ldap.get_member(username, uid=True)


def ldap_get_active_members():
    return _ldap_get_group_members("active")


def ldap_get_intro_members():
    return _ldap_get_group_members("intromembers")


def ldap_get_eboard():
    members = _ldap_get_group_members("eboard-chairman") + _ldap_get_group_members("eboard-evaluations"
        ) + _ldap_get_group_members("eboard-financial") + _ldap_get_group_members("eboard-history"
        ) + _ldap_get_group_members("eboard-imps") + _ldap_get_group_members("eboard-opcomm"
        ) + _ldap_get_group_members("eboard-research") + _ldap_get_group_members("eboard-social"
        ) + _ldap_get_group_members("eboard-pr")

    return members


def ldap_get_live_onfloor():
    """
    :return: All upperclassmen who live on floor and are not eboard
    """
    members = []
    onfloor = _ldap_get_group_members("onfloor")
    for member in onfloor:
        if ldap_get_roomnumber(member) and not ldap_is_eboard(member):
            members.append(member)

    return members


# Status checkers

def ldap_is_eboard(account):
    return _ldap_is_member_of_group(account, 'eboard')


def ldap_is_intromember(account):
    return _ldap_is_member_of_group(account, 'intromembers')

def ldap_get_roomnumber(account):
    try:
        return account.roomNumber
    except AttributeError:
        return None
