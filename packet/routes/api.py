"""
Shared API endpoints
"""

from datetime import datetime
from json import dumps
from typing import Dict, Any, Union, Tuple

from flask import session, request

from packet import app, db, ldap
from packet.context_processors import get_rit_name
from packet.log_utils import log_time
from packet.mail import send_report_mail
from packet.utils import (
    before_request,
    packet_auth,
    notify_slack,
    sync_freshman as sync_freshman_list,
    create_new_packets,
    sync_with_ldap,
)
from packet.models import Packet, MiscSignature, NotificationSubscription, Freshman
from packet.notifications import (
    packet_signed_notification,
    packet_100_percent_notification,
)
import packet.stats as stats


class POSTFreshman:
    """
    Represents a freshman POST request payload.
    """

    def __init__(self, freshman: Dict[str, Any]) -> None:
        """
        Initialize a POSTFreshman instance.

        Args:
            freshman (Dict[str, Any]): The freshman data.
        """
        self.name: str = freshman["name"].strip()
        self.rit_username: str = freshman["rit_username"].strip()
        self.onfloor: bool = freshman["onfloor"].strip() == "TRUE"


@app.route("/api/v1/freshmen", methods=["POST"])
@packet_auth
def sync_freshman() -> Tuple[str, int]:
    """
    Create or update freshmen entries from a list

    Returns:
        Tuple[str, int]: A tuple containing a success message and the HTTP status code.

    Body parameters: [
        {
         rit_username: string
         name: string
         onfloor: boolean
        }
    ]
    """

    # Only allow evals to create new frosh
    username: str = str(session["userinfo"].get("preferred_username", ""))
    if not ldap.is_evals(ldap.get_member(username)):
        return "Forbidden: not Evaluations Director", 403

    freshmen_in_post: Dict[str, POSTFreshman] = {
        freshman.rit_username: freshman for freshman in map(POSTFreshman, request.json)
    }
    sync_freshman_list(freshmen_in_post)
    return dumps("Done"), 200


@app.route("/api/v1/packets", methods=["POST"])
@packet_auth
@log_time
def create_packet() -> Tuple[str, int]:
    """
    Create a new packet.

    Returns:
        Tuple[str, int]: A tuple containing a success message and the HTTP status code.

    Body parameters: {
      start_date: the start date of the packets in MM/DD/YYYY format
      freshmen: [
        {
          rit_username: string
          name: string
          onfloor: boolean
        }
      ]
    }
    """

    # Only allow evals to create new packets
    username: str = str(session["userinfo"].get("preferred_username", ""))
    if not ldap.is_evals(ldap.get_member(username)):
        return "Forbidden: not Evaluations Director", 403

    base_date: datetime = datetime.strptime(request.json["start_date"], "%m/%d/%Y %H")

    freshmen_in_post: Dict[str, POSTFreshman] = {
        freshman.rit_username: freshman
        for freshman in map(POSTFreshman, request.json["freshmen"])
    }

    create_new_packets(base_date, freshmen_in_post)

    return dumps("Done"), 201


@app.route("/api/v1/sync", methods=["POST"])
@packet_auth
@log_time
def sync_ldap() -> Tuple[str, int]:
    """
    Sync LDAP with the database.

    Returns:
        Tuple[str, int]: A tuple containing a success message and the HTTP status code.
    """

    # Only allow evals to sync ldap
    username: str = str(session["userinfo"].get("preferred_username", ""))
    if not ldap.is_evals(ldap.get_member(username)):
        return "Forbidden: not Evaluations Director", 403
    sync_with_ldap()
    return dumps("Done"), 201


@app.route("/api/v1/packets/<username>", methods=["GET"])
@packet_auth
@before_request
def get_packets_by_user(
    username: str, info: Dict[str, Any]
) -> Union[Dict[int, Dict[str, Any]], Tuple[str, int]]:
    """
    Return a dictionary of packets for a freshman by username, giving packet start and end date by packet id

    Args:
        username (str): The username of the freshman.
        info (Dict[str, Any]): The user information dictionary.

    Returns:
        Union[Dict[int, Dict[str, Any]], Tuple[str, int]]: A dictionary of packets or an error message.
    """

    if info["ritdn"] != username:
        return "Forbidden - not your packet", 403

    frosh: Freshman = Freshman.by_username(username)

    return {
        packet.id: {
            "start": packet.start,
            "end": packet.end,
        }
        for packet in frosh.packets
    }


@app.route("/api/v1/packets/<username>/newest", methods=["GET"])
@packet_auth
@before_request
def get_newest_packet_by_user(
    username: str, info: Dict[str, Any]
) -> Union[Dict[int, Dict[str, Any]], Tuple[str, int]]:
    """
    Return a user's newest packet

    Args:
        username (str): The username of the user.
        info (Dict[str, Any]): The user information dictionary.

    Returns:
        Union[Dict[int, Dict[str, Any]], Tuple[str, int]]: The newest packet information or an error message.
    """

    if not info["is_upper"] and info["ritdn"] != username:
        return "Forbidden - not your packet", 403

    frosh: Freshman = Freshman.by_username(username)

    packet: Packet = frosh.packets[-1]

    return {
        packet.id: {
            "start": packet.start,
            "end": packet.end,
            "required": vars(packet.signatures_required()),
            "received": vars(packet.signatures_received()),
        }
    }


