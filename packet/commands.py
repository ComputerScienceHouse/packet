"""
Defines command-line utilities for use with the app
"""

from secrets import token_hex
from datetime import datetime, time, timedelta
import csv
import click

from . import app, db
from .models import Freshman, Packet, FreshSignature, UpperSignature, MiscSignature
from .ldap import ldap_get_eboard, ldap_get_live_onfloor

@app.cli.command("create-secret")
def create_secret():
    """
    Generates a securely random token. Useful for creating a value for use in the "SECRET_KEY" config setting.
    """
    print("Here's your random secure token:")
    print(token_hex())

packet_start_time = time(hour=19)
packet_end_time = time(hour=21)

class CSVFreshman:
    def __init__(self, row):
        self.name = row[0]
        self.rit_username = row[3]
        self.onfloor = row[1] == "TRUE"

def parse_csv(freshmen_csv):
    print("Parsing file...")
    try:
        with open(freshmen_csv, newline='') as freshmen_csv_file:
            return {freshman.rit_username: freshman for freshman in map(CSVFreshman, csv.reader(freshmen_csv_file))}
    except Exception as e:
        print("Failure while parsing CSV")
        raise e

@app.cli.command("sync-freshmen")
@click.argument("freshmen_csv")
def sync_freshmen(freshmen_csv):
    """
    Updates the freshmen entries in the DB to match the given CSV.
    """
    freshmen_in_csv = parse_csv(freshmen_csv)

    print("Syncing contents with the DB...")
    freshmen_in_db = {freshman.rit_username: freshman for freshman in Freshman.query.all()}

    for csv_freshman in freshmen_in_csv.values():
        if csv_freshman.rit_username not in freshmen_in_db:
            # This is a new freshman so add them to the DB
            freshmen_in_db[csv_freshman.rit_username] = Freshman(rit_username=csv_freshman.rit_username,
                                                                 name=csv_freshman.name, onfloor=csv_freshman.onfloor)
            db.session.add(freshmen_in_db[csv_freshman.rit_username])
        else:
            # This freshman is already in the DB so just update them
            freshmen_in_db[csv_freshman.rit_username].onfloor = csv_freshman.onfloor
            freshmen_in_db[csv_freshman.rit_username].name = csv_freshman.name

    # Update all freshmen entries that represent people who are no longer freshmen
    for freshman in filter(lambda freshman: freshman.rit_username not in freshmen_in_csv, freshmen_in_db.values()):
        freshman.onfloor = False

    # Update the freshmen signatures of each open or future packet
    for packet in Packet.query.filter(Packet.end > datetime.now()).all():
        # Handle the freshmen that are no longer onfloor
        for fresh_sig in filter(lambda fresh_sig: not fresh_sig.freshman.onfloor, packet.fresh_signatures):
            FreshSignature.query.filter_by(packet_id=fresh_sig.packet_id,
                                           freshman_username=fresh_sig.freshman_username).delete()

        # Add any new onfloor freshmen
        # pylint: disable=cell-var-from-loop
        current_fresh_sigs = set(map(lambda fresh_sig: fresh_sig.freshman_username, packet.fresh_signatures))
        for csv_freshman in filter(lambda csv_freshman: csv_freshman.rit_username not in current_fresh_sigs and
                                                        csv_freshman.onfloor and
                                                        csv_freshman.rit_username != packet.freshman_username,
                                   freshmen_in_csv.values()):
            db.session.add(FreshSignature(packet=packet, freshman=freshmen_in_db[csv_freshman.rit_username]))

    db.session.commit()
    print("Done!")

