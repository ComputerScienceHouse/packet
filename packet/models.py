"""
Defines the application's database models.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship

from . import db

# The required number of off-floor and alumni signatures
REQUIRED_MISC_SIGNATURES = 15


class SigCounts:
    """
    Utility class for returning counts of signatures broken out by type
    """
    def __init__(self, eboard, upper, fresh, misc):
        self.eboard = eboard
        self.upper = upper      # Upperclassmen excluding eboard
        self.fresh = fresh
        self.misc = misc
        self.member_total = eboard + upper + misc
        self.total = eboard + upper + fresh + misc


class Freshman(db.Model):
    __tablename__ = "freshman"
    rit_username = Column(String(10), primary_key=True)
    name = Column(String(64), nullable=False)
    onfloor = Column(Boolean, nullable=False)
    fresh_signatures = relationship("FreshSignature")

    # One freshman can have multiple packets if they repeat the intro process
    packets = relationship("Packet", order_by="desc(Packet.id)")

    def current_packet(self):
        """
        :return: The most recent packet for this freshman
        """
        return next(iter(self.packets), None)


class Packet(db.Model):
    __tablename__ = "packet"
    id = Column(Integer, primary_key=True, autoincrement=True)
    freshman_username = Column(ForeignKey("freshman.rit_username"))
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    info_eboard = Column(Text, nullable=True)   # Used to fulfil the eboard description requirement
    info_events = Column(Text, nullable=True)   # Used to fulfil the events list requirement
    info_achieve = Column(Text, nullable=True)  # Used to fulfil the technical achievements list requirement

    freshman = relationship("Freshman", back_populates="packets")
    upper_signatures = relationship("UpperSignature")
    fresh_signatures = relationship("FreshSignature")
    misc_signatures = relationship("MiscSignature")

    def is_open(self):
        return self.start < datetime.now() < self.end

    def signatures_required(self):
        eboard = sum(map(lambda sig: 1 if sig.eboard else 0, self.upper_signatures))
        upper = len(self.upper_signatures) - eboard
        fresh = len(self.fresh_signatures)

        return SigCounts(eboard, upper, fresh, REQUIRED_MISC_SIGNATURES)

    def signatures_received(self):
        """
        Result capped so it will never be greater than that of signatures_required()
        """
        eboard = sum(map(lambda sig: 1 if sig.eboard and sig.signed else 0, self.upper_signatures))
        upper = sum(map(lambda sig: 1 if not sig.eboard and sig.signed else 0, self.upper_signatures))
        fresh = sum(map(lambda sig: 1 if sig.signed else 0, self.fresh_signatures))

        misc = len(self.misc_signatures)
        if misc > REQUIRED_MISC_SIGNATURES:
            misc = REQUIRED_MISC_SIGNATURES

        return SigCounts(eboard, upper, fresh, misc)


class UpperSignature(db.Model):
    __tablename__ = "signature_upper"
    packet_id = Column(Integer, ForeignKey("packet.id"), primary_key=True)
    member = Column(String(36), primary_key=True)
    signed = Column(Boolean, default=False, nullable=False)
    eboard = Column(Boolean, default=False, nullable=False)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    packet = relationship("Packet", back_populates="upper_signatures")


class FreshSignature(db.Model):
    __tablename__ = "signature_fresh"
    packet_id = Column(Integer, ForeignKey("packet.id"), primary_key=True)
    freshman_username = Column(ForeignKey("freshman.rit_username"), primary_key=True)
    signed = Column(Boolean, default=False, nullable=False)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    packet = relationship("Packet", back_populates="fresh_signatures")
    freshman = relationship("Freshman", back_populates="fresh_signatures")


class MiscSignature(db.Model):
    __tablename__ = "signature_misc"
    packet_id = Column(Integer, ForeignKey("packet.id"), primary_key=True)
    member = Column(String(36), primary_key=True)
    updated = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    packet = relationship("Packet", back_populates="misc_signatures")
