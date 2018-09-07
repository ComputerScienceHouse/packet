from datetime import datetime

from .models import Packet, Freshman, FreshSignature, UpperSignature, MiscSignature, db


def signed_packets(member, intro=False):
    # Checks whether or not member is a freshman
    if intro:
        return db.session.query(Packet.freshman_username, Freshman.name, FreshSignature.signed) \
            .select_from(FreshSignature).join(Packet).join(Freshman) \
            .filter(FreshSignature.freshman_username == member) \
            .filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).all()
    # Checks whether or not member is an upperclassman
    if db.session.query(UpperSignature.member).filter(UpperSignature.member == member).count() > 0:
        return db.session.query(Freshman.rit_username, Freshman.name, UpperSignature.signed) \
            .select_from(UpperSignature).join(Packet).join(Freshman) \
            .filter(UpperSignature.member == member) \
            .filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).all()
    return db.session.query(Freshman.rit_username, Freshman.name, MiscSignature.member.isnot(None)) \
        .select_from(Freshman).join(Packet).outerjoin(MiscSignature) \
        .filter(Packet.end > datetime.now()).filter(Packet.start < datetime.now()).all()
