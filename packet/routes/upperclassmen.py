"""
Routes available to CSH users only
"""
import json

from operator import itemgetter
from typing import Optional, Dict, Any, List
from flask import redirect, render_template, url_for, Response

from packet import app
from packet.models import Packet
from packet.utils import before_request, packet_auth
from packet.log_utils import log_cache, log_time
from packet.stats import packet_stats


@app.route('/')
@packet_auth
def index() -> Response:
    return redirect(url_for('packets'), 302)


@app.route('/member/<uid>/')
@log_cache
@packet_auth
@before_request
@log_time
def upperclassman(uid: str, info: Optional[Dict[str, Any]] = None) -> str:
    open_packets = Packet.open_packets()

    # Pre-calculate and store the return value of did_sign()
    for packet in open_packets:
        packet.did_sign_result = packet.did_sign(uid, True)

    signatures: int = sum(map(lambda packet: 1 if packet.did_sign_result else 0, open_packets))

    open_packets.sort(key=lambda packet: packet.freshman_username)
    open_packets.sort(key=lambda packet: packet.did_sign_result, reverse=True)

    return render_template('upperclassman.html', info=info, open_packets=open_packets, member=uid,
                           signatures=signatures)


@app.route('/upperclassmen/')
@log_cache
@packet_auth
@before_request
@log_time
def upperclassmen_total(info: Optional[Dict[str, Any]] = None) -> str:
    open_packets = Packet.open_packets()

    # Sum up the signed packets per upperclassman
    upperclassmen: Dict[str, int] = dict()
    misc: Dict[str, int] = dict()
    for packet in open_packets:
        for sig in packet.upper_signatures:
            if sig.member not in upperclassmen:
                upperclassmen[sig.member] = 0

            if sig.signed:
                upperclassmen[sig.member] += 1
        for sig in packet.misc_signatures:
            misc[sig.member] = 1 + misc.get(sig.member, 0)

    return render_template('upperclassmen_totals.html', info=info, num_open_packets=len(open_packets),
                           upperclassmen=sorted(upperclassmen.items(), key=itemgetter(1), reverse=True),
                           misc=sorted(misc.items(), key=itemgetter(1), reverse=True))


@app.route('/stats/packet/<packet_id>')
@packet_auth
@before_request
def packet_graphs(packet_id: int, info: Optional[Dict[str, Any]] = None) -> str:
    stats = packet_stats(packet_id)
    fresh: List[int] = []
    misc: List[int] = []
    upper: List[int] = []

    # Make a rolling sum of signatures over time
    def agg(l: List[int], attr: str, date: str) -> None:
        l.append((l[-1] if l else 0) + len(stats['dates'][date][attr]))

    dates: List[str] = list(stats['dates'].keys())
    for date in dates:
        agg(fresh, 'fresh', date)
        agg(misc, 'misc', date)
        agg(upper, 'upper', date)

    # Stack misc and upper on top of fresh for a nice stacked line graph
    for i in range(len(dates)):
        misc[i] = misc[i] + fresh[i]
        upper[i] = upper[i] + misc[i]

    return render_template('packet_stats.html',
        info=info,
        data=json.dumps({
            'dates': dates,
            'accum': {
                'fresh': fresh,
                'misc': misc,
                'upper': upper,
                },
            'daily': {

                }
        }),
        fresh=stats['freshman'],
        packet=Packet.by_id(packet_id),
    )
