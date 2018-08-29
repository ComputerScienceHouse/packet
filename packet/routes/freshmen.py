from flask import render_template, redirect

from packet import auth, app
from packet.ldap import ldap_get_live_onfloor, ldap_get_eboard
from packet.utils import before_request


@app.route("/")
@before_request
def index(info=None):
    return redirect("/packet/" + info['uid'], 302)


@app.route("/packet/<uid>")
@auth.oidc_auth
@before_request
def freshman_packet(uid, info=None):
    onfloor = ldap_get_live_onfloor()
    eboard = ldap_get_eboard()
    return render_template("packet.html", info=info, eboard=eboard, onfloor=onfloor, uid=uid)


@app.route("/packets")
@auth.oidc_auth
@before_request
def packets(info=None):
    freshmen = [
        {
            "name": "Testiboi",
            "signatures": 12,
            "uid": 111
        },
        {
            "name": "Ram Zallllllan",
            "signatures": 69,
            "uid": 420
        }
    ]
    return render_template("active_packets.html", info=info, freshmen=freshmen)
