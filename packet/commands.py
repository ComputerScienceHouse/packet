"""
Defines command-line utilities for use with packet
"""

import sys

from secrets import token_hex
from datetime import datetime, time, date
import csv
import click
from typing import Union

from . import app, db
from .models import Packet, FreshSignature, UpperSignature, MiscSignature
from .utils import sync_freshman, sync_with_ldap


@app.cli.command('create-secret')
def create_secret() -> None:
    """
    Generates a securely random token. Useful for creating a value for use in the "SECRET_KEY" config setting.
    """

    print("Here's your random secure token:")
    print(token_hex())


packet_start_time: time = time(hour=19)
packet_end_time: time = time(hour=21)


class CSVFreshman:
    """
    Represents a freshman entry in the CSV file.
    """

    def __init__(self, row: list[str]) -> None:
        """
        Initializes a CSVFreshman instance from a CSV row.

        Args:
            row: The CSV row to initialize from.
        """

        self.name: str = row[0].strip()
        self.rit_username: str = row[3].strip()
        self.onfloor: bool = row[1].strip() == 'TRUE'


def parse_csv(freshmen_csv: str) -> dict[str, CSVFreshman]:
    """
    Parses a CSV file containing freshman data.

    Args:
        freshmen_csv: The path to the CSV file to parse.

    Returns:
        A dictionary mapping RIT usernames to their corresponding CSVFreshman instances.
    """

    print('Parsing file...')

    try:
        with open(freshmen_csv, newline='') as freshmen_csv_file:
            return {freshman.rit_username: freshman for freshman in map(CSVFreshman, csv.reader(freshmen_csv_file))}
    except Exception as e:
        print('Failure while parsing CSV')
        raise e


def input_date(prompt: str) -> date:
    """
    Prompts the user for a date input and returns it as a date object.

    Args:
        prompt: The prompt to display to the user.

    Returns:
        The date entered by the user.
    """

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

    Args:
        freshmen_csv: The path to the CSV file to sync.
    """

    freshmen_in_csv = parse_csv(freshmen_csv)

    print('Syncing contents with the DB...')
    sync_freshman(freshmen_in_csv)
    print('Done!')


# TODO: this needs fixed with a proper datetime
# @app.cli.command('create-packets')
# @click.argument('freshmen_csv')
# def create_packets(freshmen_csv: str) -> None:
#     """
#     Creates a new packet season for each of the freshmen in the given CSV.
#     """
#     print("WARNING: The 'sync-freshmen' command must be run first to ensure that the state of floor is up to date.")
#     if input('Continue? (y/N): ').lower() != 'y':
#         return

#     # Collect the necessary data
#     base_date = input_date('Input the first day of packet season')
#     freshmen_in_csv = parse_csv(freshmen_csv)
#     create_new_packets(base_date, freshmen_in_csv)
#     print('Done!')


@app.cli.command('ldap-sync')
def ldap_sync() -> None:
    """
    Updates the upper and misc sigs in the DB to match ldap.
    """

    sync_with_ldap()
    print('Done!')


