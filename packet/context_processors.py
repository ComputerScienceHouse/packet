"""
Context processors used by the jinja templates
"""

import hashlib
import urllib
from functools import lru_cache
from datetime import datetime
from typing import Callable, Union

from csh_ldap import CSHMember

from packet.models import Freshman, UpperSignature
from packet import app
from packet.ldap import ldap


@lru_cache(maxsize=128)
def get_csh_name(username: str) -> str:
    """
    Get the full name of a user from their CSH username.

    Args:
        username: The CSH username of the user.

    Returns:
        The full name of the user or the username if not found.
    """

    try:
        member: CSHMember = ldap.get_member(username)
        return member.cn + ' (' + member.uid + ')'
    except Exception:
        return username


def get_roles(sig: UpperSignature) -> dict[str, Union[str, None]]:
    """
    Converts a signature's role fields to a dict for ease of access.

    Args:
        sig: The signature object to extract roles from.

    Returns:
        A dictionary mapping role short names to role long names.
    """

    return {
        'eboard': sig.eboard if sig.eboard else None,
        'rtp': 'RTP' if sig.active_rtp else None,
        'three_da': '3DA' if sig.three_da else None,
        'wm': 'Wiki Maintainer' if sig.w_m else None,
        'webmaster': 'Webmaster' if sig.webmaster else None,
        'cm': 'Constitutional Maintainer' if sig.c_m else None,
        'drink': 'Drink Admin' if sig.drink_admin else None,
    }


@lru_cache(maxsize=256)
def get_rit_name(username: str) -> str:
    """
    Get the full name of a user from their RIT username.

    Args:
        username: The RIT username of the user.

    Returns:
        The full name of the user or the username if not found.
    """

    try:
        freshman: Freshman = Freshman.query.filter_by(rit_username=username).first()

        return freshman.name + ' (' + username + ')'
    except Exception:
        return username


@lru_cache(maxsize=256)
def get_rit_image(username: str) -> str:
    """
    Get the RIT image URL for a given username.

    Args:
        username: The username of the user to retrieve the RIT image for.

    Returns:
        The URL of the user's RIT image or a default image URL.
    """

    addresses: list[str] = [username + '@rit.edu', username + '@g.rit.edu']

    if not username:
        # If no username is provided, return a default image URL
        addresses = []

    for addr in addresses:
        url: str = 'https://gravatar.com/avatar/' + hashlib.md5(addr.encode('utf8')).hexdigest() + '.jpg?d=404&s=250'

        try:
            with urllib.request.urlopen(url) as gravatar:
                if gravatar.getcode() == 200:
                    return url

        except Exception:
            continue

    return 'https://www.gravatar.com/avatar/freshmen?d=mp&f=y'


def log_time(label: str) -> None:
    """
    Used during debugging to log timestamps while rendering templates

    Args:
        label: The label to log.
    """

    print(label, datetime.now())


@app.context_processor
def utility_processor() -> dict[str, Callable]:
    """
    Provides utility functions for Jinja templates.

    Returns:
        A dictionary of utility functions.
    """

    return dict(
        get_csh_name=get_csh_name,
        get_rit_name=get_rit_name,
        get_rit_image=get_rit_image,
        log_time=log_time,
        get_roles=get_roles,
    )
