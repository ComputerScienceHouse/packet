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
REQUIRED_MISC_SIGNATURES: int = 10


class SigCounts:
    """
    Utility class for returning counts of signatures broken out by type
    """

    def __init__(self, upper: int, fresh: int, misc: int):
        """
        Initialize the SigCounts instance.

        Args:
            upper (int): The number of upper signatures.
            fresh (int): The number of freshman signatures.
            misc (int): The number of miscellaneous signatures.
        """

        # Base fields
        self.upper: int = upper
        self.fresh: int = fresh
        self.misc: int = misc

        # Capped version of misc so it will never be greater than REQUIRED_MISC_SIGNATURES
        self.misc_capped: int = (
            misc if misc <= REQUIRED_MISC_SIGNATURES else REQUIRED_MISC_SIGNATURES
        )

        # Totals (calculated using misc_capped)
        self.member_total: int = upper + self.misc_capped
        self.total: int = upper + fresh + self.misc_capped


class Freshman(db.Model):
    """
    Represents a freshman student in the database.
    """

    __tablename__: str = "freshman"

    rit_username = cast(str, Column(String(10), primary_key=True))
    name = cast(str, Column(String(64), nullable=False))
    onfloor = cast(bool, Column(Boolean, nullable=False))
    fresh_signatures = cast("FreshSignature", relationship("FreshSignature"))

    # One freshman can have multiple packets if they repeat the intro process
    packets = cast("Packet", relationship("Packet", order_by="desc(Packet.id)"))

    @classmethod
    def by_username(cls, username: str) -> "Packet":
        """
        Helper method to retrieve a freshman by their RIT username

        Args:
            username (str): The RIT username of the freshman.

        Returns:
            Freshman: The freshman with the given RIT username, or None if not found.
        """

        return cls.query.filter_by(rit_username=username).first()

    @classmethod
    def get_all(cls) -> list["Packet"]:
        """
        Helper method to get all freshmen easily

        Args:
            cls: The class being queried.

        Returns:
            list[Freshman]: A list of all freshmen.
        """

        return cls.query.all()


class Packet(db.Model):
    """
    Represents a packet in the database.
    """

    __tablename__: str = "packet"

    id = cast(int, Column(Integer, primary_key=True, autoincrement=True))
    freshman_username = cast(str, Column(ForeignKey("freshman.rit_username")))
    start = cast(datetime, Column(DateTime, nullable=False))
    end = cast(datetime, Column(DateTime, nullable=False))

    freshman = cast(Freshman, relationship("Freshman", back_populates="packets"))

    # The `lazy='subquery'` kwarg enables eager loading for signatures which makes signature calculations much faster
    # See the docs here for details: https://docs.sqlalchemy.org/en/latest/orm/loading_relationships.html
    upper_signatures = cast(
        "UpperSignature",
        relationship(
            "UpperSignature",
            lazy="subquery",
            order_by="UpperSignature.signed.desc(), UpperSignature.updated",
        ),
    )
    fresh_signatures = cast(
        "FreshSignature",
        relationship(
            "FreshSignature",
            lazy="subquery",
            order_by="FreshSignature.signed.desc(), FreshSignature.updated",
        ),
    )
    misc_signatures = cast(
        "MiscSignature",
        relationship(
            "MiscSignature", lazy="subquery", order_by="MiscSignature.updated"
        ),
    )

    def is_open(self) -> bool:
        """
        Checks if the packet is currently open.

        Returns:
            bool: True if the packet is open, False otherwise.
        """

        return self.start < datetime.now() < self.end

    def signatures_required(self) -> SigCounts:
        """
        Calculates the number of signatures required for this packet.

        Returns:
            SigCounts: A SigCounts instance with the fields set to the number of signatures required by this packet
        """

        upper: int = len(self.upper_signatures)
        fresh: int = len(self.fresh_signatures)

        return SigCounts(upper, fresh, REQUIRED_MISC_SIGNATURES)

    def signatures_received(self) -> SigCounts:
        """
        Calculates the number of signatures received for this packet.

        Returns:
            SigCounts: A SigCounts instance with the fields set to the number of signatures received for this packet
        """

        upper: int = sum(map(lambda sig: 1 if sig.signed else 0, self.upper_signatures))
        fresh: int = sum(map(lambda sig: 1 if sig.signed else 0, self.fresh_signatures))

        return SigCounts(upper, fresh, len(self.misc_signatures))

    def did_sign(self, username: str, is_csh: bool) -> bool:
        """
        Checks if the given account signed this packet.

        Args:
            username: The CSH or RIT username to check for
            is_csh: Set to True for CSH accounts and False for freshmen
        Returns:
            bool: True if the given account signed this packet, False otherwise
        """

        if not is_csh:
            for sig in filter(
                lambda sig: sig.freshman_username == username, self.fresh_signatures
            ):
                return sig.signed

        for sig in filter(
            lambda sig: sig.member == username,
            chain(self.upper_signatures, self.misc_signatures),
        ):
            if isinstance(sig, MiscSignature):
                return True

            return sig.signed

        # The user must be a misc CSHer that hasn't signed this packet or an off-floor freshmen
        return False

    def is_100(self) -> bool:
        """
        Checks if this packet has reached 100%

        Returns:
            bool: True if the packet is 100% signed, False otherwise
        """

        return self.signatures_required().total == self.signatures_received().total

    @classmethod
    def open_packets(cls) -> list["Packet"]:
        """
        Helper method for fetching all currently open packets

        Args:
            cls: The class itself (Packet)

        Returns:
            list[Packet]: A list of all currently open packets
        """

        return cls.query.filter(
            cls.start < datetime.now(), cls.end > datetime.now()
        ).all()

    @classmethod
    def by_id(cls, packet_id: int) -> "Packet":
        """
        Helper method for fetching 1 packet by its id

        Args:
            cls: The class itself (Packet)
            packet_id: The id of the packet to fetch

        Returns:
            Packet: The packet with the given id, or None if not found
        """

        return cls.query.filter_by(id=packet_id).first()


