from flask import render_template, redirect

from packet import auth, app
from packet.ldap import ldap_is_eboard
from packet.member import current_packets
from packet.packet import get_number_signed, signed_packet, get_freshman, \
    get_number_required_off_floor, get_number_required_on_floor
from packet.packet import get_signatures, get_upperclassmen_percent
from packet.utils import before_request


@app.route('/logout')
@auth.oidc_logout
def logout():
    return redirect("/")


@app.route("/packet/<uid>")
@auth.oidc_auth
@before_request
def freshman_packet(uid, info=None):
    freshman = get_freshman(uid)
    upperclassmen_percent = get_upperclassmen_percent(uid)
    signatures = get_signatures(uid)
    signed_dict = get_number_signed(uid, True)
    if freshman.onfloor:
        required = get_number_required_on_floor()
    else:
        required = get_number_required_off_floor()
    signed = get_number_signed(uid)

    packet_signed = signed_packet(info['uid'], uid)
    return render_template("packet.html", info=info, signatures=signatures, uid=uid, required=required, signed=signed,
                           freshman=freshman, packet_signed=packet_signed, upperclassmen_percent=upperclassmen_percent,
                           signed_dict=signed_dict)


@app.route("/packets")
@auth.oidc_auth
@before_request
def packets(info=None):
    if app.config["REALM"] == "csh":
        if info["member_info"]["onfloor"]:
            if info["member_info"]["room"] is not None or ldap_is_eboard(info['user_obj']):
                open_packets = current_packets(info["uid"], False, True)
            else:
                open_packets = current_packets(info["uid"], False, False)
        else:
            open_packets = current_packets(info["uid"], False, False)
    else:
        open_packets = current_packets(info["uid"], True, info["onfloor"])

    open_packets.sort(key=lambda x: x.total_signatures, reverse=True)
    open_packets.sort(key=lambda x: x.did_sign, reverse=True)

    return render_template("active_packets.html", info=info, packets=open_packets)
