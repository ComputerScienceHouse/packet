"""
Defines the application's database models
"""

from datetime import datetime
from itertools import chain
from typing import cast, Optional

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from . import db

# The required number of honorary member, advisor, and alumni signatures
REQUIRED_MISC_SIGNATURES = 10


class SigCounts:
    """
    Utility class for returning counts of signatures broken out by type
    """
    def __init__(self, upper: int, fresh: int, misc: int):
        # Base fields
        self.upper = upper
        self.fresh = fresh
        self.misc = misc

        # Capped version of misc so it will never be greater than REQUIRED_MISC_SIGNATURES
        self.misc_capped = misc if misc <= REQUIRED_MISC_SIGNATURES else REQUIRED_MISC_SIGNATURES

        # Totals (calculated using misc_capped)
        self.member_total = upper + self.misc_capped
        self.total = upper + fresh + self.misc_capped


class Freshman(db.Model):
    __tablename__ = 'freshman'
    rit_username = cast(str, Column(String(10), primary_key=True))
    name = cast(str, Column(String(64), nullable=False))
    onfloor = cast(bool, Column(Boolean, nullable=False))
    fresh_signatures = cast('FreshSignature', relationship('FreshSignature'))

    # One freshman can have multiple packets if they repeat the intro process
    packets = cast('Packet', relationship('Packet', order_by='desc(Packet.id)'))

    @classmethod
    def by_username(cls, username: str) -> 'Packet':
        """
        Helper method to retrieve a freshman by their RIT username
        """
        return cls.query.filter_by(rit_username=username).first()

    @classmethod
    def get_all(cls) -> list['Packet']:
        """
        Helper method to get all freshmen easily
        """
        return cls.query.all()


class Packet(db.Model):
    __tablename__ = 'packet'
    id = cast(int, Column(Integer, primary_key=True, autoincrement=True))
    freshman_username = cast(str, Column(ForeignKey('freshman.rit_username')))
    start = cast(datetime, Column(DateTime, nullable=False))
    end = cast(datetime, Column(DateTime, nullable=False))

    freshman = cast(Freshman, relationship('Freshman', back_populates='packets'))

    # The `lazy='subquery'` kwarg enables eager loading for signatures which makes signature calculations much faster
    # See the docs here for details: https://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html
    upper_signatures = cast('UpperSignature', relationship('UpperSignature', lazy='subquery',
                                    order_by='UpperSignature.signed.desc(), UpperSignature.updated'))
    fresh_signatures = cast('FreshSignature', relationship('FreshSignature', lazy='subquery',
                                    order_by='FreshSignature.signed.desc(), FreshSignature.updated'))
    misc_signatures = cast('MiscSignature',
            relationship('MiscSignature', lazy='subquery', order_by='MiscSignature.updated'))

    def is_open(self) -> bool:
        return self.start < datetime.now() < self.end

    def signatures_required(self) -> SigCounts:
        """
        :return: A SigCounts instance with the fields set to the number of signatures received by this packet
        """
        upper = len(self.upper_signatures)
        fresh = len(self.fresh_signatures)

        return SigCounts(upper, fresh, REQUIRED_MISC_SIGNATURES)

    def signatures_received(self) -> SigCounts:
        """
        :return: A SigCounts instance with the fields set to the number of required signatures for this packet
        """
        upper = sum(map(lambda sig: 1 if sig.signed else 0, self.upper_signatures))
        fresh = sum(map(lambda sig: 1 if sig.signed else 0, self.fresh_signatures))

        return SigCounts(upper, fresh, len(self.misc_signatures))

    def did_sign(self, username: str, is_csh: bool) -> bool:
        """
        :param username: The CSH or RIT username to check for
        :param is_csh: Set to True for CSH accounts and False for freshmen
        :return: Boolean value for if the given account signed this packet
        """
        if is_csh:
            for sig in filter(lambda sig: sig.member == username, chain(self.upper_signatures, self.misc_signatures)):
                if isinstance(sig, MiscSignature):
                    return True
                else:
                    return sig.signed
        else:
            for sig in filter(lambda sig: sig.freshman_username == username, self.fresh_signatures):
                return sig.signed

        # The user must be a misc CSHer that hasn't signed this packet or an off-floor freshmen
        return False

    def is_100(self) -> bool:
        """
        Checks if this packet has reached 100%
        """
        return self.signatures_required().total == self.signatures_received().total

    @classmethod
    def open_packets(cls) -> list['Packet']:
        """
        Helper method for fetching all currently open packets
        """
        return cls.query.filter(cls.start < datetime.now(), cls.end > datetime.now()).all()

    @classmethod
    def by_id(cls, packet_id: int) -> 'Packet':
        """
        Helper method for fetching 1 packet by its id
        """
        return cls.query.filter_by(id=packet_id).first()

class UpperSignature(db.Model):
    __tablename__ = 'signature_upper'
    packet_id = cast(int, Column(Integer, ForeignKey('packet.id'), primary_key=True))
    member = cast(str, Column(String(36), primary_key=True))
    signed = cast(bool, Column(Boolean, default=False, nullable=False))
    eboard = cast(Optional[str], Column(String(12), nullable=True))
    active_rtp = cast(bool, Column(Boolean, default=False, nullable=False))
    three_da = cast(bool, Column(Boolean, default=False, nullable=False))
    webmaster = cast(bool, Column(Boolean, default=False, nullable=False))
    c_m = cast(bool, Column(Boolean, default=False, nullable=False))
    w_m = cast(bool, Column(Boolean, default=False, nullable=False))
    drink_admin = cast(bool, Column(Boolean, default=False, nullable=False))
    updated = cast(datetime, Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False))

    packet = cast(Packet, relationship('Packet', back_populates='upper_signatures'))


class FreshSignature(db.Model):
    __tablename__ = 'signature_fresh'
    packet_id = cast(int, Column(Integer, ForeignKey('packet.id'), primary_key=True))
    freshman_username = cast(str, Column(ForeignKey('freshman.rit_username'), primary_key=True))
    signed = cast(bool, Column(Boolean, default=False, nullable=False))
    updated = cast(datetime, Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False))

    packet = cast(Packet, relationship('Packet', back_populates='fresh_signatures'))
    freshman = cast(Freshman, relationship('Freshman', back_populates='fresh_signatures'))


class MiscSignature(db.Model):
    __tablename__ = 'signature_misc'
    packet_id = cast(int, Column(Integer, ForeignKey('packet.id'), primary_key=True))
    member = cast(str, Column(String(36), primary_key=True))
    updated = cast(datetime, Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False))

    packet = cast(Packet, relationship('Packet', back_populates='misc_signatures'))


class NotificationSubscription(db.Model):
    __tablename__ = 'notification_subscriptions'
    member = cast(str, Column(String(36), nullable=True))
    freshman_username = cast(str, Column(ForeignKey('freshman.rit_username'), nullable=True))
    token = cast(str, Column(String(256), primary_key=True, nullable=False))
