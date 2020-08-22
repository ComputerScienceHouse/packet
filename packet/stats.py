from datetime import timedelta

from packet.models import Packet, MiscSignature, UpperSignature


def packet_stats(packet_id):
    """
    Gather statistics for a packet in the form of number of signatures per day

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
    packet = Packet.by_id(packet_id)

    dates = [packet.start.date() + timedelta(days=x) for x in range(0, (packet.end-packet.start).days + 1)]

    print(dates)

    upper_stats = {date: list() for date in dates}
    for uid, date in map(lambda sig: (sig.member, sig.updated),
                         filter(lambda sig: sig.signed, packet.upper_signatures)):
        upper_stats[date.date()].append(uid)

    fresh_stats = {date: list() for date in dates}
    for username, date in map(lambda sig: (sig.freshman_username, sig.updated),
                              filter(lambda sig: sig.signed, packet.fresh_signatures)):
        fresh_stats[date.date()].append(username)

    misc_stats = {date: list() for date in dates}
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


def sig2dict(sig):
    """
    A utility function for upperclassman stats.
    Converts an UpperSignature to a dictionary with the date and the packet.
    """
    packet = Packet.by_id(sig.packet_id)
    return {
            'date': sig.updated.date(),
            'packet': {
                'id': packet.id,
                'freshman_username': packet.freshman_username,
                },
            }


def upperclassman_stats(uid):
    """
    Gather statistics for an upperclassman's signature habits

    Return format: {
        member: <uid>,
        signautes: {
            <date>: [{
                id: <packet_id>,
                freshman_username,
            }],
        },
    }
    """

    sigs = UpperSignature.query.filter(
            UpperSignature.signed,
            UpperSignature.member == uid
            ).all() + MiscSignature.query.filter(MiscSignature.member == uid).all()

    sig_dicts = list(map(sig2dict, sigs))

    dates = set(map(lambda sd: sd['date'], sig_dicts))

    return {
            'member': uid,
            'signatures': {
                date.isoformat() : list(
                    map(lambda sd: sd['packet'],
                        filter(lambda sig, d=date: sig['date'] == d,
                            sig_dicts
                            )
                        )
                    ) for date in dates
                }
            }
