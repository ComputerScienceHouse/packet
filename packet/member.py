from collections import namedtuple

from sqlalchemy import exc

from .models import db
from .packet import get_number_required


def current_packets(member, intro=False, onfloor=False):
    """
    Get a list of currently open packets with the signed state of each packet.  Returns a <result>
    :param member: the member currently viewing all packets
    :param intro: true if current member is an intro member
    :param other: true if current member is off floor or alumni
    :return: <tuple> a list of packets that are currently open, and their attributes
    """

    # Tuple for compatibility with UI code.  Should be refactored or deleted altogether later
    SPacket = namedtuple('spacket', ['rit_username', 'name', 'did_sign', 'total_signatures', 'required_signatures'])

    packets = []
    required = get_number_required()

    if intro and onfloor:
        required -= 1

    signed_packets = get_signed_packets(member, intro, onfloor)

    try:
        result = db.engine.execute("SELECT packets.username AS username, packets.name AS name, packets.sigs_recvd "
                                   "AS received FROM "
                                   "((SELECT freshman.rit_username AS username, freshman.name AS name, packet.id "
                                   "AS id FROM freshman "
                                   "INNER JOIN packet ON freshman.rit_username = packet.freshman_username)"
                                   "AS a INNER JOIN"
                                   "(SELECT totals.id AS id, sum(totals.signed) AS sigs_recvd FROM "
                                   "(SELECT packet.id AS id, count(signature_fresh.signed) AS signed FROM packet "
                                   "FULL OUTER JOIN signature_fresh ON signature_fresh.packet_id = packet.id "
                                   "WHERE signature_fresh.signed = TRUE "
                                   "AND packet.start < now() AND now() < packet.end "
                                   "GROUP BY packet.id UNION SELECT packet.id AS id, count(signature_upper.signed) "
                                   "AS signed FROM packet "
                                   "FULL OUTER JOIN signature_upper ON signature_upper.packet_id = packet.id "
                                   "WHERE signature_upper.signed = TRUE "
                                   "AND packet.start < now() AND now() < packet.end"
                                   " GROUP BY packet.id) totals GROUP BY totals.id) "
                                   "AS b ON a.id = b.id ) AS packets;")

        for pkt in result:
            signed = signed_packets.get(pkt.username)
            if signed is None:
                signed = False
            packets.append(SPacket(pkt.username, pkt.name, signed, pkt.received, required))

    except exc.SQLAlchemyError:
        return None  # TODO; Handle Errors Properly

    return packets


def get_signed_packets(member, intro=False, onfloor=False):
    """
    Get a list of all packets that a member has signed
    :param member: member retrieving prior packet signatures
    :param intro: is the member an intro member?
    :param onfloor: is the member on floor?
    :return: <dict> usernames mapped to signed status
    """
    signed_packets = {}

    try:
        if intro and onfloor:
            result = db.engine.execute("SELECT DISTINCT packet.freshman_username AS username, signature_fresh.signed AS signed "
                              "FROM packet INNER JOIN signature_fresh ON packet.id = signature_fresh.packet_id "
                                       "WHERE signature_fresh.freshman_username = " + member + ";")

            for signature in result:
                signed_packets[signature.username] = signature.signed

        if not intro:
            if onfloor:
                result = db.engine.execute(
                    "SELECT DISTINCT packet.freshman_username AS username, signature_upper.signed AS signed "
                    "FROM packet INNER JOIN signature_upper ON packet.id = signature_upper.packet_id "
                    "WHERE signature_upper.member = '" + member + "';")

                for signature in result:
                    signed_packets[signature.username] = signature.signed

            else:
                result = db.engine.execute(
                    "SELECT DISTINCT packet.freshman_username AS username, signature_misc.member AS signed "
                    "FROM packet LEFT OUTER JOIN signature_misc ON packet.id = signature_misc.packet_id "
                    "WHERE signature_misc.member = '" + member + "' OR signature_misc.member ISNULL;")

                for signature in result:
                    if signature.signed is not None:
                        signed_packets[signature.username] = True
                    else:
                        signed_packets[signature.username] = False

    except exc.SQLAlchemyError:
        return signed_packets  # TODO; More error handling

    return signed_packets
