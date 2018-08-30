from packet import auth, app
from packet.utils import before_request
from packet.packet import sign


@app.route("/api/v1/<member_username>/sign/<packet_username>")
@auth.oidc_auth
@before_request
def sign(member_username, packet_username, info):
    if info.uid != member_username and "eboard-evaluations" not in info.member_info.group_list:
        return "Error: UID Submission Mismatch"
    if not sign(member_username, packet_username):
        return "Error: Signature not valid.  Reason: Unknown"
    return "Success: Signed Packet: " + packet_username