@app.cli.command('fetch-results')
@click.option(
    '-f',
    '--file',
    'file_path',
    required=False,
    type=click.Path(exists=False, writable=True),
    help='The file to write to. If no file provided, output is sent to stdout.',
)
@click.option(
    '--csv/--no-csv',
    'use_csv',
    required=False,
    default=False,
    help='Format output as comma separated list.',
)
@click.option(
    '--date',
    'date_str',
    required=False,
    default='',
    help='Packet end date in the format MM/DD/YYYY.',
)
def fetch_results(file_path: str, use_csv: bool, date_str: str) -> None:
    """
    Fetches and prints the results from a given packet season.

    Args:
        file_path: The file to write the results to.
        use_csv: Whether to format the output as CSV.
        date_str: The end date of the packet season to retrieve results from.
    """

    end_date: Union[datetime, None] = None

    try:
        end_date = datetime.combine(datetime.strptime(date_str, '%m/%d/%Y').date(), packet_end_time)
    except ValueError:
        end_date = datetime.combine(
            input_date("Enter the last day of the packet season you'd like to retrieve results from"),
            packet_end_time,
        )

    file_handle = open(file_path, 'w', newline='') if file_path else sys.stdout

    column_titles = [
        'Name (RIT Username)',
        'Upperclassmen Score',
        'Total Score',
        'Upperclassmen',
        'Freshmen',
        'Miscellaneous',
        'Total Missed',
    ]
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
            """
            Old

            file_handle.write(
                f'''
                {row[0]}
                \t{column_titles[1]}: {row[1]}
                \t{column_titles[2]}: {row[2]}
                \t{column_titles[3]}: {row[3]}
                \t{column_titles[4]}: {row[4]}
                \t{column_titles[5]}: {row[5]}

                \t{column_titles[6]}: {row[6]}
                '''
            )
            """

            out: str = str(row[0]) + '\n'

            for i in range(1, 7):
                out += '\t{}: {}'.format(column_titles[i], row[i])

                if i != 6:
                    out += '\n'

                if i == 5:
                    out += '\n'

            file_handle.write(out + '\n')


@app.cli.command('extend-packet')
@click.argument('packet_id')
def extend_packet(packet_id: int) -> None:
    """
    Extends the given packet by setting a new end date.

    Args:
        packet_id: The ID of the packet to extend.
    """

    packet: Packet = Packet.by_id(packet_id)

    if not packet.is_open():
        print('Packet is already closed so it cannot be extended')
        return

    print('Ready to extend packet #{} for {}'.format(packet_id, packet.freshman_username))

    packet.end = datetime.combine(input_date('Enter the new end date for this packet'), packet_end_time)

    db.session.commit()

    print('Packet successfully extended')


def remove_sig(packet_id: int, username: str, is_member: bool) -> None:
    """
    Removes a signature from a packet.

    Args:
        packet_id: The ID of the packet to modify.
        username: The username of the member or freshman to remove.
        is_member: Whether the user is a member or a freshman.
    """

    packet: Packet = Packet.by_id(packet_id)

    if not packet.is_open():
        print('Packet is already closed so its signatures cannot be modified')
        return

    if is_member:
        sig = UpperSignature.query.filter_by(packet_id=packet_id, member=username).first()

        if sig is None and MiscSignature.query.filter_by(packet_id=packet_id, member=username).delete() != 1:
            print('Failed to unsign packet; could not find signature')
            return

        if sig:
            sig.signed = False

        db.session.commit()
        print('Successfully unsigned packet')
    else:
        sig = FreshSignature.query.filter_by(packet_id=packet_id, freshman_username=username).first()

        if sig is None:
            print('Failed to unsign packet; could not find signature')
            return

        sig.signed = False
        db.session.commit()
        print('Successfully unsigned packet')


@app.cli.command('remove-member-sig')
@click.argument('packet_id')
@click.argument('member')
def remove_member_sig(packet_id: int, member: str) -> None:
    """
    Removes the given member's signature from the given packet.

    Args:
        packet_id: The ID of the packet to modify.
        member: The member's CSH username
    """

    remove_sig(packet_id, member, True)


@app.cli.command('remove-freshman-sig')
@click.argument('packet_id')
@click.argument('freshman')
def remove_freshman_sig(packet_id: int, freshman: str) -> None:
    """
    Removes the given freshman's signature from the given packet.

    Args:
        packet_id: The ID of the packet to modify.
        freshman: The freshman's RIT username
    """

    remove_sig(packet_id, freshman, False)


@app.cli.command('remove-user-sig')
@click.argument('packet_id')
@click.argument('user')
def remove_user_sig(packet_id: int, user: str) -> None:
    """
    Removes the given user's signature from the given packet, whether they are a member or a freshman.

    Args:
        packet_id: The ID of the packet to modify.
        user: The user's username
    """

    remove_sig(packet_id, user, False)
    remove_sig(packet_id, user, True)
