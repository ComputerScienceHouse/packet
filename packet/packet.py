from packet.ldap import ldap_get_member, ldap_is_intromember
from .models import Freshman, UpperSignature, FreshSignature, MiscSignature, db


def sign(signer_username, freshman_username):
    if signer_username == freshman_username:
        return False

    freshman_signed = Freshman.query.filter_by(rit_username=freshman_username).first()
    if freshman_signed is None:
        return False
    packet = freshman_signed.current_packet()
    if packet is None or not packet.is_open():
        return False

    upper_signature = UpperSignature.query.filter(UpperSignature.member == signer_username,
                                                  UpperSignature.packet == packet).first()
    fresh_signature = FreshSignature.query.filter(FreshSignature.freshman_username == signer_username,
                                                  FreshSignature.packet == packet).first()

    if upper_signature:
        if ldap_is_intromember(ldap_get_member(signer_username)):
            return False
        upper_signature.signed = True
    elif fresh_signature:
        # Make sure only on floor freshmen can sign packets
        freshman_signer = Freshman.query.filter_by(rit_username=signer_username).first()
        if freshman_signer and not freshman_signer.onfloor:
            return False
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
        db.session.query(MiscSignature).filter(MiscSignature.member == signer_username).delete()
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
    packet = Freshman.query.filter_by(rit_username=freshman_username).first().current_packet()
    eboard = db.session.query(UpperSignature.member,
                              UpperSignature.signed,
                              UpperSignature.packet_id,
                              UpperSignature.eboard)\
        .filter(UpperSignature.packet_id == packet.id, UpperSignature.eboard.is_(True))\
        .order_by(UpperSignature.signed.desc())
    upper_signatures = db.session.query(UpperSignature.member,
                                        UpperSignature.packet_id,
                                        UpperSignature.eboard)\
        .filter(UpperSignature.packet_id == packet.id, UpperSignature.eboard.is_(False))\
        .order_by(UpperSignature.signed.desc())
    fresh_signatures = db.session.query(FreshSignature.freshman_username,
                                        FreshSignature.packet_id,
                                        FreshSignature.signed)\
        .filter(FreshSignature.packet_id == packet.id)\
        .order_by(FreshSignature.signed.desc())
    misc_signatures = db.session.query(MiscSignature.member, MiscSignature.packet_id)\
        .filter(MiscSignature.packet_id == packet.id)
    return {'eboard': eboard,
            'upperclassmen': upper_signatures,
            'freshmen': fresh_signatures,
            'misc': misc_signatures}


def get_number_signed(freshman_username):
    return Freshman.query.filter_by(rit_username=freshman_username).first().current_packet().signatures_received()


def get_number_required(freshman_username):
    return Freshman.query.filter_by(rit_username=freshman_username).first().current_packet().signatures_required()
