# Credit to Liam Middlebrook and Ram Zallan
# https://github.com/liam-middlebrook/gallery
from functools import wraps, lru_cache

import requests
from flask import session

from packet import _ldap, auth, app
from packet.models import Freshman
from packet.ldap import (ldap_get_member,
                         ldap_is_active,
                         ldap_is_onfloor,
                         ldap_get_roomnumber,
                         ldap_get_groups,
                         ldap_is_intromember)

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
    freshman = Freshman.query.filter_by(rit_username=uid).first()
    if freshman is not None:
        return freshman.onfloor
    else:
        return False


def packet_auth(func):
    """
    Decorator for easily configuring oidc
    """
    @auth.oidc_auth
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        if app.config["REALM"] == "csh":
            username = str(session["userinfo"].get("preferred_username", ""))
            if ldap_is_intromember(ldap_get_member(username)):
                app.logger.warn("Stopped intro member {} from accessing upperclassmen packet".format(username))
                return "Sorry, upperclassmen packet is not available to intro members.", 401

        return func(*args, **kwargs)

    return wrapped_function

def notify_slack(name: str):
    """
    Sends a congratulate on sight decree to Slack
    """
    if app.config["SLACK_WEBHOOK_URL"] is None:
        app.logger.warn("SLACK_WEBHOOK_URL not configured, not sending message to slack.")
        return

    msg = f'{name} got :100: on packet. Shower on sight.'
    requests.put(app.config["SLACK_WEBHOOK_URL"], json={'text':msg})
    app.logger.info("Posted 100% notification to slack for " + name)
