from flask import render_template

from packet import app
from packet.models import Packet, Freshman
from packet.routes.shared import packet_sort_key
from packet.utils import before_request, admin_auth, is_frosh
from packet.log_utils import log_cache, log_time


@app.route('/admin/packets')
@log_cache
@admin_auth
@before_request
@log_time
def admin_packets(info=None):
    open_packets = Packet.open_packets()

    # Pre-calculate and store the return values of did_sign(), signatures_received(), and signatures_required()
    for packet in open_packets:
        packet.did_sign_result = packet.did_sign(info['uid'], app.config['REALM'] == 'csh', is_frosh())
        packet.signatures_received_result = packet.signatures_received()
        packet.signatures_required_result = packet.signatures_required()

    open_packets.sort(key=packet_sort_key, reverse=True)

    return render_template('admin_packets.html',
                           open_packets=open_packets,
                           info=info)


@app.route('/admin/freshmen')
@log_cache
@admin_auth
@before_request
@log_time
def admin_freshmen(info=None):
    all_freshmen = Freshman.get_all()

    return render_template('admin_freshmen.html',
                           all_freshmen=all_freshmen,
                           info=info)
