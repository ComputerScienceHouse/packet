"""
Routes available to both freshmen and CSH users
"""

from datetime import datetime
from flask import render_template, redirect

from packet import auth, app
from packet.utils import before_request
from packet.models import Packet


@app.route('/logout')
@auth.oidc_logout
def logout():
    return redirect("/")


@app.route("/packet/<freshman_username>/<packet_id>/")
@auth.oidc_auth
@before_request
def freshman_packet(freshman_username, packet_id, info=None):
    packet = Packet.query.filter_by(freshman_username=freshman_username, id=packet_id).first()

    if packet is None:
        return "Invalid packet or freshman", 404
    else:
        can_sign = packet.is_open()

        # If the packet is open and the user is an off-floor freshman set can_sign to False
        if packet.is_open() and app.config["REALM"] != "csh":
            if info["uid"] not in map(lambda sig: sig.freshman_username, packet.fresh_signatures):
                can_sign = False

        return render_template("packet.html",
                               info=info,
                               packet=packet,
                               can_sign=can_sign,
                               did_sign=packet.did_sign(info["uid"], app.config["REALM"] == "csh"),
                               required=packet.signatures_required(),
                               received=packet.signatures_received(),
                               eboard=filter(lambda sig: sig.eboard, packet.upper_signatures),
                               upper=filter(lambda sig: not sig.eboard, packet.upper_signatures))


@app.route("/packets/")
@auth.oidc_auth
@before_request
def packets(info=None):
    open_packets = Packet.query.filter(Packet.start < datetime.now(), Packet.end > datetime.now()).all()

    # Pre-calculate and store the return values of did_sign(), signatures_received(), and signatures_required()
    for packet in open_packets:
        packet.did_sign_result = packet.did_sign(info["uid"], app.config["REALM"] == "csh")
        packet.signatures_received_result = packet.signatures_received()
        packet.signatures_required_result = packet.signatures_required()

    open_packets.sort(key=lambda packet: packet.signatures_received_result.total, reverse=True)
    open_packets.sort(key=lambda packet: packet.did_sign_result, reverse=True)

    return render_template("active_packets.html", info=info, packets=open_packets)
