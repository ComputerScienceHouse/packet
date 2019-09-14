"""
Shared API endpoints
"""
from datetime import datetime, timedelta
from json import dumps

from flask import session, request

from packet import app, db
from packet.context_processors import get_rit_name
from packet.commands import packet_start_time, packet_end_time
from packet.ldap import ldap_get_eboard_role, ldap_get_active_rtps, ldap_get_3das, ldap_get_webmasters, \
    ldap_get_drink_admins, ldap_get_constitutional_maintainers, ldap_is_intromember, ldap_get_active_members, \
    ldap_is_on_coop, _ldap_is_member_of_group, ldap_get_member
from packet.mail import send_report_mail, send_start_packet_mail
from packet.utils import before_request, packet_auth, notify_slack
from packet.models import Packet, MiscSignature, NotificationSubscription, Freshman, FreshSignature, UpperSignature
from packet.notifications import packet_signed_notification, packet_100_percent_notification, \
        packet_starting_notification, packets_starting_notification


@app.route('/api/v1/freshmen', methods=['POST'])
@packet_auth
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
    if not _ldap_is_member_of_group(ldap_get_member(username), 'eboard-evaluations'):
        return 'Forbidden: not Evaluations Director', 403

    freshmen = request.json
    results = list()

    packets = Packet.query.filter(Packet.end > datetime.now()).all()

    for freshman in freshmen:
        rit_username = freshman['rit_username']
        name = freshman['name']
        onfloor = freshman['onfloor']

        frosh = Freshman.query.filter_by(rit_username=rit_username).first()
        if frosh:
            if onfloor and not frosh.onfloor:
                # Add new onfloor signature
                for packet in packets:
                    db.session.add(FreshSignature(packet=packet, freshman=frosh))
            elif not onfloor and frosh.onfloor:
                # Remove outdated onfloor signature
                for packet in packets:
                    FreshSignature.query.filter_by(packet_id=packet.id, freshman_username=frosh.rit_username).delete()

            frosh.name = name
            frosh.onfloor = onfloor

            results.append(f"'{name} ({rit_username})' updated")
        else:
            frosh = Freshman(rit_username=rit_username, name=name, onfloor=onfloor)
            db.session.add(frosh)
            if onfloor:
                # Add onfloor signature
                for packet in packets:
                    db.session.add(FreshSignature(packet=packet, freshman=frosh))

            results.append(f"Freshman '{name} ({rit_username})' created")

    db.session.commit()
    return dumps(results), 200


@app.route('/api/v1/packets', methods=['POST'])
@packet_auth
def create_packet():
    """
    Create a new packet.

    Body parameters: {
      start_date: the start date of the packets in MM/DD/YYYY format
      freshmen: [
        rit_username: string
      ]
    }
    """

    # Only allow evals to create new packets
    username = str(session['userinfo'].get('preferred_username', ''))
    if not _ldap_is_member_of_group(ldap_get_member(username), 'eboard-evaluations'):
        return 'Forbidden: not Evaluations Director', 403

    base_date = datetime.strptime(request.json['start_date'], '%m/%d/%Y').date()

    start = datetime.combine(base_date, packet_start_time)
    end = datetime.combine(base_date, packet_end_time) + timedelta(days=14)

    frosh = request.json['freshmen']
    results = list()

    # Gather upperclassmen data from LDAP
    all_upper = list(filter(
        lambda member: not ldap_is_intromember(member) and not ldap_is_on_coop(member), ldap_get_active_members()))

    rtp = ldap_get_active_rtps()
    three_da = ldap_get_3das()
    webmaster = ldap_get_webmasters()
    c_m = ldap_get_constitutional_maintainers()
    drink = ldap_get_drink_admins()

    # Packet starting notifications
    packets_starting_notification(start)

    for frosh_rit_username in frosh:
        # Create the packet and signatures
        freshman = Freshman.query.filter_by(rit_username=frosh_rit_username).first()
        if freshman is None:
            results.append(f"Freshman '{frosh_rit_username}' not found")
            continue

        packet = Packet(freshman=freshman, start=start, end=end)
        db.session.add(packet)
        send_start_packet_mail(packet)
        packet_starting_notification(packet)

        for member in all_upper:
            sig = UpperSignature(packet=packet, member=member.uid)
            sig.eboard = ldap_get_eboard_role(member)
            sig.active_rtp = member.uid in rtp
            sig.three_da = member.uid in three_da
            sig.webmaster = member.uid in webmaster
            sig.c_m = member.uid in c_m
            sig.drink_admin = member.uid in drink
            db.session.add(sig)

        for onfloor_freshman in Freshman.query.filter_by(onfloor=True).filter(Freshman.rit_username !=
                                                                              freshman.rit_username).all():
            db.session.add(FreshSignature(packet=packet, freshman=onfloor_freshman))

        results.append(f'Packet created for {frosh_rit_username}')

    db.session.commit()

    return dumps(results), 201


@app.route('/api/v1/packets/<username>', methods=['GET'])
@packet_auth
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
@packet_auth
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
@packet_auth
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
@packet_auth
@before_request
def sign(packet_id, info):
    packet = Packet.by_id(packet_id)

    if packet is not None and packet.is_open():
        was_100 = packet.is_100()
        if app.config['REALM'] == 'csh':
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
            for sig in filter(lambda sig: sig.freshman_username == info['uid'], packet.fresh_signatures):
                sig.signed = True
                app.logger.info('Freshman {} signed packet {}'.format(info['uid'], packet_id))
                return commit_sig(packet, was_100, info['uid'])

    app.logger.warn("Failed to add {}'s signature to packet {}".format(info['uid'], packet_id))
    return 'Error: Signature not valid.  Reason: Unknown'


@app.route('/api/v1/subscribe/', methods=['POST'])
@packet_auth
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
@packet_auth
@before_request
def report(info):
    form_results = request.form
    send_report_mail(form_results, get_rit_name(info['uid']))
    return 'Success: ' + get_rit_name(info['uid']) + ' sent a report'


@app.route("/api/v1/stats/packet/<packet_id>")
@packet_auth
def packet_stats(packet_id):
    packet = Packet.by_id(packet_id)

    dates = [packet.start.date() + timedelta(days=x) for x in range(0, (packet.end-packet.start).days)]

    upper_stats = dict()
    for date in map(lambda sig: sig.updated, filter(lambda sig: sig.signed, packet.upper_signatures)):
        upper_stats[date.date()] = upper_stats.get(date.date(), 0) + 1

    fresh_stats = dict()
    for date in map(lambda sig: sig.updated, filter(lambda sig: sig.signed, packet.fresh_signatures)):
        fresh_stats[date.date()] = fresh_stats.get(date.date(), 0) + 1

    misc_stats = dict()
    for date in map(lambda sig: sig.updated, packet.misc_signatures):
        misc_stats[date.date()] = misc_stats.get(date.date(), 0) + 1

    total_stats = dict()
    for date in dates:
        total_stats[date.isoformat()] = {
                'upper': upper_stats.get(date, 0),
                'fresh': fresh_stats.get(date, 0),
                'misc': misc_stats.get(date, 0),
                }

    return {
            'packet_id': packet_id,
            'dates': total_stats,
            }


def commit_sig(packet, was_100, uid):
    packet_signed_notification(packet, uid)
    db.session.commit()
    if not was_100 and packet.is_100():
        packet_100_percent_notification(packet)
        notify_slack(packet.freshman.name)

    return 'Success: Signed Packet: ' + packet.freshman_username
