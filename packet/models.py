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

    def signatures_req(self):
        upper_count = UpperSignature.query.filter(
                UpperSignature.packet == self.id).count()
        fresh_count = FreshSignature.query.filter(
                FreshSignature.packet == self.id).count()
        all_count = upper_count + fresh_count + 15
        return all_count

    def signatures_total(self):
        upper_count = UpperSignature.query.filter(
                UpperSignature.packet == self.id,
                UpperSignature.signed == True).count()
        fresh_count = FreshSignature.query.filter(
                FreshSignature.packet == self.id,
                FreshSignature.signed == True).count()
        misc_count = MiscSignature.query.filter(
                MiscSignature.packet == self.id).count()
        sig_count = upper_count + fresh_count + misc_count
        return sig_count



class UpperSignature(db.Model):
    __tablename__ = 'signature_upper'
    packet = Column(Integer, ForeignKey('packet.id'), primary_key=True)
    member = Column(String(36), nullable=False)
    signed = Column(Boolean, default=False, nullable=False)
    updated = Column(DateTime, onupdate=datetime.now, nullable=False)


class FreshSignature(db.Model):
    __tablename__ = 'signature_fresh'
    packet = Column(Integer, ForeignKey('packet.id'), primary_key=True)
    freshman = Column(ForeignKey('freshman.id'), nullable=False)
    signed = Column(Boolean, default=False, nullable=False)
    updated = Column(DateTime, onupdate=datetime.now, nullable=False)


class MiscSignature(db.Model):
    __tablename__ = 'signature_misc'
    packet = Column(Integer, ForeignKey('packet.id'), primary_key=True)
    member = Column(String(36), nullable=False)
    updated = Column(DateTime, onupdate=datetime.now, nullable=False)

