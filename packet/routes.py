"""
Routes live here for now. As the application is built out they'll be refactored and split into blueprints.
"""

import json
from flask import session, jsonify, render_template

from packet.utils import before_request
from . import auth, app
from .models import Freshman
from .ldap import ldap_get_eboard


@app.route("/")
@auth.oidc_auth
@before_request
def index(info=None):
    freshmen = [
        {
            "name": "Testiboi",
            "signatures": 12,
            "uid": 111
        }
    ]
    return render_template("active_packets.html", info=info, freshmen=freshmen)


@app.route("/packet/<uid>")
@auth.oidc_auth
@before_request
def freshman_packet(uid, info=None):
    eboard = ldap_get_eboard()
    return render_template("packet.html", info=info, eboard=eboard)


@app.route("/csh-auth/")
@auth.oidc_auth
def csh_auth_test():
    # This just tests auth for now
    auth_info_json = json.dumps({"id_token": session["id_token"], "access_token": session["access_token"],
                                 "userinfo": session["userinfo"]}, indent=4)

    return """
            <h2>CSH auth succeeded. Here's the results:</h2>
            <pre>{}</pre>
        """.format(auth_info_json)


@app.route("/api/test/")
@auth.oidc_auth
def test_endpoint():
    # This just tests auth and DB access for API calls
    return jsonify({freshman.id: freshman.name for freshman in Freshman.query.all()})
