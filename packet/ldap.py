from functools import lru_cache

from packet import _ldap


@lru_cache(maxsize=4096)
def _ldap_get_group_members(group):
    return _ldap.get_group(group).get_members()


@lru_cache(maxsize=4096)
def _ldap_is_member_of_group(member, group):
    group_list = member.get("memberOf")
    for group_dn in group_list:
        if group == group_dn.split(",")[0][3:]:
            return True
    return False


@lru_cache(maxsize=2048)
def _ldap_is_member_of_directorship(account, directorship):
    directors = _ldap.get_directorship_heads(directorship)
    for director in directors:
        if director.uid == account.uid:
            return True
    return False


# Getters

@lru_cache(maxsize=4096)
def ldap_get_member(username):
    return _ldap.get_member(username, uid=True)


@lru_cache(maxsize=1024)
def ldap_get_active_members():
    return _ldap_get_group_members("active")


@lru_cache(maxsize=1024)
def ldap_get_intro_members():
    return _ldap_get_group_members("intromembers")


@lru_cache(maxsize=1024)
def ldap_get_onfloor_members():
    return _ldap_get_group_members("onfloor")


@lru_cache(maxsize=1024)
def ldap_get_groups(account):
    group_list = account.get("memberOf")
    groups = []
    for group_dn in group_list:
        if "cn=groups,cn=accounts" in group_dn:
            groups.append(group_dn.split(",")[0][3:])
    return groups


@lru_cache(maxsize=1024)
def ldap_get_eboard():
    members = _ldap_get_group_members("eboard-chairman") + _ldap_get_group_members("eboard-evaluations"
        ) + _ldap_get_group_members("eboard-financial") + _ldap_get_group_members("eboard-history"
        ) + _ldap_get_group_members("eboard-imps") + _ldap_get_group_members("eboard-opcomm"
        ) + _ldap_get_group_members("eboard-research") + _ldap_get_group_members("eboard-social"
        ) + _ldap_get_group_members("eboard-pr")

    return members


@lru_cache(maxsize=2048)
def ldap_get_live_onfloor():
    """
    :return: All upperclassmen who live on floor and are not eboard
    """
    members = []
    onfloor = ldap_get_onfloor_members()
    for member in onfloor:
        if ldap_get_roomnumber(member) and not ldap_is_eboard(member):
            members.append(member)
    return members


# Status checkers

@lru_cache(maxsize=1024)
def ldap_is_active(account):
    return _ldap_is_member_of_group(account, 'active')


@lru_cache(maxsize=1024)
def ldap_is_alumni(account):
    # If the user is not active, they are an alumni.
    return not _ldap_is_member_of_group(account, 'active')


@lru_cache(maxsize=1024)
def ldap_is_eboard(account):
    return _ldap_is_member_of_group(account, 'eboard')


@lru_cache(maxsize=1024)
def ldap_is_rtp(account):
    return _ldap_is_member_of_group(account, 'rtp')


@lru_cache(maxsize=1024)
def ldap_is_intromember(account):
    return _ldap_is_member_of_group(account, 'intromembers')


@lru_cache(maxsize=1024)
def ldap_is_onfloor(account):
    return _ldap_is_member_of_group(account, 'onfloor')


@lru_cache(maxsize=1024)
def ldap_is_current_student(account):
    return _ldap_is_member_of_group(account, 'current_student')


@lru_cache(maxsize=1024)
def ldap_get_roomnumber(account):
    try:
        return account.roomNumber
    except AttributeError:
        return None
