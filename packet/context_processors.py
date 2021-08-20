"""
Context processors used by the jinja templates
"""
import hashlib
import urllib
from functools import lru_cache
from datetime import datetime
from typing import Callable

from packet.models import Freshman, UpperSignature
from packet import app, ldap


# pylint: disable=bare-except
@lru_cache(maxsize=128)
def get_csh_name(username: str) -> str:
    try:
        member = ldap.get_member(username)
        return member.cn + ' (' + member.uid + ')'
    except:
        return username


def get_roles(sig: UpperSignature) -> dict[str, str]:
    """
    Converts a signature's role fields to a dict for ease of access.
    :return: A dictionary of role short names to role long names
    """
    out = {}
    if sig.eboard:
        out['eboard'] = sig.eboard
    if sig.active_rtp:
        out['rtp'] = 'RTP'
    if sig.three_da:
        out['three_da'] = '3DA'
    if sig.w_m:
        out['wm'] = 'Wiki Maintainer'
    if sig.webmaster:
        out['webmaster'] = 'Webmaster'
    if sig.c_m:
        out['cm'] = 'Constitutional Maintainer'
    if sig.drink_admin:
        out['drink'] = 'Drink Admin'
    return out


# pylint: disable=bare-except
@lru_cache(maxsize=256)
def get_rit_name(username: str) -> str:
    try:
        freshman = Freshman.query.filter_by(rit_username=username).first()
        return freshman.name + ' (' + username + ')'
    except:
        return username


# pylint: disable=bare-except
@lru_cache(maxsize=256)
def get_rit_image(username: str) -> str:
    if username:
        addresses = [username + '@rit.edu', username + '@g.rit.edu']
        for addr in addresses:
            url = 'https://gravatar.com/avatar/' + hashlib.md5(addr.encode('utf8')).hexdigest() + '.jpg?d=404&s=250'
            try:
                gravatar = urllib.request.urlopen(url)
                if gravatar.getcode() == 200:
                    return url
            except:
                continue
    return 'https://www.gravatar.com/avatar/freshmen?d=mp&f=y'


def log_time(label: str) -> None:
    """
    Used during debugging to log timestamps while rendering templates
    """
    print(label, datetime.now())


@app.context_processor
def utility_processor() -> dict[str, Callable]:
    return dict(
        get_csh_name=get_csh_name, get_rit_name=get_rit_name, get_rit_image=get_rit_image, log_time=log_time,
        get_roles=get_roles
    )
