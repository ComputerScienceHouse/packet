from flask import redirect, render_template, request

from packet import auth, app
from packet.packet import set_essays, get_current_packet
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
    packet = get_current_packet(info['uid'])
    return render_template("essays.html", info=info, packet=packet)


@app.route("/essay", methods=["POST"])
@auth.oidc_auth
@before_request
def submit_essay(info=None):
    formdata = request.form
    if set_essays(info['uid'], formdata['info_eboard'], formdata['info_events'], formdata['info_achieve']):
        return redirect("/essays", 302)
    return redirect("/essays", 500)
