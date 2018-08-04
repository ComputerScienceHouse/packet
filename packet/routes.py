"""
Routes live here for now. As the application is built out they'll be refactored and split into blueprints.
"""

import json
from flask import session, jsonify

from . import auth, app
from .models import Freshman

@app.route("/")
def index():
    return """
            <center>
                <h2>CSH web packet mk2</h2>
                <p>Coming soon to a server near you</p>
            </center>
        """

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
