from .models import *
from . import ldap
import datetime

def sign(member_username, freshman_username):
    member = ldap.ldap_get_member(member_username)
    if member:
        if ldap.ldap_is_onfloor(member):
            eboard = ldap.ldap_is_eboard(member)
            packet = Packet.query.filter_by(freshman_username=freshman_username)
            signature = UpperSignature(packet.id, member_username, True, eboard, datetime.now(), packet)
            db.session.add(signature)
            db.session.commit()
        elif ldap.ldap_is_intromember(member):
            packet = Packet.query.filter_by(freshman_username=freshman_username)
            signature = FreshSignature(packet.id, member_username, True, datetime.now(), packet)
            db.session.add(signature)
            db.session.commit()
        else:
            packet = Packet.query.filter_by(freshman_username=freshman_username)
            signature = MiscSignature(packet.id, member_username, datetime.now(), packet)
            db.session.add(signature)
            db.session.commit()
    else:
        return {'error': "User is not a valid Member"}

def get_signatures(freshman_username):
    packet = Packet.query(freshman_username=freshman_username)
    signatures=[]
    for signature in UpperSignature.query.filter_by(packet_id=packet.id, signed=True):
        signatures.append(signature.member)
    for signature in FreshSignature.query.filter_by(packet_id=packet.id, signed=True):
        signatures.append(signature.member)
    for signature in MiscSignature.query.filter_by(packet_id=packet.id):
        signatures.append(signature.member)
    return signatures

def get_numbers(freshman_username):
    packet = Packet.query(freshman_username=freshman_username)
    return packet.signatures_received(), packet.signatures_required()