from collections import namedtuple
from itertools import chain

from flask import render_template, redirect

from packet import auth, app
from packet.models import Freshman, Packet
from packet.packet import get_signatures, get_number_required, get_number_signed, get_upperclassmen_percent
from packet.utils import before_request, signed_packet
from packet.member import current_packets
from packet.packet import get_number_required, get_number_signed

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
    if app.config["REALM"] == "csh":
        open_packets = current_packets(info["uid"], False, info["member_info"]["onfloor"])
    else:
        open_packets = current_packets(info["uid"], True, info["onfloor"])

    open_packets.sort(key=lambda x: x.total_signatures, reverse=True)
    open_packets.sort(key=lambda x: x.did_sign, reverse=True)

    return render_template("active_packets.html", info=info, packets=open_packets)
