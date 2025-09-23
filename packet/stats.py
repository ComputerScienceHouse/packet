from datetime import date as datetype, timedelta
from typing import TypedDict, Union, cast, Callable

from packet.models import Packet, MiscSignature, UpperSignature


# Types
class Freshman(TypedDict):
    """
    Represents a freshman student.

    Attributes:
        name: The name of the freshman.
        rit_username: The RIT username of the freshman.
    """

    name: str
    rit_username: str


class WhoSigned(TypedDict):
    """
    Represents the users who signed a packet.

    Attributes:
        upper: A list of upperclassman user IDs.
        misc: A list of miscellaneous user IDs.
        fresh: A list of freshman usernames.
    """

    upper: list[str]
    misc: list[str]
    fresh: list[str]


class PacketStats(TypedDict):
    """
    Represents the statistics for a packet.

    Attributes:
        packet_id: The ID of the packet.
        freshman: The freshman associated with the packet.
        dates: A dictionary mapping dates to the users who signed the packet on that date.
    """

    packet_id: int
    freshman: Freshman
    dates: dict[str, dict[str, list[str]]]


class SimplePacket(TypedDict):
    """
    Represents a simplified version of a packet.

    Attributes:
        id: The ID of the packet.
        freshman_username: The RIT username of the freshman associated with the packet.
    """

    id: int
    freshman_username: str


class SigDict(TypedDict):
    """
    Represents a signature's metadata.

    Attributes:
        date: The date the signature was made.
        packet: The packet associated with the signature.
    """

    date: datetype
    packet: SimplePacket


Stats = dict[datetype, list[str]]


def packet_stats(packet_id: int) -> PacketStats:
    """
    Gather statistics for a packet in the form of number of signatures per day

    Args:
        packet_id (int): The ID of the packet to gather statistics for.

    Returns:
        PacketStats: The statistics for the packet.

        Return format: {
            packet_id,
            freshman: {
                name,
                rit_username,
            },
            dates: {
            <date>: {
                    upper: [ uid ],
                    misc: [ uid ],
                    fresh: [ freshman_username ],
            },
            },
        }
    """

    packet: Packet = Packet.by_id(packet_id)

    dates = [packet.start.date() + timedelta(days=x) for x in range(0, (packet.end - packet.start).days + 1)]

    print(dates)

    upper_stats: Stats = {date: list() for date in dates}
    for uid, date in map(
        lambda sig: (sig.member, sig.updated),
        filter(lambda sig: sig.signed, packet.upper_signatures),
    ):
        upper_stats[date.date()].append(uid)

    fresh_stats: Stats = {date: list() for date in dates}
    for username, date in map(
        lambda sig: (sig.freshman_username, sig.updated),
        filter(lambda sig: sig.signed, packet.fresh_signatures),
    ):
        fresh_stats[date.date()].append(username)

    misc_stats: Stats = {date: list() for date in dates}
    for uid, date in map(lambda sig: (sig.member, sig.updated), packet.misc_signatures):
        misc_stats[date.date()].append(uid)

    total_stats = dict()
    for date in dates:
        total_stats[date.isoformat()] = {
            'upper': upper_stats[date],
            'fresh': fresh_stats[date],
            'misc': misc_stats[date],
        }

    return {
        'packet_id': packet_id,
        'freshman': {
            'name': packet.freshman.name,
            'rit_username': packet.freshman.rit_username,
        },
        'dates': total_stats,
    }


def sig2dict(sig: Union[UpperSignature, MiscSignature]) -> SigDict:
    """
    A utility function for upperclassman stats.
    Converts an UpperSignature to a dictionary with the date and the packet.

    Args:
        sig (UpperSignature): The signature to convert.

    Returns:
        SigDict: The converted signature dictionary.
    """

    packet = Packet.by_id(sig.packet_id)

    return {
        'date': sig.updated.date(),
        'packet': {
            'id': packet.id,
            'freshman_username': packet.freshman_username,
        },
    }


class UpperStats(TypedDict):
    """
    Represents the statistics for an upperclassman.

    Attributes:
        member: The UID of the upperclassman.
        signatures: A dictionary mapping dates to the packets signed by the upperclassman on that date.
    """

    member: str
    signatures: dict[str, list[SimplePacket]]


def upperclassman_stats(uid: str) -> UpperStats:
    """
    Gather statistics for an upperclassman's signature habits

    Args:
        uid (str): The UID of the upperclassman.

    Returns:
        UpperStats: The statistics for the upperclassman.

        Return format: {
            member: <uid>,
            signatures: {
                <date>: [{
                    id: <packet_id>,
                    freshman_username,
                }],
            },
        }
    """

    sigs = (
        UpperSignature.query.filter(UpperSignature.signed, UpperSignature.member == uid).all()
        + MiscSignature.query.filter(MiscSignature.member == uid).all()
    )

    sig_dicts = list(map(sig2dict, sigs))

    dates = set(map(lambda sd: sd['date'], sig_dicts))

    return {
        'member': uid,
        'signatures': {
            date.isoformat(): list(
                map(
                    lambda sd: sd['packet'],
                    filter(cast(Callable, lambda sig, d=date: sig['date'] == d), sig_dicts),
                )
            )
            for date in dates
        },
    }
