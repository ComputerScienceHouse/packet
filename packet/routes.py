"""
Routes live here for now. As the application is built out they'll be refactored and split into blueprints.
"""

import json
from flask import session, jsonify, render_template

from . import auth, app
from .models import Freshman


@app.route("/")
def index():
    return render_template("list_setup.html", info=info)


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
