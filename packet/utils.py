from functools import wraps, lru_cache

import requests
from flask import session

from packet import auth, app
from packet.models import Freshman
from packet.ldap import ldap_get_member, ldap_is_intromember

INTRO_REALM = "https://sso.csh.rit.edu/auth/realms/intro"

def before_request(func):
    """
    Credit to Liam Middlebrook and Ram Zallan
    https://github.com/liam-middlebrook/gallery
    """
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
            info = {
                "realm": "csh",
                "uid": uid
            }

        kwargs["info"] = info
        return func(*args, **kwargs)

    return wrapped_function


@lru_cache(maxsize=128)
def is_on_floor(rit_username):
    """
    Checks if a freshman is on floor
    """
    freshman = Freshman.query.filter_by(rit_username=rit_username).first()
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
            if ldap_is_intromember(ldap_get_member(str(session["userinfo"].get("preferred_username", "")))):
                return "Sorry, upperclassmen packet is not available to intro members.", 401

        return func(*args, **kwargs)

    return wrapped_function


def notify_slack(name: str):
    """
    Sends a congratulate on sight decree to Slack.
    """
    if app.config["SLACK_WEBHOOK_URL"] is None:
        print("SLACK_WEBHOOK_URL not configured, not sending message to slack.")
        return
    msg = f'{name} got :100: on packet. Shower on sight.'
    requests.put(app.config["SLACK_WEBHOOK_URL"], json={'text':msg})
