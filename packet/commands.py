"""
Defines command-line utilities for use with the app
"""

from secrets import token_hex
from datetime import datetime, time, timedelta
import click

from . import app, db
from .models import Freshman, Packet, UpperSignature, FreshSignature
from .ldap import ldap_get_eboard, ldap_get_live_onfloor

@app.cli.command("create-secret")
def create_secret():
    """
    Generates a securely random token. Useful for creating a value for use in the "SECRET_KEY" config setting.
    """
    print("Here's your random secure token:")
    print(token_hex())

def get_member_username(member):
    return member.uid

@app.cli.command("create-packets")
@click.argument("freshmen_csv")
def create_packets(freshmen_csv):
    """
    Creates all database entries needed to start a new packet season.
    """
    print("Welcome to the packet season creation CLI", end="\n\n")

    rawDate = None
    while rawDate is None:
        try:
            dateStr = input("Input the first day of packet season (format: MM/DD/YYYY): ")
            rawDate = datetime.strptime(dateStr, "%m/%d/%Y").date()
        except ValueError:
            pass

    start = datetime.combine(rawDate, time(hour=19))
    end = datetime.combine(rawDate, time(hour=23, minute=59)) + timedelta(days=14)
    print("start = {}; end = {}".format(start, end), end="\n\n")

    eboard = list(map(get_member_username, ldap_get_eboard()))
    onfloor = list(map(get_member_username, ldap_get_live_onfloor()))
    print("eboard members = {}".format(eboard))
    print("onfloor members = {}".format(onfloor), end="\n\n")

    print("Parsing freshmen csv...")
    allFreshmen = {}
    onfloorFreshmen = {}

    try:
        with open(freshmen_csv) as freshmenFile:
            for row in freshmenFile:
                row = row.strip().split(",")

                allFreshmen[row[3]] = row[0]

                if row[1] == "TRUE":
                    onfloorFreshmen[row[3]] = row[0]

    except Exception as e:
        print("Things broke")
        raise e

    print("All freshmen = {}".format(allFreshmen))
    print("On floor freshmen = {}".format(onfloorFreshmen), end="\n\n")

    if input("Data ready; create the season? (Y/n): ").lower() != "y":
        return

    # Go ahead and create all Freshman entries now so FreshSignatures can be created iteratively
    freshmen = {}
    for ritUsername, name in allFreshmen.items():
        freshmen[ritUsername] = Freshman(rit_username=ritUsername, name=name, onfloor=ritUsername in onfloorFreshmen)
        db.session.add(freshmen[ritUsername])

    # Create the new packets and the signatures
    for ritUsername, name in allFreshmen.items():
        packet = Packet(freshman=freshmen[ritUsername], start=start, end=end)
        db.session.add(packet)

        for username in eboard:
            db.session.add(UpperSignature(packet=packet, member=username, eboard=True))

        for username in onfloor:
            db.session.add(UpperSignature(packet=packet, member=username))

        for otherRitUsername in onfloorFreshmen.keys():
            if otherRitUsername != ritUsername:
                db.session.add(FreshSignature(packet=packet, freshman=freshmen[otherRitUsername]))

    db.session.commit()
    print("Done!")
