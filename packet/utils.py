"""
General utilities and decorators for supporting the Python logic
"""
from datetime import datetime
from functools import wraps, lru_cache

import requests
from flask import session, redirect

from packet import auth, app, db
from packet.models import Freshman, FreshSignature, Packet
from packet.ldap import ldap_get_member, ldap_is_intromember, ldap_is_evals, ldap_is_rtp

INTRO_REALM = 'https://sso.csh.rit.edu/auth/realms/intro'

def before_request(func):
    """
    Credit to Liam Middlebrook and Ram Zallan
    https://github.com/liam-middlebrook/gallery
    """
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        uid = str(session['userinfo'].get('preferred_username', ''))
        member = ldap_get_member(uid)

        if session['id_token']['iss'] == INTRO_REALM:
            info = {
                'realm': 'intro',
                'uid': uid,
                'onfloor': is_freshman_on_floor(uid)
            }
        else:
            info = {
                'realm': 'csh',
                'uid': uid,
                'admin': ldap_is_evals(member) or ldap_is_rtp(member)
            }

        kwargs['info'] = info
        return func(*args, **kwargs)

    return wrapped_function


@lru_cache(maxsize=128)
def is_freshman_on_floor(rit_username):
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
    @auth.oidc_auth('app')
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        if app.config['REALM'] == 'csh':
            username = str(session['userinfo'].get('preferred_username', ''))
            if ldap_is_intromember(ldap_get_member(username)):
                app.logger.warn('Stopped intro member {} from accessing upperclassmen packet'.format(username))
                return redirect(app.config['PROTOCOL'] + app.config['PACKET_INTRO'], code=301)

        return func(*args, **kwargs)

    return wrapped_function


def admin_auth(func):
    """
    Decorator for easily configuring oidc
    """
    @auth.oidc_auth('app')
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        if app.config['REALM'] == 'csh':
            username = str(session['userinfo'].get('preferred_username', ''))
            member = ldap_get_member(username)
            if not ldap_is_evals(member) and not ldap_is_rtp(member):
                app.logger.warn('Stopped member {} from accessing admin UI'.format(username))
                return redirect(app.config['PROTOCOL'] + app.config['PACKET_UPPER'], code=301)

        return func(*args, **kwargs)

    return wrapped_function


def notify_slack(name: str):
    """
    Sends a congratulate on sight decree to Slack
    """
    if app.config['SLACK_WEBHOOK_URL'] is None:
        app.logger.warn('SLACK_WEBHOOK_URL not configured, not sending message to slack.')
        return

    msg = f':pizza-party: {name} got :100: on packet! :pizza-party:'
    requests.put(app.config['SLACK_WEBHOOK_URL'], json={'text':msg})
    app.logger.info('Posted 100% notification to slack for ' + name)


def sync_freshman(freshmen_list):
    freshmen_in_db = {freshman.rit_username: freshman for freshman in Freshman.query.all()}

    for list_freshman in freshmen_list.values():
        if list_freshman.rit_username not in freshmen_in_db:
            # This is a new freshman so add them to the DB
            freshmen_in_db[list_freshman.rit_username] = Freshman(rit_username=list_freshman.rit_username,
                                                                 name=list_freshman.name, onfloor=list_freshman.onfloor)
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
