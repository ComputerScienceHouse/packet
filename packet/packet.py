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
    return {'eboard': eboard,
            'upperclassmen': upper_signatures,
            'freshmen': FreshSignature.query.filter_by(packet_id=packet.id),
            'misc': MiscSignature.query.filter_by(packet_id=packet.id)}


def get_numbers_signed(freshman_username):
    return Freshman.query.filter_by(rit_username=freshman_username)[0].current_packet().signatures_recieved()


def get_numbers_required(freshman_username):
    return Freshman.query.filter_by(rit_username=freshman_username)[0].current_packet().signatures_required()
