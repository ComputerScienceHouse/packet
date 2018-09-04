from collections import namedtuple
from itertools import chain

from flask import render_template, redirect

from packet import auth, app
from packet.models import Freshman, Packet
from packet.packet import get_signatures, get_number_required, get_number_signed, get_upperclassmen_percent
from packet.utils import before_request, signed_packet
from packet.member import signed_packets
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
    open_packets = signed_packets(info["uid"])
    s_packets = []

    SPacket = namedtuple('spacket', ['rit_username', 'name', 'did_sign', 'total_signatures', 'required_signatures'])

    for result in open_packets:
        s_packets.append(SPacket(result[0], result[1], result[2],
                                 sum(get_number_signed(result[0]).values()),
                                 sum(get_number_required(result[0]).values())))

    s_packets.sort(key=lambda x: x.total_signatures, reverse=True)
    s_packets.sort(key=lambda x: x.did_sign, reverse=True)

    return render_template("active_packets.html", info=info, packets=s_packets)
