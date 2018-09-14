"""
Routes available to freshmen only
"""

from flask import redirect, render_template, request, url_for

from packet import auth, app, db
from packet.models import Packet
from packet.utils import before_request


@app.route("/")
@auth.oidc_auth
@before_request
def index(info=None):
    most_recent_packet = Packet.query.filter_by(freshman_username=info['uid']).order_by(Packet.id.desc()).first()

    if most_recent_packet is not None:
        return redirect(url_for("freshman_packet", packet_id=most_recent_packet.id), 302)
    else:
        return redirect(url_for("packets"), 302)


@app.route("/essays/<packet_id>/")
@auth.oidc_auth
@before_request
def essays(packet_id, info=None):
    packet = Packet.by_id(packet_id)

    if packet is not None and packet.freshman_username == info["uid"]:
        return render_template("essays.html", info=info, packet=packet)
    else:
        return redirect(url_for("index"), 302)


@app.route("/essays/<packet_id>/", methods=["POST"])
@auth.oidc_auth
@before_request
def submit_essays(packet_id, info=None):
    packet = Packet.by_id(packet_id)

    if packet is not None and packet.is_open() and packet.freshman_username == info["uid"]:
        packet.info_eboard = request.form.get("info_eboard", None)
        packet.info_events = request.form.get("info_events", None)
        packet.info_achieve = request.form.get("info_achieve", None)

        db.session.commit()
        return redirect(url_for("essays", packet_id=packet_id), 302)
    else:
        return redirect(url_for("index"), 302)
