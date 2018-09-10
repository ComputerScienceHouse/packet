from collections import namedtuple
from logging import getLogger

from sqlalchemy import exc

from .models import db, REQUIRED_MISC_SIGNATURES
from .packet import get_number_required, get_misc_signatures

LOGGER = getLogger(__name__)


def current_packets(member, intro=False, onfloor=False):
    """
    Get a list of currently open packets with the signed state of each packet.
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
    misc_signatures = get_misc_signatures()

    try:
        for pkt in query_packets_with_signed():
            signed = signed_packets.get(pkt.username)
            misc = misc_signatures.get(pkt.username)
            if signed is None:
                signed = False
            if misc is None:
                misc = 0
            if misc > REQUIRED_MISC_SIGNATURES:
                misc = REQUIRED_MISC_SIGNATURES
            packets.append(SPacket(pkt.username, pkt.name, signed, pkt.received + misc, required))

    except exc.SQLAlchemyError as e:
        LOGGER.error(e)
        raise e

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
            for signature in query_signed_intromember(member):
                signed_packets[signature.username] = signature.signed

        if not intro:
            if onfloor:
                for signature in query_signed_upperclassman(member):
                    signed_packets[signature.username] = signature.signed

            else:
                for signature in query_signed_alumni(member):
                    signed_packets[signature.username] = bool(signature.signed)

    except exc.SQLAlchemyError as e:
        LOGGER.error(e)
        raise e

    return signed_packets


def query_packets_with_signed():
    """
    Query the database and return a list of currently open packets and the number of signatures they currently have
    :return: a list of results: intro members with open packets, their name, username, and number of signatures received
    """
    try:
        return db.engine.execute("""
        SELECT packets.username AS username, packets.name AS name, coalesce(packets.sigs_recvd, 0) AS received 
         FROM ( ( SELECT freshman.rit_username 
         AS username, freshman.name AS name, packet.id AS id, packet.start AS start, packet.end AS end 
         FROM freshman INNER JOIN packet ON freshman.rit_username = packet.freshman_username) AS a 
                       LEFT JOIN (  SELECT totals.id  AS id, coalesce(sum(totals.signed), 0)  AS sigs_recvd 
                       FROM ( SELECT packet.id AS id, coalesce(count(signature_fresh.signed), 0) AS signed 
                       FROM packet FULL OUTER JOIN signature_fresh ON signature_fresh.packet_id = packet.id 
                       WHERE signature_fresh.signed = TRUE  AND packet.start < now() AND now() < packet.end 
                       GROUP BY packet.id 
                       UNION SELECT packet.id AS id, coalesce(count(signature_upper.signed), 0) AS signed FROM packet 
                       FULL OUTER JOIN signature_upper ON signature_upper.packet_id = packet.id 
                       WHERE signature_upper.signed = TRUE AND packet.start < now() AND now() < packet.end 
                       GROUP BY packet.id ) totals GROUP BY totals.id ) AS b ON a.id = b.id ) AS packets 
                       WHERE packets.start < now() AND now() < packets.end; 
                                """)

    except exc.SQLAlchemyError:
        raise exc.SQLAlchemyError("Error: Failed to get open packets with signatures received from database")


def query_signed_intromember(member):
    """
    Query the database and return the list of packets signed by the given intro member
    :param member: the user making the query
    :return: list of results matching the query
    """
    try:
        return db.engine.execute("""
            SELECT DISTINCT packet.freshman_username AS username, signature_fresh.signed AS signed FROM packet 
            INNER JOIN signature_fresh ON packet.id = signature_fresh.packet_id 
            WHERE signature_fresh.freshman_username = '""" + member + "';")

    except exc.SQLAlchemyError:
        raise exc.SQLAlchemyError("Error: Failed to get intromember's signatures from database")


def query_signed_upperclassman(member):
    """
    Query the database and return the list of packets signed by the given upperclassman
    :param member: the user making the query
    :return: list of results matching the query
    """
    try:
        return db.engine.execute("""
            SELECT DISTINCT packet.freshman_username AS username, signature_upper.signed AS signed FROM packet 
            INNER JOIN signature_upper ON packet.id = signature_upper.packet_id 
            WHERE signature_upper.member = '""" + member + "';")

    except exc.SQLAlchemyError:
        raise exc.SQLAlchemyError("Error: Failed to get upperclassman's signatures from database")


def query_signed_alumni(member):
    """
    Query the database and return the list of packets signed by the given alumni/off-floor
    :param member: the user making the query
    :return: list of results matching the query
    """
    try:
        return db.engine.execute("""
            SELECT DISTINCT packet.freshman_username AS username, signature_misc.member AS signed 
            FROM packet LEFT OUTER JOIN signature_misc ON packet.id = signature_misc.packet_id 
            WHERE signature_misc.member = '""" + member + "' OR signature_misc.member ISNULL;")

    except exc.SQLAlchemyError:
        raise exc.SQLAlchemyError("Error: Failed to get alumni's signatures from database")
