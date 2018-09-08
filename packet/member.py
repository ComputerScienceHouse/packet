from datetime import datetime

from .models import Packet, Freshman, FreshSignature, UpperSignature, MiscSignature, db


def current_packets(member, intro=False, other=False):
    """
    Get a list of currently open packets with the signed state of each packet.  Returns a <result>
    :param member: the member currently viewing all packets
    :param intro: true if current member is an intro member
    :param other: true if current member is off floor or alumni
    :return: <result> a list of packets that are currently open
    """

    # Checks whether or not member is a freshman
    if intro:
        return db.session.query(Packet.freshman_username, Freshman.name, FreshSignature.signed) \
            .select_from(FreshSignature).join(Packet).join(Freshman) \
            .filter(FreshSignature.freshman_username == member) \
            .filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).all()

    # Checks whether or not member is an upperclassman, and onfloor
    if not other:
        return db.session.query(Freshman.rit_username, Freshman.name, UpperSignature.signed) \
            .select_from(UpperSignature).join(Packet).join(Freshman) \
            .filter(UpperSignature.member == member) \
            .filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).all()

    # Off floor / Alumni case
    return db.session.query(Freshman.rit_username, Freshman.name, MiscSignature.member.isnot(None)) \
        .select_from(Freshman).join(Packet).outerjoin(MiscSignature) \
        .filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).all()
