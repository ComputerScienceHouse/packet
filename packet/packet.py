from datetime import datetime
from functools import lru_cache

from sqlalchemy import exc, false, true

from packet.ldap import ldap_get_member, ldap_is_intromember
from .models import Freshman, UpperSignature, FreshSignature, MiscSignature, db, Packet


def sign(signer_username, freshman_username):
    if not valid_signature(signer_username, freshman_username):
        return False

    packet = get_freshman(freshman_username).current_packet()
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
        freshman_signer = get_freshman(signer_username)
        if freshman_signer and not freshman_signer.onfloor:
            return False
        fresh_signature.signed = True
    else:
        db.session.add(MiscSignature(packet=packet, member=signer_username))
    db.session.commit()

    clear_cache()

    return True


def get_essays(freshman_username):
    packet = Freshman.query.filter_by(rit_username=freshman_username).first().current_packet()
    return {'eboard': packet.info_eboard,
            'events': packet.info_events,
            'achieve': packet.info_achieve}


def set_essays(freshman_username, eboard=None, events=None, achieve=None):
    packet = Freshman.query.filter_by(rit_username=freshman_username).first().current_packet()
    if eboard is not None:
        packet.info_eboard = eboard
    if events is not None:
        packet.info_events = events
    if achieve is not None:
        packet.info_achieve = achieve
    try:
        db.session.commit()
    except exc.SQLAlchemyError:
        return False
    return True


@lru_cache(maxsize=512)
def get_signatures(freshman_username):
    """
    Gets a list of all signatures for the given member
    :param freshman_username: the freshman to get the signatures in their most recent packet
    :return: <dict><list> list of signatures for the different categories
    """
    packet = Freshman.query.filter_by(rit_username=freshman_username).first().current_packet()

    eboard = db.session.query(UpperSignature.member, UpperSignature.signed, Freshman.rit_username) \
        .select_from(UpperSignature).join(Packet).join(Freshman) \
        .filter(UpperSignature.packet_id == packet.id, UpperSignature.eboard.is_(True)) \
        .order_by(UpperSignature.signed.desc()) \
        .distinct().all()

    upper_signatures = db.session.query(UpperSignature.member, UpperSignature.signed, Freshman.rit_username) \
        .select_from(UpperSignature).join(Packet).join(Freshman) \
        .filter(UpperSignature.packet_id == packet.id, UpperSignature.eboard.is_(False)) \
        .order_by(UpperSignature.signed.desc()) \
        .distinct().all()
    fresh_signatures = db.session.query(
        FreshSignature.freshman_username, FreshSignature.signed, Freshman.rit_username, Freshman.name) \
        .select_from(Packet).join(FreshSignature).join(Freshman) \
        .filter(FreshSignature.packet_id == packet.id) \
        .order_by(FreshSignature.signed.desc()) \
        .distinct().all()

    misc_signatures = db.session.query(MiscSignature.member, Freshman.rit_username) \
        .select_from(MiscSignature).join(Packet).join(Freshman) \
        .filter(MiscSignature.packet_id == packet.id) \
        .order_by(MiscSignature.updated.asc()) \
        .distinct().all()

    return {'eboard': eboard,
            'upperclassmen': upper_signatures,
            'freshmen': fresh_signatures,
            'misc': misc_signatures}


@lru_cache(maxsize=512)
def get_misc_signatures():
    packet_misc_sigs = {}
    try:
        result = db.engine.execute("""
            SELECT packet.freshman_username AS username, count(signature_misc.member) AS signatures FROM packet 
            RIGHT OUTER JOIN signature_misc ON packet.id = signature_misc.packet_id 
            GROUP BY packet.freshman_username;
            """)
        for packet in result:
            packet_misc_sigs[packet.username] = packet.signatures
    except exc.SQLAlchemyError:
        raise exc.SQLAlchemyError("Error: Unable to query miscellaneous signatures from database")
    return packet_misc_sigs


