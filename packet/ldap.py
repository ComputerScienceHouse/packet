"""
Helper functions for working with the csh_ldap library
"""

from functools import lru_cache
from datetime import date

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
        )

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


def ldap_get_active_rtps():
    """
    All active RTPs
    :return: A list of CSHMember instances
    """
    return [member.uid for member in _ldap_get_group_members("active_rtp")]


def ldap_get_3das():
    """
    All 3das
    :return: A list of CSHMember instances
    """
    return [member.uid for member in _ldap_get_group_members("3da")]


def ldap_get_webmasters():
    """
    All webmasters
    :return: A list of CSHMember instances
    """
    return [member.uid for member in _ldap_get_group_members("webmaster")]


def ldap_get_constitutional_maintainers():
    """
    All constitutional maintainers
    :return: A list of CSHMember instances
    """
    return [member.uid for member in _ldap_get_group_members("constitutional_maintainers")]


def ldap_get_drink_admins():
    """
    All drink admins
    :return: A list of CSHMember instances
    """
    return [member.uid for member in _ldap_get_group_members("drink")]


def ldap_get_eboard_role(member):
    """
    :param member: A CSHMember instance
    :return: A String or None
    """

    return_val = None

    if _ldap_is_member_of_group(member, "eboard-chairman"):
        return_val = "Chairman"
    elif _ldap_is_member_of_group(member, "eboard-evaluations"):
        return_val = "Evals"
    elif _ldap_is_member_of_group(member, "eboard-financial"):
        return_val = "Financial"
    elif _ldap_is_member_of_group(member, "eboard-history"):
        return_val = "History"
    elif _ldap_is_member_of_group(member, "eboard-imps"):
        return_val = "Imps"
    elif _ldap_is_member_of_group(member, "eboard-opcomm"):
        return_val = "OpComm"
    elif _ldap_is_member_of_group(member, "eboard-research"):
        return_val = "R&D"
    elif _ldap_is_member_of_group(member, "eboard-social"):
        return_val = "Social"
    elif _ldap_is_member_of_group(member, "eboard-secretary"):
        return_val = "Secretary"

    return return_val

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


def ldap_is_on_coop(member):
    """
    :param member: A CSHMember instance
    """
    if date.today().month > 6:
        return _ldap_is_member_of_group(member, "fall_coop")
    else:
        return _ldap_is_member_of_group(member, "spring_coop")


def ldap_get_roomnumber(member):
    """
    :param member: A CSHMember instance
    """
    try:
        return member.roomNumber
    except AttributeError:
        return None
