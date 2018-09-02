from .models import Freshman, UpperSignature, FreshSignature, MiscSignature, db


def sign(signer_username, freshman_username):
    freshman = Freshman.query.filter_by(rit_username=freshman_username).first()
    if freshman is None:
        return False
    packet = freshman.current_packet()
    if packet is None:
        return False
    if not packet.is_open():
        return False

    upper_signature = UpperSignature.query.filter(UpperSignature.member == signer_username).first()
    fresh_signature = FreshSignature.query.filter(FreshSignature.freshman_username == signer_username).first()

    if upper_signature:
        upper_signature.signed = True
    elif fresh_signature:
        fresh_signature.signed = True
    else:
        db.session.add(MiscSignature(packet=packet, member=signer_username))
    db.session.commit()

    return True


# This is a forbidden function.  Only those with the power of evals may wield it
def unsign(signer_username, freshman_username):
    freshman = Freshman.query.filter_by(rit_username=freshman_username).first()
    if freshman is None:
        return False
    packet = freshman.current_packet()
    if packet is None:
        return False
    if not packet.is_open():
        return False

    upper_signature = UpperSignature.query.filter(UpperSignature.member == signer_username).first()
    fresh_signature = FreshSignature.query.filter(FreshSignature.freshman_username == signer_username).first()

    if upper_signature:
        upper_signature.signed = False
    elif fresh_signature:
        fresh_signature.signed = False
    else:
        db.session.query(MiscSignature).filter(MiscSignature.member==signer_username).delete()
    db.session.commit()

    return True


def set_requirements(freshman_username, eboard=None, events=None, achieve=None):
    packet = Freshman.query.filter_by(rit_username=freshman_username).first().current_packet()
    if eboard is not None:
        packet.info_eboard = eboard
    if events is not None:
        packet.info_events = events
    if achieve is not None:
        packet.info_achieve = achieve
    db.session.commit()
    return True


def get_requirements(freshman_username):
    packet = Freshman.query.filter_by(rit_username=freshman_username).first().current_packet()
    return {'eboard': packet.info_eboard,
            'events': packet.info_events,
            'achieve': packet.info_achieve}


def get_signatures(freshman_username):
    packet = Freshman.query.filter_by(rit_username=freshman_username)[0].current_packet()
    eboard = UpperSignature.query.filter_by(packet_id=packet.id, eboard=True)
    upper_signatures = UpperSignature.query.filter_by(packet_id=packet.id, eboard=False)
    return {'eboard': eboard,
            'upperclassmen': upper_signatures,
            'freshmen': FreshSignature.query.filter_by(packet_id=packet.id),
            'misc': MiscSignature.query.filter_by(packet_id=packet.id)}


def get_number_signed(freshman_username):
    return Freshman.query.filter_by(rit_username=freshman_username).first().current_packet().signatures_received()


def get_number_required(freshman_username):
    return Freshman.query.filter_by(rit_username=freshman_username).first().current_packet().signatures_required()
