"""
Helper functions for working with the csh_ldap library
"""

from functools import lru_cache

from packet import _ldap


def _ldap_get_group_members(group):
    """
    :return: A list of CSHMember instances
    """
    return _ldap.get_group(group).get_members()


def _ldap_is_member_of_group(member, group):
    """
    :param member: A CSHMember instance
    """
    for group_dn in member.get("memberOf"):
        if group == group_dn.split(",")[0][3:]:
            return True

    return False


# Getters

@lru_cache(maxsize=256)
def ldap_get_member(username):
    """
    :return: A CSHMember instance
    """
    return _ldap.get_member(username, uid=True)


def ldap_get_active_members():
    """
    Gets all current, dues-paying members
    :return: A list of CSHMember instances
    """
    return _ldap_get_group_members("active")


def ldap_get_intro_members():
    """
    Gets all freshmen members
    :return: A list of CSHMember instances
    """
    return _ldap_get_group_members("intromembers")


def ldap_get_eboard():
    """
    Gets all voting members of eboard
    :return: A list of CSHMember instances
    """
    members = _ldap_get_group_members("eboard-chairman") + _ldap_get_group_members("eboard-evaluations"
        ) + _ldap_get_group_members("eboard-financial") + _ldap_get_group_members("eboard-history"
        ) + _ldap_get_group_members("eboard-imps") + _ldap_get_group_members("eboard-opcomm"
        ) + _ldap_get_group_members("eboard-research") + _ldap_get_group_members("eboard-social"
        ) + _ldap_get_group_members("eboard-pr")

    return members


def ldap_get_live_onfloor():
    """
    All upperclassmen who live on floor and are not eboard
    :return: A list of CSHMember instances
    """
    members = []
    onfloor = _ldap_get_group_members("onfloor")
    for member in onfloor:
        if ldap_get_roomnumber(member) and not ldap_is_eboard(member):
            members.append(member)

    return members


# Status checkers

def ldap_is_eboard(member):
    """
    :param member: A CSHMember instance
    """
    return _ldap_is_member_of_group(member, "eboard")


def ldap_is_intromember(member):
    """
    :param member: A CSHMember instance
    """
    return _ldap_is_member_of_group(member, "intromembers")


def ldap_get_roomnumber(member):
    """
    :param member: A CSHMember instance
    """
    try:
        return member.roomNumber
    except AttributeError:
        return None
