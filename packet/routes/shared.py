"""
Routes available to both freshmen and CSH users
"""

from flask import render_template, redirect

from packet import auth, app
from packet.utils import before_request, packet_auth
from packet.models import Packet
from packet.log_utils import log_cache, log_time


@app.route('/logout/')
@auth.oidc_logout
def logout():
    return redirect('https://csh.rit.edu')


@app.route('/packet/<packet_id>/')
@log_cache
@packet_auth
@before_request
@log_time
def freshman_packet(packet_id, info=None):
    packet = Packet.by_id(packet_id)

    if packet is None:
        return 'Invalid packet or freshman', 404
    else:
        can_sign = packet.is_open()

        # If the packet is open and the user is an off-floor freshman set can_sign to False
        if packet.is_open() and app.config['REALM'] != 'csh':
            if info['uid'] not in map(lambda sig: sig.freshman_username, packet.fresh_signatures):
                can_sign = False

        # The current user's freshman signature on this packet
        fresh_sig = list(filter(
            lambda sig: sig.freshman_username == info['ritdn'] if info else '',
            packet.fresh_signatures
        ))

        return render_template('packet.html',
                               info=info,
                               packet=packet,
                               can_sign=can_sign,
                               did_sign=packet.did_sign(info['uid'], app.config['REALM'] == 'csh'),
                               required=packet.signatures_required(),
                               received=packet.signatures_received(),
                               upper=packet.upper_signatures,
                               fresh_sig=fresh_sig)


def packet_sort_key(packet):
    """
    Utility function for generating keys for sorting packets
    """
    return packet.freshman.name, -packet.signatures_received_result.total, not packet.did_sign_result


@app.route('/packets/')
@log_cache
@packet_auth
@before_request
@log_time
def packets(info=None):
    open_packets = Packet.open_packets()

    # Pre-calculate and store the return values of did_sign(), signatures_received(), and signatures_required()
    for packet in open_packets:
        packet.did_sign_result = packet.did_sign(info['uid'], app.config['REALM'] == 'csh')
        packet.signatures_received_result = packet.signatures_received()
        packet.signatures_required_result = packet.signatures_required()

    open_packets.sort(key=packet_sort_key)

    return render_template('active_packets.html', info=info, packets=open_packets)


@app.route('/sw.js', methods=['GET'])
@app.route('/OneSignalSDKWorker.js', methods=['GET'])
def service_worker():
    return app.send_static_file('js/sw.js')


@app.route('/update-sw.js', methods=['GET'])
@app.route('/OneSignalSDKUpdaterWorker.js', methods=['GET'])
def update_service_worker():
    return app.send_static_file('js/update-sw.js')


@app.errorhandler(404)
@packet_auth
@before_request
def not_found(e, info=None):
    return render_template('not_found.html', e=e, info=info), 404


@app.errorhandler(500)
@packet_auth
@before_request
def error(e, info=None):
    return render_template('error.html', e=e, info=info), 500
