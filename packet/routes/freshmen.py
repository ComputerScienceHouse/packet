from flask import redirect, render_template, request

from packet import auth, app, db
from packet.models import Packet
from packet.utils import before_request


@app.route("/")
@auth.oidc_auth
@before_request
def index(info=None):
    return redirect("/packet/" + info['uid'], 302)


@app.route("/essays")
@auth.oidc_auth
@before_request
def essays(info=None):
    packet = Packet.query.filter_by(freshman_username=info['uid']).first()
    return render_template("essays.html", info=info, packet=packet)


@app.route("/essay", methods=["POST"])
@auth.oidc_auth
@before_request
def submit_essay(info=None):
    formdata = request.form
    packet = Packet.query.filter_by(freshman_username=info['uid']).first()

    packet.info_eboard = formdata['info_eboard']
    packet.info_events = formdata['info_events']
    packet.info_achieve = formdata['info_achieve']
    db.session.commit()

    return redirect("/essays", 302)
