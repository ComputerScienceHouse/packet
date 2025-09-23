"""
General utilities and decorators for supporting the Python logic
"""

from datetime import datetime, timedelta
from functools import wraps, lru_cache
from typing import Any, Callable, TypeVar, cast
from urllib.parse import urlparse

import requests
from flask import session, redirect, request

from packet import auth, app, db
from packet.ldap import ldap
from packet.mail import send_start_packet_mail
from packet.models import (
    Freshman,
    FreshSignature,
    Packet,
    UpperSignature,
    MiscSignature,
)
from packet.notifications import (
    packets_starting_notification,
    packet_starting_notification,
)

INTRO_REALM = 'https://sso.csh.rit.edu/auth/realms/intro'

WrappedFunc = TypeVar('WrappedFunc', bound=Callable)


def before_request(func: WrappedFunc) -> WrappedFunc:
    """
    Decorator to run a function before a request.

    Args:
        func (WrappedFunc): The function to wrap.

    Returns:
        WrappedFunc: The wrapped function.

    Notes:
        Credit to Liam Middlebrook and Ram Zallan
        https://github.com/liam-middlebrook/gallery
    """

    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        """
        Run the wrapped function before a request.

        Args:
            *args: Positional arguments to pass to the wrapped function.
            **kwargs: Keyword arguments to pass to the wrapped function.

        Returns:
            Any: The return value of the wrapped function.
        """

        uid = str(session['userinfo'].get('preferred_username', ''))

        if session['id_token']['iss'] == INTRO_REALM:
            info = {
                'realm': 'intro',
                'uid': uid,
                'onfloor': is_freshman_on_floor(uid),
                'admin': False,  # It's always false if frosh
                'ritdn': uid,
                'is_upper': False,  # Always fals in intro realm
            }
        else:
            member = ldap.get_member(uid)
            info = {
                'realm': 'csh',
                'uid': uid,
                'admin': ldap.is_evals(member),
                'groups': ldap.get_groups(member),
                'ritdn': member.ritdn,
                'is_upper': not is_frosh(),
            }

        kwargs['info'] = info
        return func(*args, **kwargs)

    return cast(WrappedFunc, wrapped_function)


@lru_cache(maxsize=128)
def is_freshman_on_floor(rit_username: str) -> bool:
    """
    Checks if a freshman is on floor

    Args:
        rit_username (str): The RIT username of the freshman.

    Returns:
        bool: True if the freshman is on floor, False otherwise.
    """

    freshman = Freshman.query.filter_by(rit_username=rit_username).first()

    if freshman is None:
        return False

    return freshman.onfloor


@app.before_request
def before_request_callback() -> Any:
    """
    Pre-request function to ensure we're on the right URL before OIDC sees anything

    Returns:
        Any: The return value of the wrapped function.
    """

    url = urlparse(request.base_url)

    if url.netloc != app.config['SERVER_NAME']:
        return redirect(
            request.base_url.replace(urlparse(request.base_url).netloc, app.config['SERVER_NAME']),
            code=302,
        )

    return None


def packet_auth(func: WrappedFunc) -> WrappedFunc:
    """
    Decorator for easily configuring oidc

    Args:
        func (WrappedFunc): The function to wrap.

    Returns:
        WrappedFunc: The wrapped function.
    """

    @auth.oidc_auth('app')
    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        """
        Run the wrapped function with OIDC authentication.

        Args:
            *args: Positional arguments to pass to the wrapped function.
            **kwargs: Keyword arguments to pass to the wrapped function.

        Returns:
            Any: The return value of the wrapped function.
        """

        if app.config['REALM'] == 'csh':
            username: str = str(session['userinfo'].get('preferred_username', ''))

            if ldap.is_intromember(ldap.get_member(username)):
                app.logger.warn('Stopped intro member {} from accessing upperclassmen packet'.format(username))
                return redirect(app.config['PROTOCOL'] + app.config['PACKET_INTRO'], code=301)

        return func(*args, **kwargs)

    return cast(WrappedFunc, wrapped_function)