class UpperSignature(db.Model):
    """
    Represents a signature from an upperclassman.
    """

    __tablename__: str = "signature_upper"

    packet_id = cast(int, Column(Integer, ForeignKey("packet.id"), primary_key=True))
    member = cast(str, Column(String(36), primary_key=True))
    signed = cast(bool, Column(Boolean, default=False, nullable=False))
    eboard = cast(Optional[str], Column(String(12), nullable=True))
    active_rtp = cast(bool, Column(Boolean, default=False, nullable=False))
    three_da = cast(bool, Column(Boolean, default=False, nullable=False))
    webmaster = cast(bool, Column(Boolean, default=False, nullable=False))
    c_m = cast(bool, Column(Boolean, default=False, nullable=False))
    w_m = cast(bool, Column(Boolean, default=False, nullable=False))
    drink_admin = cast(bool, Column(Boolean, default=False, nullable=False))
    updated = cast(
        datetime,
        Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False),
    )

    packet = cast(Packet, relationship("Packet", back_populates="upper_signatures"))


class FreshSignature(db.Model):
    """
    Represents a signature from a freshman.
    """

    __tablename__ = "signature_fresh"
    packet_id = cast(int, Column(Integer, ForeignKey("packet.id"), primary_key=True))
    freshman_username = cast(
        str, Column(ForeignKey("freshman.rit_username"), primary_key=True)
    )
    signed = cast(bool, Column(Boolean, default=False, nullable=False))
    updated = cast(
        datetime,
        Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False),
    )

    packet = cast(Packet, relationship("Packet", back_populates="fresh_signatures"))
    freshman = cast(
        Freshman, relationship("Freshman", back_populates="fresh_signatures")
    )


class MiscSignature(db.Model):
    """
    Represents a signature from a miscellaneous member.
    """

    __tablename__ = "signature_misc"
    packet_id = cast(int, Column(Integer, ForeignKey("packet.id"), primary_key=True))
    member = cast(str, Column(String(36), primary_key=True))
    updated = cast(
        datetime,
        Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False),
    )

    packet = cast(Packet, relationship("Packet", back_populates="misc_signatures"))


class NotificationSubscription(db.Model):
    """
    Represents a notification subscription for a member or freshman.
    """

    __tablename__ = "notification_subscriptions"
    member = cast(str, Column(String(36), nullable=True))
    freshman_username = cast(
        str, Column(ForeignKey("freshman.rit_username"), nullable=True)
    )

    token = cast(str, Column(String(256), primary_key=True, nullable=False))
