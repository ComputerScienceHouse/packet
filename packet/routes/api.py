"""
Shared API endpoints
"""
from datetime import datetime
from json import dumps

from flask import session, request

from packet import app, db, ldap
from packet.context_processors import get_rit_name
from packet.log_utils import log_time
from packet.mail import send_report_mail
from packet.utils import before_request, upper_auth, notify_slack, sync_freshman as sync_freshman_list, \
    create_new_packets, sync_with_ldap
from packet.models import Packet, MiscSignature, NotificationSubscription, Freshman
from packet.notifications import packet_signed_notification, packet_100_percent_notification
import packet.stats as stats


class POSTFreshman:
    def __init__(self, freshman):
        self.name = freshman['name'].strip()
        self.rit_username = freshman['rit_username'].strip()
        self.onfloor = freshman['onfloor'].strip() == 'TRUE'


@app.route('/api/v1/freshmen', methods=['POST'])
def sync_freshman():
    """
    Create or update freshmen entries from a list

    Body parameters: [
        {
         rit_username: string
         name: string
         onfloor: boolean
        }
    ]
    """

    # Only allow evals to create new frosh
    username = str(session['userinfo'].get('preferred_username', ''))
    if not ldap.is_evals(ldap.get_member(username)):
        return 'Forbidden: not Evaluations Director', 403

    freshmen_in_post = {freshman.rit_username: freshman for freshman in map(POSTFreshman, request.json)}
    sync_freshman_list(freshmen_in_post)
    return dumps('Done'), 200


@app.route('/api/v1/packets', methods=['POST'])
@log_time
def create_packet():
    """
    Create a new packet.

    Body parameters: {
      start_date: the start date of the packets in MM/DD/YYYY format
      freshmen: [
        {
          rit_username: string
          name: string
          onfloor: boolean
        }
      ]
    }
    """

    # Only allow evals to create new packets
    username = str(session['userinfo'].get('preferred_username', ''))
    if not ldap.is_evals(ldap.get_member(username)):
        return 'Forbidden: not Evaluations Director', 403

    base_date = datetime.strptime(request.json['start_date'], '%m/%d/%Y').date()

    freshmen_in_post = {freshman.rit_username: freshman for freshman in map(POSTFreshman, request.json['freshmen'])}

    create_new_packets(base_date, freshmen_in_post)

    return dumps('Done'), 201


@app.route('/api/v1/sync', methods=['POST'])
@log_time
def sync_ldap():
    # Only allow evals to sync ldap
    username = str(session['userinfo'].get('preferred_username', ''))
    if not ldap.is_evals(ldap.get_member(username)):
        return 'Forbidden: not Evaluations Director', 403
    sync_with_ldap()
    return dumps('Done'), 201


@app.route('/api/v1/packets/<username>', methods=['GET'])
def get_packets_by_user(username: str) -> dict:
    """
    Return a dictionary of packets for a freshman by username, giving packet start and end date by packet id
    """
    frosh = Freshman.by_username(username)

    return {packet.id: {
        'start': packet.start,
        'end': packet.end,
    } for packet in frosh.packets}


@app.route('/api/v1/packets/<username>/newest', methods=['GET'])
def get_newest_packet_by_user(username: str) -> dict:
    """
    Return a user's newest packet
    """
    frosh = Freshman.by_username(username)

    packet = frosh.packets[-1]

    return {
        packet.id: {
            'start': packet.start,
            'end': packet.end,
            'required': vars(packet.signatures_required()),
            'received': vars(packet.signatures_received()),
        }
    }


@app.route('/api/v1/packet/<packet_id>', methods=['GET'])
def get_packet_by_id(packet_id: int) -> dict:
    """
    Return the scores of the packet in question
    """

    packet = Packet.by_id(packet_id)

    return {
        'required': vars(packet.signatures_required()),
        'received': vars(packet.signatures_received()),
    }


@app.route('/api/v1/sign/<packet_id>/', methods=['POST'])
@before_request
def sign(packet_id, info):
    packet = Packet.by_id(packet_id)

    if packet is not None and packet.is_open():
        was_100 = packet.is_100()
        if app.config['REALM'] == 'csh' and not ldap.is_intromember(ldap.get_member(info['uid'])):
            # Check if the CSHer is an upperclassman and if so, sign that row
            for sig in filter(lambda sig: sig.member == info['uid'], packet.upper_signatures):
                sig.signed = True
                app.logger.info('Member {} signed packet {} as an upperclassman'.format(info['uid'], packet_id))
                return commit_sig(packet, was_100, info['uid'])

            # The CSHer is a misc so add a new row
            db.session.add(MiscSignature(packet=packet, member=info['uid']))
            app.logger.info('Member {} signed packet {} as a misc'.format(info['uid'], packet_id))
            return commit_sig(packet, was_100, info['uid'])
        else:
            # Check if the freshman is onfloor and if so, sign that row
            for sig in filter(lambda sig: sig.freshman_username == info['ritdn'], packet.fresh_signatures):
                sig.signed = True
                app.logger.info('Freshman {} signed packet {}'.format(info['ritdn'], packet_id))
                return commit_sig(packet, was_100, info['ritdn'])

    app.logger.warn("Failed to add {}'s signature to packet {}".format(info['uid'], packet_id))
    return 'Error: Signature not valid.  Reason: Unknown'


@app.route('/api/v1/subscribe/', methods=['POST'])
@before_request
def subscribe(info):
    data = request.form
    if app.config['REALM'] == 'csh':
        subscription = NotificationSubscription(token=data['token'], member=info['uid'])
    else:
        subscription = NotificationSubscription(token=data['token'], freshman_username=info['uid'])
    db.session.add(subscription)
    db.session.commit()
    return 'Token subscribed for ' + info['uid']


@app.route('/api/v1/report/', methods=['POST'])
@before_request
def report(info):
    form_results = request.form
    send_report_mail(form_results, get_rit_name(info['ritdn']))
    return 'Success: ' + get_rit_name(info['ritdn']) + ' sent a report'


@app.route('/api/v1/stats/packet/<packet_id>')
@upper_auth
def packet_stats(packet_id):
    return stats.packet_stats(packet_id)


@app.route('/api/v1/stats/upperclassman/<uid>')
@upper_auth
def upperclassman_stats(uid):
    return stats.upperclassman_stats(uid)


@app.route('/readiness')
def readiness() -> tuple[str, int]:
    """A basic healthcheck. Returns 200 to indicate flask is running"""
    return 'ready', 200


def commit_sig(packet, was_100, uid):
    packet_signed_notification(packet, uid)
    db.session.commit()
    if not was_100 and packet.is_100():
        packet_100_percent_notification(packet)
        notify_slack(packet.freshman.name)

    return 'Success: Signed Packet: ' + packet.freshman_username
