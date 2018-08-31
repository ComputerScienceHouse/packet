from datetime import datetime
from .models import Freshman, UpperSignature, FreshSignature, MiscSignature, db


def sign(signer_username, freshman_username):
    freshman = Freshman.query.filter_by(rit_username=freshman_username)[0]
    packet = freshman.current_packet()
    if packet is None:
        return False
    if not packet.is_open():
        return False

    upper_signature = UpperSignature.query.filter_by(member=signer_username)[0]
    fresh_signature = FreshSignature.query.filter_by(freshman=signer_username)[0]
    if upper_signature:
        upper_signature.signed = True
    elif fresh_signature:
        fresh_signature.signed = True
    else:
        db.session.add(MiscSignature(packet.id, signer_username, datetime.now(), packet))
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


def get_number_signed(freshman_username):
    return Freshman.query.filter_by(rit_username=freshman_username)[0].current_packet().signatures_received()


def get_number_required(freshman_username):
    return Freshman.query.filter_by(rit_username=freshman_username)[0].current_packet().signatures_required()
