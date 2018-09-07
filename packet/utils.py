# Credit to Liam Middlebrook and Ram Zallan
# https://github.com/liam-middlebrook/gallery
from functools import wraps, lru_cache

import requests
from flask import session

from packet import _ldap, app
from packet.ldap import (ldap_get_member,
                         ldap_is_active,
                         ldap_is_onfloor,
                         ldap_get_roomnumber,
                         ldap_get_groups)
from packet.models import FreshSignature, UpperSignature, MiscSignature
from packet.packet import get_current_packet, get_freshman

INTRO_REALM = "https://sso.csh.rit.edu/auth/realms/intro"


def before_request(func):
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        uid = str(session["userinfo"].get("preferred_username", ""))

        if session["id_token"]["iss"] == INTRO_REALM:
            info = {
                "realm": "intro",
                "uid": uid,
                "onfloor": is_on_floor(uid)
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


@lru_cache(maxsize=2048)
def get_member_info(uid):
    account = ldap_get_member(uid)

    member_info = {
        "user_obj": account,
        "group_list": ldap_get_groups(account),
        "uid": account.uid,
        "name": account.cn,
        "active": ldap_is_active(account),
        "onfloor": ldap_is_onfloor(account),
        "room": ldap_get_roomnumber(account),
    }
    return member_info


@lru_cache(maxsize=2048)
def is_on_floor(uid):
    return get_freshman(uid).onfloor


@lru_cache(maxsize=2048)
def signed_packet(signer, freshman):
    packet = get_current_packet(freshman)
    freshman_signature = FreshSignature.query.filter_by(packet=packet, freshman_username=signer, signed=True).first()
    upper_signature = UpperSignature.query.filter_by(packet=packet, member=signer, signed=True).first()
    misc_signature = MiscSignature.query.filter_by(packet=packet, member=signer).first()

    if freshman_signature is not None:
        return freshman_signature.signed
    if upper_signature is not None:
        return upper_signature.signed
    if misc_signature is not None:
        return misc_signature
    return False


@app.context_processor
def utility_processor():
    # pylint: disable=bare-except
    @lru_cache(maxsize=4096)
    def get_display_name(username):
        try:
            member = ldap_get_member(username)
            return member.cn + " (" + member.uid + ")"
        except:
            return username

    return dict(get_display_name=get_display_name)