@app.route("/api/v1/packet/<int:packet_id>", methods=["GET"])
@packet_auth
@before_request
def get_packet_by_id(
    packet_id: int, info: Dict[str, Any]
) -> Union[Dict[str, Dict[str, Any]], Tuple[str, int]]:
    """
    Return the scores of the packet in question

    Args:
        packet_id (int): The ID of the packet.
        info (Dict[str, Any]): The user information dictionary.

    Returns:
        Union[Dict[str, Dict[str, Any]], Tuple[str, int]]: The packet scores or an error message.
    """

    packet: Packet = Packet.by_id(packet_id)

    if not info["is_upper"] and info["ritdn"] != packet.freshman.rit_username:
        return "Forbidden - not your packet", 403

    return {
        "required": vars(packet.signatures_required()),
        "received": vars(packet.signatures_received()),
    }


@app.route("/api/v1/sign/<int:packet_id>/", methods=["POST"])
@packet_auth
@before_request
def sign(packet_id: int, info: Dict[str, Any]) -> str:
    """
    Sign a packet for the user.

    Args:
        packet_id (int): The ID of the packet.
        info (Dict[str, Any]): The user information dictionary.

    Returns:
        str: A success message indicating the signature has been added.
    """

    packet: Packet = Packet.by_id(packet_id)

    if packet is not None and packet.is_open():
        was_100: bool = packet.is_100()
        if app.config["REALM"] == "csh":
            # Check if the CSHer is an upperclassman and if so, sign that row
            for sig in filter(
                lambda sig: sig.member == info["uid"], packet.upper_signatures
            ):
                sig.signed = True
                app.logger.info(
                    "Member {} signed packet {} as an upperclassman".format(
                        info["uid"], packet_id
                    )
                )
                return commit_sig(packet, was_100, info["uid"])

            # The CSHer is a misc so add a new row
            db.session.add(MiscSignature(packet=packet, member=info["uid"]))
            app.logger.info(
                "Member {} signed packet {} as a misc".format(info["uid"], packet_id)
            )

            return commit_sig(packet, was_100, info["uid"])
        else:
            # Check if the freshman is onfloor and if so, sign that row
            for sig in filter(
                lambda sig: sig.freshman_username == info["uid"],
                packet.fresh_signatures,
            ):
                sig.signed = True
                app.logger.info(
                    "Freshman {} signed packet {}".format(info["uid"], packet_id)
                )
                return commit_sig(packet, was_100, info["uid"])

    app.logger.warn(
        "Failed to add {}'s signature to packet {}".format(info["uid"], packet_id)
    )
    return "Error: Signature not valid.  Reason: Unknown"


@app.route("/api/v1/subscribe/", methods=["POST"])
@packet_auth
@before_request
def subscribe(info: Dict[str, Any]) -> str:
    """
    Subscribe a user to notifications.

    Args:
        info (Dict[str, Any]): The user information dictionary.

    Returns:
        str: A success message indicating the subscription has been created.
    """

    data = request.form
    subscription: NotificationSubscription
    if app.config["REALM"] == "csh":
        subscription = NotificationSubscription(token=data["token"], member=info["uid"])
    else:
        subscription = NotificationSubscription(
            token=data["token"], freshman_username=info["uid"]
        )
    db.session.add(subscription)
    db.session.commit()
    return "Token subscribed for " + info["uid"]


@app.route("/api/v1/report/", methods=["POST"])
@packet_auth
@before_request
def report(info: Dict[str, Any]) -> str:
    """
    Report an issue with a specific packet.

    Args:
        info (Dict[str, Any]): The user information dictionary.

    Returns:
        str: A success message indicating the report has been sent.
    """

    form_results = request.form
    send_report_mail(form_results, get_rit_name(info["uid"]))

    return "Success: " + get_rit_name(info["uid"]) + " sent a report"


@app.route("/api/v1/stats/packet/<int:packet_id>")
@packet_auth
@before_request
def packet_stats(
    packet_id: int, info: Dict[str, Any]
) -> Union[stats.PacketStats, Tuple[str, int]]:
    """
    Get statistics for a specific packet.

    Args:
        packet_id (int): The ID of the packet.
        info (Dict[str, Any]): The user information dictionary.

    Returns:
        Union[stats.PacketStats, Tuple[str, int]]: The packet statistics or an error message.
    """

    if (
        not info["is_upper"]
        and info["ritdn"] != Packet.by_id(packet_id).freshman.rit_username
    ):
        return "Forbidden - not your packet", 403

    return stats.packet_stats(packet_id)


@app.route("/api/v1/stats/upperclassman/<uid>")
@packet_auth
@before_request
def upperclassman_stats(
    uid: str, info: Dict[str, Any]
) -> Union[stats.UpperStats, Tuple[str, int]]:
    """
    Get statistics for a specific upperclassman.

    Args:
        uid (str): The user ID of the upperclassman.
        info (Dict[str, Any]): The user information dictionary.

    Returns:
        Union[stats.UpperStats, Tuple[str, int]]: The upperclassman statistics or an error message.
    """

    if not info["is_upper"]:
        return "Forbidden", 403

    return stats.upperclassman_stats(uid)


@app.route("/readiness")
def readiness() -> Tuple[str, int]:
    """
    Check the readiness of the application.

    Returns:
        Tuple[str, int]: A tuple containing the readiness status and the HTTP status code.
    """

    return "ready", 200


def commit_sig(packet: Packet, was_100: bool, uid: str) -> str:
    """
    Commit the signature to the database and send notifications.

    Args:
        packet (Packet): The packet to commit the signature for.
        was_100 (bool): Whether the packet was previously at 100% completion.
        uid (str): The user ID of the member signing the packet.

    Returns:
        str: A success message indicating the signature has been committed.
    """

    packet_signed_notification(packet, uid)
    db.session.commit()

    if not was_100 and packet.is_100():
        packet_100_percent_notification(packet)
        notify_slack(packet.freshman.name)

    return "Success: Signed Packet: " + packet.freshman_username
