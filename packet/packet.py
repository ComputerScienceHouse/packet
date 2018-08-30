from .models import *


def sign(member_username, freshman_username):
    freshman = Freshman.query.filter_by(rit_username=freshman_username)[0]
    packet = freshman.current_packet()
    if UpperSignature.query.filter_by(member=member_username, eboard=True)[0]:
        UpperSignature.query.filter_by(member=member_username, eboard=True)[0].signed = True
    elif UpperSignature.query.filter_by(member=member_username)[0]:
        UpperSignature.query.filter_by(member=member_username)[0].signed = True
    elif FreshSignature.query.filter_by(member=member_username)[0]:
        FreshSignature.query.filter_by(member=member_username)[0].signed = True
    else:
        db.session.add(MiscSignature(packet.id, member_username, datetime.now(), packet))
    db.session.commit()
    return True


def get_signatures(freshman_username):
    packet = Freshman.query.filter_by(rit_username=freshman_username)[0].current_packet()
    eboard = UpperSignature.query.filter_by(packet_id=packet.id, eboard=True)
    upper_signatures = UpperSignature.query.filter_by(packet_id=packet.id, eboard=False)
    return eboard, \
           upper_signatures, \
           FreshSignature.query.filter_by(packet_id=packet.id), \
           MiscSignature.query.filter_by(packet_id=packet.id)


def get_numbers_eboard(freshman_username):
    packet = Packet.query(freshman_username=freshman_username)
    packet.upper_signatures.filter_by(signed=True, eboard=True)


def get_numbers_upperclassmen(freshman_username):
    packet = Packet.query(freshman_username=freshman_username)
    packet.upper_signatures.filter_by(signed=True, eboard=False).count()


def get_numbers_freshmen(freshman_username):
    packet = Packet.query(freshman_username=freshman_username)
    packet.fresh_signatures.filter_by(signed=True).count()


def get_numbers_misc(freshman_username):
    packet = Packet.query(freshman_username=freshman_username)
    return packet.misc_signatures.count()


def get_numbers_total(freshman_username):
    packet = Packet.query(freshman_username=freshman_username)
    return packet.signatures_received(), packet.signatures_required()
