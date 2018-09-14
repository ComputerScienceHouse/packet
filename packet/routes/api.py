from packet import auth, app, db
from packet.utils import before_request
from packet.models import Packet, MiscSignature


@app.route("/api/v1/sign/<packet_username>/<packet_id>/", methods=["POST"])
@auth.oidc_auth
@before_request
def sign(packet_username, packet_id, info):
    packet = Packet.query.filter_by(freshman_username=packet_username, id=packet_id).first()

    if packet is not None and packet.is_open():
        if app.config["REALM"] == "csh":
            # Check if the CSHer is an upperclassman and if so, sign that row
            for sig in filter(lambda sig: sig.member == info["uid"], packet.upper_signatures):
                sig.signed = True
                db.session.commit()
                return "Success: Signed Packet: " + packet_username

            # The CSHer is a misc so add a new row
            db.session.add(MiscSignature(packet=packet, member=info["uid"]))
            db.session.commit()
            return "Success: Signed Packet: " + packet_username
        else:
            # Check if the freshman is onfloor and if so, sign that row
            for sig in filter(lambda sig: sig.freshman_username == info["uid"], packet.fresh_signatures):
                sig.signed = True
                db.session.commit()
                return "Success: Signed Packet: " + packet_username

    return "Error: Signature not valid.  Reason: Unknown"
