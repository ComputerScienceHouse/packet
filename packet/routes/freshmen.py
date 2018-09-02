from flask import redirect, render_template

from packet import auth, app
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
    return render_template("essays.html", info=info)
