from datetime import datetime
from itertools import chain

from flask import redirect, render_template

from packet import auth, app
from packet.models import Packet
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

    for packet in open_packets:
        packet.did_sign = False

        for sig in chain(filter(lambda sig: sig.signed, packet.upper_signatures), packet.misc_signatures):
            if sig.member == uid:
                packet.did_sign = True
                break

    open_packets.sort(key=lambda x: x.did_sign, reverse=True)

    return render_template("upperclassman.html", info=info, open_packets=open_packets, member=uid)
