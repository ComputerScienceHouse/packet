import os
import json

from flask import Flask, session, jsonify
from flask_pyoidc.flask_pyoidc import OIDCAuthentication

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

auth = OIDCAuthentication(app, issuer=app.config["OIDC_ISSUER"],
                          client_registration_info=app.config["OIDC_CLIENT_CONFIG"])

# Create the database session and import models
db = SQLAlchemy(app)
from packet.models import * # pylint: disable=wrong-import-position, wildcard-import

migrate = Migrate(app, db)

@app.route("/")
@auth.oidc_auth
def index():
    # This just tests auth for now
    auth_info_json = json.dumps({"id_token": session["id_token"], "access_token": session["access_token"],
                               "userinfo": session["userinfo"]}, indent=4)

    return """
            <h2>CSH auth succeeded. Here's the results:</h2>
            <pre>{}</pre>
        """.format(auth_info_json)

@app.route("/api/test")
@auth.oidc_auth
def test_endpoint():
    # This just tests auth and DB access for API calls
    return jsonify({freshman.id: freshman.name for freshman in Freshman.query.all()})
