"""
Routes available to freshmen only
"""

from typing import Any
from flask import Response, redirect, url_for

from packet import app
from packet.models import Packet
from packet.utils import before_request, packet_auth


@app.route('/')
@packet_auth
@before_request
def index(info: dict[str, Any]) -> Response:
    """
    Redirect to the most recent packet for the user.

    Args:
        info (dict[str, Any]): The user information dictionary.

    Returns:
        Response: The redirect response.
    """

    most_recent_packet = (
        Packet.query.filter_by(freshman_username=info['uid'])
        .order_by(Packet.id.desc())  # type: ignore
        .first()
    )

    if most_recent_packet is not None:
        return redirect(url_for('freshman_packet', packet_id=most_recent_packet.id), 302)

    return redirect(url_for('packets'), 302)