@lru_cache(maxsize=512)
def valid_signature(signer_username, freshman_username):
    if signer_username == freshman_username:
        return False

    freshman_signed = get_freshman(freshman_username)
    if freshman_signed is None:
        return False

    packet = freshman_signed.current_packet()
    if packet is None or not packet.is_open():
        return False

    return True


def get_freshman(freshman_username):
    return Freshman.query.filter_by(rit_username=freshman_username).first()


def get_current_packet(freshman_username):
    return get_freshman(freshman_username).current_packet()


@lru_cache(maxsize=512)
def get_number_signed(freshman_username, separated=False):
    """
    Gets the raw number of signatures for the user
    :param freshman_username: The user to get signature numbers for
    :param separated: A boolean indicating whether to return the results as separated
    :return: <Packet> list of results that are in the form of Packet database objects
    """
    return db.session.query(Packet) \
        .filter(Packet.freshman_username == freshman_username,
                Packet.start < datetime.now(), Packet.end > datetime.now()) \
        .first().signatures_received(not separated)


@lru_cache(maxsize=256)
def get_number_required_on_floor(separated=False):
    """
    Get the number of required signatures for Packet (not counting on/off-floor status)
    :param separated: whether or not to separate those by category
    :return: a map or an integer of total signatures required
    """
    return db.session.query(Packet).join(Freshman).filter(
        Packet.start < datetime.now(),
        Packet.end > datetime.now(),
        Freshman.onfloor == true()
    ).first().signatures_required(not separated)


@lru_cache(maxsize=256)
def get_number_required_off_floor(separated=False):
    """
    Get the number of required signatures for Packet (not counting on/off-floor status)
    :param separated: whether or not to separate those by category
    :return: a map or an integer of total signatures required
    """
    return db.session.query(Packet).join(Freshman).filter(
        Packet.start < datetime.now(),
        Packet.end > datetime.now(),
        Freshman.onfloor == false()
    ).first().signatures_required(not separated)


@lru_cache(maxsize=512)
def get_upperclassmen_percent(username, onfloor=False):
    if onfloor:
        required = get_number_required_on_floor(True)
    else:
        required = get_number_required_off_floor(True)
    upperclassmen_required = required['upperclassmen'] + required['eboard'] + required['miscellaneous']

    signatures = get_number_signed(username, True)
    upperclassmen_signature = signatures['upperclassmen'] + signatures['eboard'] + signatures['miscellaneous']

    return upperclassmen_signature / upperclassmen_required * 100


@lru_cache(maxsize=512)
def signed_packets(member):
    # Checks whether or not member is a freshman
    if get_freshman(member) is not None:
        return FreshSignature.query.filter_by(freshman_username=member, signed=True).all()
    # Checks whether or not member is an upperclassman
    if UpperSignature.query.filter_by(member=member).first() is not None:
        return UpperSignature.query.filter_by(member=member, signed=True).all()
    return MiscSignature.query.filter_by(member=member).all()


@lru_cache(maxsize=512)
def signed_packet(signer, freshman):
    packet = get_current_packet(freshman)
    freshman_signature = FreshSignature.query.filter_by(packet=packet, freshman_username=signer, signed=True).first()
    upper_signature = UpperSignature.query.filter_by(packet=packet, member=signer, signed=True).first()
    misc_signature = MiscSignature.query.filter_by(packet=packet, member=signer).first()

    if freshman_signature is not None:
        return freshman_signature.signed
    if upper_signature is not None:
        return upper_signature.signed
    if misc_signature is not None:
        return misc_signature
    return False


def clear_cache():
    """
    Clear cache of all frequently changing data
    """
    get_upperclassmen_percent.cache_clear()
    get_number_signed.cache_clear()
    get_number_required_on_floor.cache_clear()
    get_number_required_off_floor.cache_clear()
    signed_packets.cache_clear()
    get_signatures.cache_clear()
    get_misc_signatures.cache_clear()