@app.cli.command("create-packets")
@click.argument("freshmen_csv")
def create_packets(freshmen_csv):
    """
    Creates a new packet season for each of the freshmen in the given CSV.
    """
    print("WARNING: The 'sync-freshmen' command must be run first to ensure that the state of floor is up to date.")
    if input("Continue? (y/N): ").lower() != "y":
        return

    # Collect the necessary data
    base_date = None
    while base_date is None:
        try:
            date_str = input("Input the first day of packet season (format: MM/DD/YYYY): ")
            base_date = datetime.strptime(date_str, "%m/%d/%Y").date()
        except ValueError:
            pass

    start = datetime.combine(base_date, packet_start_time)
    end = datetime.combine(base_date, packet_end_time) + timedelta(days=14)

    print("Fetching data from LDAP...")
    eboard = set(member.uid for member in ldap_get_eboard())
    onfloor = set(member.uid for member in ldap_get_live_onfloor())
    all_upper = eboard.union(onfloor)

    # Create the new packets and the signatures for each freshman in the given CSV
    freshmen_in_csv = parse_csv(freshmen_csv)
    print("Creating DB entries...")
    for freshman in Freshman.query.filter(Freshman.rit_username.in_(freshmen_in_csv)).all():
        packet = Packet(freshman=freshman, start=start, end=end)
        db.session.add(packet)

        for member in all_upper:
            db.session.add(UpperSignature(packet=packet, member=member, eboard=member in eboard))

        for onfloor_freshman in Freshman.query.filter_by(onfloor=True).filter(Freshman.rit_username !=
                                                                              freshman.rit_username).all():
            db.session.add(FreshSignature(packet=packet, freshman=onfloor_freshman))

    db.session.commit()
    print("Done!")

@app.cli.command("ldap-sync")
def ldap_sync():
    """
    Updates the upper and misc sigs in the DB to match ldap.
    """
    print("Fetching data from LDAP...")
    eboard = set(member.uid for member in ldap_get_eboard())
    onfloor = set(member.uid for member in ldap_get_live_onfloor())
    all_upper = eboard.union(onfloor)

    print("Applying updates to the DB...")
    for packet in Packet.query.filter(Packet.end > datetime.now()).all():
        # Update the eboard state of all UpperSignatures
        for sig in packet.upper_signatures:
            sig.eboard = sig.member in eboard

        # Migrate UpperSignatures that are from accounts that are not eboard or onfloor anymore
        for sig in filter(lambda sig: sig.member not in all_upper, packet.upper_signatures):
            UpperSignature.query.filter_by(packet_id=packet.id, member=sig.member).delete()
            if sig.signed:
                db.session.add(MiscSignature(packet=packet, member=sig.member))

        # Migrate MiscSignatures that are from accounts that are now eboard or onfloor members
        for sig in filter(lambda sig: sig.member in all_upper, packet.misc_signatures):
            MiscSignature.query.filter_by(packet_id=packet.id, member=sig.member).delete()
            db.session.add(UpperSignature(packet=packet, member=sig.member, eboard=sig.member in eboard, signed=True))

        # Create UpperSignatures for any new eboard or onfloor members
        # pylint: disable=cell-var-from-loop
        upper_sigs = set(map(lambda sig: sig.member, packet.upper_signatures))
        for member in filter(lambda member: member not in upper_sigs, all_upper):
            db.session.add(UpperSignature(packet=packet, member=member, eboard=member in eboard))

    db.session.commit()
    print("Done!")

@app.cli.command("fetch-results")
def fetch_results():
    """
    Fetches and prints the results from a given packet season.
    """
    end_date = None
    while end_date is None:
        try:
            date_str = input("Enter the last day of the packet season you'd like to retrieve results from " +
                             "(format: MM/DD/YYYY): ")
            end_date = datetime.strptime(date_str, "%m/%d/%Y").date()
        except ValueError:
            pass

    end_date = datetime.combine(end_date, packet_end_time)

    for packet in Packet.query.filter_by(end=end_date).all():
        print()

        print("{} ({}):".format(packet.freshman.name, packet.freshman.rit_username))

        received = packet.signatures_received()
        required = packet.signatures_required()

        print("\tUpperclassmen score: {:0.2f}%".format(received.member_total / required.member_total * 100))
        print("\tTotal score: {:0.2f}%".format(received.total / required.total * 100))
        print()

        print("\tEboard: {}/{}".format(received.eboard, required.eboard))
        print("\tUpperclassmen: {}/{}".format(received.upper, required.upper))
        print("\tFreshmen: {}/{}".format(received.fresh, required.fresh))
        print("\tMiscellaneous: {}/{}".format(received.misc, required.misc))
        print()

        print("\tTotal missed:", required.total - received.total)
