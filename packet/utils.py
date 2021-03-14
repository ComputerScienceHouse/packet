"""
General utilities and decorators for supporting the Python logic
"""
from datetime import datetime, time, timedelta, date
from functools import wraps, lru_cache
from typing import Any, Callable, TypeVar, cast

import requests
from flask import session, redirect, abort

from packet import auth, app, db, ldap
from packet.mail import send_start_packet_mail
from packet.models import Freshman, FreshSignature, Packet, UpperSignature, MiscSignature
from packet.notifications import packets_starting_notification, packet_starting_notification

INTRO_REALM = 'https://sso.csh.rit.edu/auth/realms/intro'

WrappedFunc = TypeVar('WrappedFunc', bound=Callable)

def before_request(func: WrappedFunc) -> WrappedFunc:
    """
    Credit to Liam Middlebrook and Ram Zallan
    https://github.com/liam-middlebrook/gallery
    """

    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        uid = str(session['userinfo'].get('preferred_username', ''))
        if session['id_token']['iss'] == INTRO_REALM:
            info = {
                'realm': 'intro',
                'uid': uid,
                'onfloor': is_freshman_on_floor(uid),
                'admin': False,  # It's always false if frosh
                'ritdn': uid,
                'is_upper': False,
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
    """
    freshman = Freshman.query.filter_by(rit_username=rit_username).first()
    if freshman is not None:
        return freshman.onfloor
    else:
        return False


def upper_auth(func: WrappedFunc) -> WrappedFunc:
    """
    Decorator for denying access to intromembers on priviledged routes
    """

    @auth.oidc_auth('app')
    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        if app.config['REALM'] == 'csh':
            username = str(session['userinfo'].get('preferred_username', ''))
            if ldap.is_intromember(ldap.get_member(username)):
                app.logger.warn('Stopped intro member {} from accessing upperclassmen packet'.format(username))
                # TODO we should display a notice to the user that we reidrected them
                return redirect(app.config['PROTOCOL'] + app.config['PACKET_UPPER'], code=301)
        else:
            # If we're not in the csh realm, priviledged routes shouldn't be served
            abort(404)

        return func(*args, **kwargs)

    return cast(WrappedFunc, wrapped_function)


def admin_auth(func: WrappedFunc) -> WrappedFunc:
    """
    Decorator for easily configuring oidc
    """

    @auth.oidc_auth('app')
    @wraps(func)
    def wrapped_function(*args: list, **kwargs: dict) -> Any:
        if app.config['REALM'] == 'csh':
            username = str(session['userinfo'].get('preferred_username', ''))
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
    """
    if app.config['SLACK_WEBHOOK_URL'] is None:
        app.logger.warn('SLACK_WEBHOOK_URL not configured, not sending message to slack.')
        return

    msg = f':pizza-party: {name} got :100: on packet! :pizza-party:'
    requests.put(app.config['SLACK_WEBHOOK_URL'], json={'text': msg})
    app.logger.info('Posted 100% notification to slack for ' + name)


def sync_freshman(freshmen_list: dict) -> None:
    freshmen_in_db = {freshman.rit_username: freshman for freshman in Freshman.query.all()}

    for list_freshman in freshmen_list.values():
        if list_freshman.rit_username not in freshmen_in_db:
            # This is a new freshman so add them to the DB
            freshmen_in_db[list_freshman.rit_username] = Freshman(rit_username=list_freshman.rit_username,
                                                                  name=list_freshman.name,
                                                                  onfloor=list_freshman.onfloor)
            db.session.add(freshmen_in_db[list_freshman.rit_username])
        else:
            # This freshman is already in the DB so just update them
            freshmen_in_db[list_freshman.rit_username].onfloor = list_freshman.onfloor
            freshmen_in_db[list_freshman.rit_username].name = list_freshman.name

    # Update all freshmen entries that represent people who are no longer freshmen
    for freshman in filter(lambda freshman: freshman.rit_username not in freshmen_list, freshmen_in_db.values()):
        freshman.onfloor = False

    # Update the freshmen signatures of each open or future packet
    for packet in Packet.query.filter(Packet.end > datetime.now()).all():
        # Handle the freshmen that are no longer onfloor
        for fresh_sig in filter(lambda fresh_sig: not fresh_sig.freshman.onfloor, packet.fresh_signatures):
            FreshSignature.query.filter_by(packet_id=fresh_sig.packet_id,
                                           freshman_username=fresh_sig.freshman_username).delete()

        # Add any new onfloor freshmen
        # pylint: disable=cell-var-from-loop
        current_fresh_sigs = set(map(lambda fresh_sig: fresh_sig.freshman_username, packet.fresh_signatures))
        for list_freshman in filter(lambda list_freshman: list_freshman.rit_username not in current_fresh_sigs and
                                                          list_freshman.onfloor and
                                                          list_freshman.rit_username != packet.freshman_username,
                                    freshmen_list.values()):
            db.session.add(FreshSignature(packet=packet, freshman=freshmen_in_db[list_freshman.rit_username]))

    db.session.commit()


def create_new_packets(base_date: date, freshmen_list: dict) -> None:
    packet_start_time = time(hour=19)
    packet_end_time = time(hour=21)
    start = datetime.combine(base_date, packet_start_time)
    end = datetime.combine(base_date, packet_end_time) + timedelta(days=14)

    print('Fetching data from LDAP...')
    all_upper = list(filter(
        lambda member: not ldap.is_intromember(member) and not ldap.is_on_coop(member), ldap.get_active_members()))


    rtp = ldap.get_active_rtps()
    three_da = ldap.get_3das()
    webmaster = ldap.get_webmasters()
    c_m = ldap.get_constitutional_maintainers()
    w_m = ldap.get_wiki_maintainers()
    drink = ldap.get_drink_admins()

    # Packet starting notifications
    packets_starting_notification(start)

    # Create the new packets and the signatures for each freshman in the given CSV
    print('Creating DB entries and sending emails...')
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

        for onfloor_freshman in Freshman.query.filter_by(onfloor=True).filter(Freshman.rit_username !=
                                                                              freshman.rit_username).all():
            db.session.add(FreshSignature(packet=packet, freshman=onfloor_freshman))

    db.session.commit()


def sync_with_ldap() -> None:
    print('Fetching data from LDAP...')
    all_upper = {member.uid: member for member in filter(
        lambda member: not ldap.is_intromember(member) and not ldap.is_on_coop(member), ldap.get_active_members())}

    rtp = ldap.get_active_rtps()
    three_da = ldap.get_3das()
    webmaster = ldap.get_webmasters()
    c_m = ldap.get_constitutional_maintainers()
    w_m = ldap.get_wiki_maintainers()
    drink = ldap.get_drink_admins()

    print('Applying updates to the DB...')
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
        # pylint: disable=cell-var-from-loop
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
    """
    if app.config['REALM'] == 'csh':
        username = str(session['userinfo'].get('preferred_username', ''))
        return ldap.is_intromember(ldap.get_member(username))
    # Always true for the intro realm
    return True