def admin_auth(func: WrappedFunc) -> WrappedFunc:
    """
    Decorator for easily configuring oidc

    Args:
        func (WrappedFunc): The function to wrap.

    Returns:
        WrappedFunc: The wrapped function.
    """

    @auth.oidc_auth('app')
    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        """
        Run the wrapped function with OIDC authentication.

        Args:
            *args: Positional arguments to pass to the wrapped function.
            **kwargs: Keyword arguments to pass to the wrapped function.

        Returns:
            Any: The return value of the wrapped function.
        """

        if app.config['REALM'] == 'csh':
            username: str = str(session['userinfo'].get('preferred_username', ''))
            member = ldap.get_member(username)

            if not ldap.is_evals(member):
                app.logger.warn('Stopped member {} from accessing admin UI'.format(username))

                return redirect(app.config['PROTOCOL'] + app.config['PACKET_UPPER'], code=301)
        else:
            return redirect(app.config['PROTOCOL'] + app.config['PACKET_INTRO'], code=301)

        return func(*args, **kwargs)

    return cast(WrappedFunc, wrapped_function)


def notify_slack(name: str) -> None:
    """
    Sends a congratulate on sight decree to Slack

    Args:
        name (str): The name of the user to congratulate.
    """

    if app.config['SLACK_WEBHOOK_URL'] is None:
        app.logger.warn('SLACK_WEBHOOK_URL not configured, not sending message to slack.')
        return

    msg: str = f':pizza-party: {name} got :100: on packet! :pizza-party:'
    requests.put(app.config['SLACK_WEBHOOK_URL'], json={'text': msg})
    app.logger.info('Posted 100% notification to slack for ' + name)


def sync_freshman(freshmen_list: dict) -> None:
    """
    Sync the list of freshmen with the database.

    Args:
        freshmen_list (dict): A dictionary of freshmen data.
    """

    freshmen_in_db = {freshman.rit_username: freshman for freshman in Freshman.query.all()}

    for list_freshman in freshmen_list.values():
        if list_freshman.rit_username not in freshmen_in_db:
            # This is a new freshman so add them to the DB
            freshmen_in_db[list_freshman.rit_username] = Freshman(
                rit_username=list_freshman.rit_username,
                name=list_freshman.name,
                onfloor=list_freshman.onfloor,
            )
            db.session.add(freshmen_in_db[list_freshman.rit_username])
        else:
            # This freshman is already in the DB so just update them
            freshmen_in_db[list_freshman.rit_username].onfloor = list_freshman.onfloor
            freshmen_in_db[list_freshman.rit_username].name = list_freshman.name

    # Update all freshmen entries that represent people who are no longer freshmen
    for freshman in filter(
        lambda freshman: freshman.rit_username not in freshmen_list,
        freshmen_in_db.values(),
    ):
        freshman.onfloor = False

    # Update the freshmen signatures of each open or future packet
    for packet in Packet.query.filter(Packet.end > datetime.now()).all():
        current_fresh_sigs = set(map(lambda fresh_sig: fresh_sig.freshman_username, packet.fresh_signatures))
        for list_freshman in filter(
            lambda list_freshman: list_freshman.rit_username not in current_fresh_sigs
            and list_freshman.rit_username != packet.freshman_username,
            freshmen_list.values(),
        ):
            db.session.add(FreshSignature(packet=packet, freshman=freshmen_in_db[list_freshman.rit_username]))

    db.session.commit()


def create_new_packets(base_date: datetime, freshmen_list: dict) -> None:
    """
    Create new packets for the given freshmen list.

    Args:
        base_date (datetime): The base date to use for the packet creation.
        freshmen_list (dict): A dictionary of freshmen data.
    """

    start = base_date
    end = base_date + timedelta(days=14)

    app.logger.info('Fetching data from LDAP...')
    all_upper = list(
        filter(
            lambda member: not ldap.is_intromember(member) and not ldap.is_on_coop(member),
            ldap.get_active_members(),
        )
    )

    rtp = ldap.get_active_rtps()
    three_da = ldap.get_3das()
    webmaster = ldap.get_webmasters()
    c_m = ldap.get_constitutional_maintainers()
    w_m = ldap.get_wiki_maintainers()
    drink = ldap.get_drink_admins()

    # Packet starting notifications
    packets_starting_notification(start)

    # Create the new packets and the signatures for each freshman in the given CSV
    app.logger.info('Creating DB entries and sending emails...')
    for freshman in Freshman.query.filter(cast(Any, Freshman.rit_username).in_(freshmen_list)).all():
        packet = Packet(freshman=freshman, start=start, end=end)
        db.session.add(packet)
        send_start_packet_mail(packet)
        packet_starting_notification(packet)

        for member in all_upper:
            sig = UpperSignature(packet=packet, member=member.uid)
            sig.eboard = ldap.get_eboard_role(member)
            sig.active_rtp = member.uid in rtp
            sig.three_da = member.uid in three_da
            sig.webmaster = member.uid in webmaster
            sig.c_m = member.uid in c_m
            sig.w_m = member.uid in w_m
            sig.drink_admin = member.uid in drink
            db.session.add(sig)

        for frosh in Freshman.query.filter(Freshman.rit_username != freshman.rit_username).all():
            db.session.add(FreshSignature(packet=packet, freshman=frosh))

    db.session.commit()


