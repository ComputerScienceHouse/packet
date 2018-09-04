from datetime import datetime
from itertools import chain

from flask import redirect, render_template
from sqlalchemy import func, case

from packet import auth, app, db
from packet.models import Packet, UpperSignature, MiscSignature
from packet.utils import before_request


@app.route("/")
@auth.oidc_auth
def index():
    return redirect("/packets", 302)


@app.route("/member/<uid>")
@auth.oidc_auth
@before_request
def upperclassman(uid, info=None):
    open_packets = Packet.query.filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).all()
    signatures = 0

    for packet in open_packets:
        packet.did_sign = False

        for sig in chain(filter(lambda sig: sig.signed, packet.upper_signatures), packet.misc_signatures):
            if sig.member == uid:
                packet.did_sign = True
                signatures += 1
                break

    open_packets.sort(key=lambda x: x.did_sign, reverse=True)

    return render_template("upperclassman.html", info=info, open_packets=open_packets, member=uid,
                           signatures=signatures)


@app.route("/upperclassmen")
@auth.oidc_auth
@before_request
def upperclassmen_total(info=None):
    open_packets = Packet.query.filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).count()

    # TODO: Only count open Packets
    upperclassmen = (db.session.query(func.count(case([(UpperSignature.signed == True, 1)])).label("signatures"),
                                      UpperSignature.member)).group_by(UpperSignature.member).all()
    upperclassmen += (db.session.query(func.count().label("signatures"),
                                       MiscSignature.member)).group_by(MiscSignature.member).all()

    upperclassmen.sort(reverse=True)

    return render_template("upperclassmen_totals.html", info=info, upperclassmen=upperclassmen,
                           open_packets=open_packets)
