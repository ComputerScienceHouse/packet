from packet import auth, app
from packet.utils import before_request
from packet.packet import sign as sign_packet


@app.route("/api/v1/<member_username>/sign/<packet_username>", methods=["POST"])
@auth.oidc_auth
@before_request
def sign(member_username, packet_username, info):
    if info['uid'] != member_username:
        if info['member_info']:
            if "eboard-evaluations" not in info['member_info']['group_list']:
                return "Error: You are not evals"
        else:
            return "Error: UID Submission Mismatch"
    if not sign_packet(member_username, packet_username):
        return "Error: Signature not valid.  Reason: Unknown"
    return "Success: Signed Packet: " + packet_username

