"""
Routes available to CSH users only
"""

from itertools import chain
from operator import itemgetter
from flask import redirect, render_template, url_for

from packet import app
from packet.models import Packet, MiscSignature
from packet.utils import before_request, packet_auth
from packet.log_utils import log_cache, log_time


@app.route("/")
@packet_auth
def index():
    return redirect(url_for("packets"), 302)


@app.route("/member/<uid>/")
@log_cache
@packet_auth
@before_request
@log_time
def upperclassman(uid, info=None):
    open_packets = Packet.open_packets()

    # Pre-calculate and store the return value of did_sign()
    for packet in open_packets:
        packet.did_sign_result = packet.did_sign(uid, True)

    signatures = sum(map(lambda packet: 1 if packet.did_sign_result else 0, open_packets))

    open_packets.sort(key=lambda packet: packet.freshman_username)
    open_packets.sort(key=lambda packet: packet.did_sign_result, reverse=True)

    return render_template("upperclassman.html", info=info, open_packets=open_packets, member=uid,
                           signatures=signatures)


@app.route("/upperclassmen/")
@log_cache
@packet_auth
@before_request
@log_time
def upperclassmen_total(info=None):
    open_packets = Packet.open_packets()

    # Sum up the signed packets per upperclassman
    upperclassmen = dict()
    for packet in open_packets:
        for sig in chain(packet.upper_signatures, packet.misc_signatures):
            if sig.member not in upperclassmen:
                upperclassmen[sig.member] = 0

            if isinstance(sig, MiscSignature):
                upperclassmen[sig.member] += 1
            elif sig.signed:
                upperclassmen[sig.member] += 1

    return render_template("upperclassmen_totals.html", info=info, num_open_packets=len(open_packets),
                           upperclassmen=sorted(upperclassmen.items(), key=itemgetter(1), reverse=True))