def sync_with_ldap() -> None:
    """
    Sync the local database with the LDAP directory.
    """

    app.logger.info('Fetching data from LDAP...')
    all_upper = {
        member.uid: member
        for member in filter(
            lambda member: not ldap.is_intromember(member) and not ldap.is_on_coop(member),
            ldap.get_active_members(),
        )
    }

    rtp = ldap.get_active_rtps()
    three_da = ldap.get_3das()
    webmaster = ldap.get_webmasters()
    c_m = ldap.get_constitutional_maintainers()
    w_m = ldap.get_wiki_maintainers()
    drink = ldap.get_drink_admins()

    app.logger.info('Applying updates to the DB...')
    for packet in Packet.query.filter(Packet.end > datetime.now()).all():
        # Update the role state of all UpperSignatures
        for sig in filter(lambda sig: sig.member in all_upper, packet.upper_signatures):
            sig.eboard = ldap.get_eboard_role(all_upper[sig.member])
            sig.active_rtp = sig.member in rtp
            sig.three_da = sig.member in three_da
            sig.webmaster = sig.member in webmaster
            sig.c_m = sig.member in c_m
            sig.w_m = sig.member in w_m
            sig.drink_admin = sig.member in drink

        # Migrate UpperSignatures that are from accounts that are not active anymore
        for sig in filter(lambda sig: sig.member not in all_upper, packet.upper_signatures):
            UpperSignature.query.filter_by(packet_id=packet.id, member=sig.member).delete()
            if sig.signed:
                sig = MiscSignature(packet=packet, member=sig.member)
                db.session.add(sig)

        # Migrate MiscSignatures that are from accounts that are now active members
        for sig in filter(lambda sig: sig.member in all_upper, packet.misc_signatures):
            MiscSignature.query.filter_by(packet_id=packet.id, member=sig.member).delete()
            sig = UpperSignature(packet=packet, member=sig.member, signed=True)
            sig.eboard = ldap.get_eboard_role(all_upper[sig.member])
            sig.active_rtp = sig.member in rtp
            sig.three_da = sig.member in three_da
            sig.webmaster = sig.member in webmaster
            sig.c_m = sig.member in c_m
            sig.w_m = sig.member in w_m
            sig.drink_admin = sig.member in drink
            db.session.add(sig)

        # Create UpperSignatures for any new active members
        upper_sigs = set(map(lambda sig: sig.member, packet.upper_signatures))
        for member in filter(lambda member: member not in upper_sigs, all_upper):
            sig = UpperSignature(packet=packet, member=member)
            sig.eboard = ldap.get_eboard_role(all_upper[sig.member])
            sig.active_rtp = sig.member in rtp
            sig.three_da = sig.member in three_da
            sig.webmaster = sig.member in webmaster
            sig.c_m = sig.member in c_m
            sig.w_m = sig.member in w_m
            sig.drink_admin = sig.member in drink
            db.session.add(sig)

    db.session.commit()


@auth.oidc_auth('app')
def is_frosh() -> bool:
    """
    Check if the current user is a freshman.

    Returns:
        bool: True if the user is a freshman, False otherwise.
    """

    if app.config['REALM'] == 'csh':
        username: str = str(session['userinfo'].get('preferred_username', ''))

        return ldap.is_intromember(ldap.get_member(username))

    # Always true for the intro realm
    return True
