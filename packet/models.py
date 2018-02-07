from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date, Boolean
from datetime import datetime, timedelta
from packet import db


def end_date():
    current = datetime.now()
    end = current + timedelta(days=14)
    return end


class Freshman(db.Model):
    __tablename__ = 'freshman'
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    onfloor = Column(Boolean, nullable=False)


class Packet(db.Model):
    __tablename__ = 'packet'
    id = Column(Integer, primary_key=True)
    freshman = Column(ForeignKey('freshman.id'), nullable=False)
    start = Column(DateTime, default=datetime.now, nullable=False)
    end = Column(DateTime, default=end_date, nullable=False)
    announce = Column(Text, nullable=True)
    info_eboard = Column(Text, nullable=True)
    info_events = Column(Text, nullable=True)
    info_achieve = Column(Text, nullable=True)


class UpperSignature(db.Model):
    __tablename__ = 'signature_upper'
    packet = Column(Integer, ForeignKey('packet.id'), primary_key=True)
    member = Column(String(36), nullable=False)
    signed = Column(Boolean, default=False, nullable=False)


class FreshSignature(db.Model):
    __tablename__ = 'signature_fresh'
    packet = Column(Integer, ForeignKey('packet.id'), primary_key=True)
    freshman = Column(ForeignKey('freshman.id'), nullable=False)
    signed = Column(Boolean, default=False, nullable=False)


class MiscSignature(db.Model):
    __tablename__ = 'signature_misc'
    packet = Column(Integer, ForeignKey('packet.id'), primary_key=True)
    member = Column(String(36), nullable=False)

