"""
Defines the application's database models.
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean

from . import db

# The required number of off-floor and alumni signatures
REQUIRED_MISC_SIGNATURES = 15

def end_date():
    return datetime.now() + timedelta(days=14)

class Freshman(db.Model):
    __tablename__ = "freshman"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    onfloor = Column(Boolean, nullable=False)

class Packet(db.Model):
    __tablename__ = "packet"
    id = Column(Integer, primary_key=True)
    freshman = Column(ForeignKey("freshman.id"), nullable=False)
    start = Column(DateTime, default=datetime.now, nullable=False)
    end = Column(DateTime, default=end_date, nullable=False)
    info_eboard = Column(Text, nullable=True)       # Used to fulfil the eboard description requirement
    info_events = Column(Text, nullable=True)       # Used to fulfil the events list requirement
    info_achieve = Column(Text, nullable=True)      # Used to fulfil the technical achievements list requirement

    def signatures_req(self):
        upper_count = UpperSignature.query.filter(UpperSignature.packet == self.id).count()
        fresh_count = FreshSignature.query.filter(FreshSignature.packet == self.id).count()
        return upper_count + fresh_count + REQUIRED_MISC_SIGNATURES

    def signatures_received(self):
        """
        Result capped so it will never be greater than that of signatures_req()
        """
        upper_count = UpperSignature.query.filter(UpperSignature.packet == self.id, UpperSignature.signed is True)\
            .count()
        fresh_count = FreshSignature.query.filter(FreshSignature.packet == self.id, FreshSignature.signed is True)\
            .count()
        misc_count = MiscSignature.query.filter(MiscSignature.packet == self.id).count()
        
        if misc_count > REQUIRED_MISC_SIGNATURES:
            misc_count = REQUIRED_MISC_SIGNATURES

        return upper_count + fresh_count + misc_count

class UpperSignature(db.Model):
    __tablename__ = "signature_upper"
    packet = Column(Integer, ForeignKey("packet.id"), primary_key=True)
    member = Column(String(36), primary_key=True)
    signed = Column(Boolean, default=False, nullable=False)
    updated = Column(DateTime, onupdate=datetime.now, nullable=False)

class FreshSignature(db.Model):
    __tablename__ = "signature_fresh"
    packet = Column(Integer, ForeignKey("packet.id"), primary_key=True)
    freshman = Column(ForeignKey("freshman.id"), primary_key=True)
    signed = Column(Boolean, default=False, nullable=False)
    updated = Column(DateTime, onupdate=datetime.now, nullable=False)

class MiscSignature(db.Model):
    __tablename__ = "signature_misc"
    packet = Column(Integer, ForeignKey("packet.id"), primary_key=True)
    member = Column(String(36), primary_key=True)
    updated = Column(DateTime, onupdate=datetime.now, nullable=False)
