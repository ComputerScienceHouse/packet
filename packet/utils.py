# Credit to Liam Middlebrook and Ram Zallan
# https://github.com/liam-middlebrook/gallery
from functools import wraps

import requests
from flask import session

from packet import _ldap, app
from packet.ldap import (ldap_get_member,
                         ldap_is_active,
                         ldap_is_onfloor,
                         ldap_get_roomnumber,
                         ldap_get_groups)
from packet.models import Freshman

INTRO_REALM = "https://sso.csh.rit.edu/auth/realms/intro"


def before_request(func):
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        uid = str(session["userinfo"].get("preferred_username", ""))

        if session["id_token"]["iss"] == INTRO_REALM:
            info = {
                "realm": "intro",
                "uid": uid
            }
        else:
            uuid = str(session["userinfo"].get("sub", ""))
            user_obj = _ldap.get_member(uid, uid=True)
            info = {
                "realm": "csh",
                "uuid": uuid,
                "uid": uid,
                "user_obj": user_obj,
                "member_info": get_member_info(uid),
                "color": requests.get('https://themeswitcher.csh.rit.edu/api/colour').content
            }

        kwargs["info"] = info
        return func(*args, **kwargs)

    return wrapped_function


def get_member_info(uid):
    account = ldap_get_member(uid)

    member_info = {
        "user_obj": account,
        "group_list": ldap_get_groups(account),
        "uid": account.uid,
        "ritUid": parse_rit_uid(account.ritDn),
        "name": account.cn,
        "active": ldap_is_active(account),
        "onfloor": ldap_is_onfloor(account),
        "room": ldap_get_roomnumber(account),
        "hp": account.housingPoints,
        "plex": account.plex,
        "rn": ldap_get_roomnumber(account),
        "birthday": parse_date(account.birthday),
        "memberSince": parse_date(account.memberSince),
        "lastlogin": parse_date(account.krblastsuccessfulauth),
        "year": parse_account_year(account.memberSince)
    }
    return member_info


def parse_date(date):
    if date:
        year = date[0:4]
        month = date[4:6]
        day = date[6:8]
        return month + "-" + day + "-" + year
    return False


def parse_rit_uid(dn):
    if dn:
        return dn.split(",")[0][4:]

    return None


def parse_account_year(date):
    if date:
        year = int(date[0:4])
        month = int(date[4:6])
        if month <= 8:
            year = year - 1
        return year
    return None


@app.context_processor
def utility_processor():
    # pylint: disable=bare-except
    def get_display_name(username):
        try:
            member = ldap_get_member(username)
            return member.cn + " (" + member.uid + ")"
        except:
            return username

    def get_freshman_name(username):
        try:
            freshman = Freshman.query.filter_by(rit_username=username).first()
            return freshman.name + " (" + freshman.rit_username + ")"
        except:
            return username

    return dict(get_display_name=get_display_name, get_freshman_name=get_freshman_name)
