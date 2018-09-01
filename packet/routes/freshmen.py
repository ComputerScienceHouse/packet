from flask import redirect

from packet import auth, app
from packet.utils import before_request


@app.route("/")
@auth.oidc_auth
@before_request
def index(info=None):
    return redirect("/packet/" + info['uid'], 302)
