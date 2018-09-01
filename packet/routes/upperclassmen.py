from flask import redirect, render_template

from packet import auth, app
from packet.models import UpperSignature
from packet.utils import before_request


@app.route("/")
@auth.oidc_auth
def index():
    return redirect("/packets", 302)


@app.route("/member/<uid>")
@auth.oidc_auth
@before_request
def upperclassman(uid, info=None):
    signatures = UpperSignature.query.filter_by(member=uid).order_by(UpperSignature.signed.desc())
    return render_template("upperclassman.html", info=info, signatures=signatures, member=uid)
