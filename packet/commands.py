"""
Defines command-line utilities for use with packet
"""

import sys

from secrets import token_hex
from datetime import datetime, time, date
import csv
import click

from . import app, db
from .models import Packet, FreshSignature, UpperSignature, MiscSignature
from .utils import sync_freshman, create_new_packets, sync_with_ldap


@app.cli.command('create-secret')
def create_secret() -> None:
    """
    Generates a securely random token. Useful for creating a value for use in the "SECRET_KEY" config setting.
    """
    print("Here's your random secure token:")
    print(token_hex())


packet_start_time = time(hour=19)
packet_end_time = time(hour=21)


class CSVFreshman:
    def __init__(self, row: list[str]) -> None:
        self.name = row[0].strip()
        self.rit_username = row[3].strip()
        self.onfloor = row[1].strip() == 'TRUE'


def parse_csv(freshmen_csv: str) -> dict[str, CSVFreshman]:
    print('Parsing file...')
    try:
        with open(freshmen_csv, newline='') as freshmen_csv_file:
            return {freshman.rit_username: freshman for freshman in map(CSVFreshman, csv.reader(freshmen_csv_file))}
    except Exception as e:
        print('Failure while parsing CSV')
        raise e


def input_date(prompt: str) -> date:
    while True:
        try:
            date_str = input(prompt + ' (format: MM/DD/YYYY): ')
            return datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            pass


@app.cli.command('sync-freshmen')
@click.argument('freshmen_csv')
def sync_freshmen(freshmen_csv: str) -> None:
    """
    Updates the freshmen entries in the DB to match the given CSV.
    """
    freshmen_in_csv = parse_csv(freshmen_csv)

    print('Syncing contents with the DB...')
    sync_freshman(freshmen_in_csv)
    print('Done!')


@app.cli.command('create-packets')
@click.argument('freshmen_csv')
def create_packets(freshmen_csv: str) -> None:
    """
    Creates a new packet season for each of the freshmen in the given CSV.
    """
    print("WARNING: The 'sync-freshmen' command must be run first to ensure that the state of floor is up to date.")
    if input('Continue? (y/N): ').lower() != 'y':
        return

    # Collect the necessary data
    base_date = input_date('Input the first day of packet season')
    freshmen_in_csv = parse_csv(freshmen_csv)
    create_new_packets(base_date, freshmen_in_csv)
    print('Done!')


@app.cli.command('ldap-sync')
def ldap_sync() -> None:
    """
    Updates the upper and misc sigs in the DB to match ldap.
    """
    sync_with_ldap()
    print('Done!')


@app.cli.command('fetch-results')
@click.option('-f', '--file', 'file_path', required=False, type=click.Path(exists=False, writable=True),
        help='The file to write to. If no file provided, output is sent to stdout.')
@click.option('--csv/--no-csv', 'use_csv', required=False, default=False, help='Format output as comma separated list.')
@click.option('--date', 'date_str', required=False, default='', help='Packet end date in the format MM/DD/YYYY.')
def fetch_results(file_path: str, use_csv: bool, date_str: str) -> None:
    """
    Fetches and prints the results from a given packet season.
    """
    end_date = None
    try:
        end_date = datetime.combine(datetime.strptime(date_str, '%m/%d/%Y').date(), packet_end_time)
    except ValueError:
        end_date = datetime.combine(input_date("Enter the last day of the packet season you'd like to retrieve results "
                                           'from'), packet_end_time)


    file_handle = open(file_path, 'w', newline='') if file_path else sys.stdout

    column_titles = ['Name (RIT Username)', 'Upperclassmen Score', 'Total Score', 'Upperclassmen', 'Freshmen',
            'Miscellaneous', 'Total Missed']
    data = list()
    for packet in Packet.query.filter_by(end=end_date).all():
        received = packet.signatures_received()
        required = packet.signatures_required()

        row = [
        '{} ({}):'.format(packet.freshman.name, packet.freshman.rit_username),
        '{:0.2f}%'.format(received.member_total / required.member_total * 100),
        '{:0.2f}%'.format(received.total / required.total * 100),
        '{}/{}'.format(received.upper, required.upper),
        '{}/{}'.format(received.fresh, required.fresh),
        '{}/{}'.format(received.misc, required.misc),
        required.total - received.total,
        ]
        data.append(row)

    if use_csv:
        writer = csv.writer(file_handle)
        writer.writerow(column_titles)
        writer.writerows(data)
    else:
        for row in data:
            file_handle.write(f'''

{row[0]}
\t{column_titles[1]}: {row[1]}
\t{column_titles[2]}: {row[2]}
\t{column_titles[3]}: {row[3]}
\t{column_titles[4]}: {row[4]}
\t{column_titles[5]}: {row[5]}

\t{column_titles[6]}: {row[6]}
''')


@app.cli.command('extend-packet')
@click.argument('packet_id')
def extend_packet(packet_id: int) -> None:
    """
    Extends the given packet by setting a new end date.
    """
    packet = Packet.by_id(packet_id)

    if not packet.is_open():
        print('Packet is already closed so it cannot be extended')
        return
    else:
        print('Ready to extend packet #{} for {}'.format(packet_id, packet.freshman_username))

    packet.end = datetime.combine(input_date('Enter the new end date for this packet'), packet_end_time)
    db.session.commit()

    print('Packet successfully extended')


def remove_sig(packet_id: int, username: str, is_member: bool) -> None:
    packet = Packet.by_id(packet_id)

    if not packet.is_open():
        print('Packet is already closed so its signatures cannot be modified')
        return
    elif is_member:
        sig = UpperSignature.query.filter_by(packet_id=packet_id, member=username).first()
        if sig is not None:
            sig.signed = False
            db.session.commit()
            print('Successfully unsigned packet')
        else:
            result = MiscSignature.query.filter_by(packet_id=packet_id, member=username).delete()
            if result == 1:
                db.session.commit()
                print('Successfully unsigned packet')
            else:
                print('Failed to unsign packet; could not find signature')
    else:
        sig = FreshSignature.query.filter_by(packet_id=packet_id, freshman_username=username).first()
        if sig is not None:
            sig.signed = False
            db.session.commit()
            print('Successfully unsigned packet')
        else:
            print('Failed to unsign packet; {} is not an onfloor'.format(username))


@app.cli.command('remove-member-sig')
@click.argument('packet_id')
@click.argument('member')
def remove_member_sig(packet_id: int, member: str) -> None:
    """
    Removes the given member's signature from the given packet.
    :param member: The member's CSH username
    """
    remove_sig(packet_id, member, True)


@app.cli.command('remove-freshman-sig')
@click.argument('packet_id')
@click.argument('freshman')
def remove_freshman_sig(packet_id: int, freshman: str) -> None:
    """
    Removes the given freshman's signature from the given packet.
    :param freshman: The freshman's RIT username
    """
    remove_sig(packet_id, freshman, False)
