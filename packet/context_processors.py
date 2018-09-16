"""
Context processors used by the jinja templates
"""

from functools import lru_cache
from datetime import datetime

from packet.ldap import ldap_get_member
from packet.models import Freshman
from packet import app


# pylint: disable=bare-except
@lru_cache(maxsize=128)
def get_csh_name(username):
    try:
        member = ldap_get_member(username)
        return member.cn + " (" + member.uid + ")"
    except:
        return username


# pylint: disable=bare-except
@lru_cache(maxsize=128)
def get_rit_name(username):
    try:
        freshman = Freshman.query.filter_by(rit_username=username).first()
        return freshman.name + " (" + username + ")"
    except:
        return username


def log_time(label):
    """
    Used during debugging to log timestamps while rendering templates
    """
    print(label, datetime.now())


@app.context_processor
def utility_processor():
    return dict(get_csh_name=get_csh_name, get_rit_name=get_rit_name, log_time=log_time)
