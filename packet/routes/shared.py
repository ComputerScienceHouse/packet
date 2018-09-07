from datetime import datetime
from itertools import chain

from flask import render_template, redirect

from packet import auth, app
from packet.models import Freshman, Packet
from packet.packet import get_signatures, get_number_required, get_number_signed, get_upperclassmen_percent
from packet.utils import before_request, signed_packet


@app.route('/logout')
@auth.oidc_logout
def logout():
    return redirect("/")


@app.route("/packet/<uid>")
@auth.oidc_auth
@before_request
def freshman_packet(uid, info=None):
    freshman = Freshman.query.filter_by(rit_username=uid).first()
    upperclassmen_percent = get_upperclassmen_percent(uid)
    signatures = get_signatures(uid)
    signed_dict = get_number_signed(uid)
    required = sum(get_number_required(uid).values())
    signed = sum(signed_dict.values())

    packet_signed = signed_packet(info['uid'], uid)
    return render_template("packet.html", info=info, signatures=signatures, uid=uid, required=required, signed=signed,
                           freshman=freshman, packet_signed=packet_signed, upperclassmen_percent=upperclassmen_percent,
                           signed_dict=signed_dict)


@app.route("/packets")
@auth.oidc_auth
@before_request
def packets(info=None):
    open_packets = Packet.query.filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).all()

    # Add the did_sign flag
    if app.config["REALM"] == "csh":
        # User is an upperclassman
        for packet in open_packets:
            packet.did_sign = False
            packet.total_signatures = sum(packet.signatures_received().values())
            packet.required_signatures = sum(packet.signatures_required().values())

            for sig in chain(filter(lambda sig: sig.signed, packet.upper_signatures), packet.misc_signatures):
                if sig.member == info["uid"]:
                    packet.did_sign = True
                    break
    else:
        # User is a freshman
        for packet in open_packets:
            packet.did_sign = False
            packet.total_signatures = sum(packet.signatures_received().values())
            packet.required_signatures = sum(packet.signatures_required().values())

            for sig in filter(lambda sig: sig.signed, packet.fresh_signatures):
                if sig.freshman_username == info["uid"]:
                    packet.did_sign = True
                    break

    open_packets.sort(key=lambda x: sum(x.signatures_received().values()), reverse=True)
    open_packets.sort(key=lambda x: x.did_sign, reverse=True)

    return render_template("active_packets.html", info=info, packets=open_packets)
