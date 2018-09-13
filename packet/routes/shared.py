from itertools import chain
from datetime import datetime
from flask import render_template, redirect

from packet import auth, app
from packet.utils import before_request
from packet.models import MiscSignature, Packet
from packet.debug_utils import log_time, log_cache


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
        can_sign = False
        did_sign = False

        if app.config["REALM"] == "csh":
            can_sign = packet.is_open()

            for sig in filter(lambda sig: sig.member == info["uid"], chain(packet.upper_signatures,
                                                                           packet.misc_signatures)):
                if isinstance(sig, MiscSignature):
                    did_sign = True
                else:
                    did_sign = sig.signed

                break
        else:
            for sig in filter(lambda sig: sig.freshman_username == info["uid"], packet.fresh_signatures):
                can_sign = packet.is_open()
                did_sign = sig.signed
                break

        return render_template("packet.html", info=info, packet=packet, can_sign=can_sign, did_sign=did_sign,
                               required=packet.signatures_required(), received=packet.signatures_received(),
                               eboard=filter(lambda sig: sig.eboard, packet.upper_signatures),
                               upper=filter(lambda sig: not sig.eboard, packet.upper_signatures))


@app.route("/packets/")
@auth.oidc_auth
@before_request
@log_time
def packets(info=None):
    @log_time
    def query():
        return Packet.query.filter(Packet.start < datetime.now(), Packet.end > datetime.now()).all()

    open_packets = query()

    # Pre-calculate and store the return values of did_sign(), signatures_received(), and signatures_required()
    @log_time
    def prec_1():
        for packet in open_packets:
            packet.did_sign_result = packet.did_sign(info["uid"], app.config["REALM"] == "csh")

    @log_time
    def prec_2():
        for packet in open_packets:
            packet.signatures_received_result = packet.signatures_received()

    @log_time
    def prec_3():
        for packet in open_packets:
            packet.signatures_required_result = packet.signatures_required()

    @log_time
    def sort():
        open_packets.sort(key=lambda packet: packet.signatures_received_result.total, reverse=True)
        open_packets.sort(key=lambda packet: packet.did_sign_result, reverse=True)

    @log_time
    def render():
        return render_template("active_packets.html", info=info, packets=open_packets)

    prec_1()
    prec_2()
    prec_3()
    sort()
    out = render()
    log_cache()
    return out
