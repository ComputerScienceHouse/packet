"""
Defines command-line utilities for use with the app
"""

from secrets import token_hex

from . import app, db
from .models import Freshman, Packet, UpperSignature

@app.cli.command("create-secret")
def create_secret():
    """
    Generates a securely random token. Useful for creating a value for use in the "SECRET_KEY" config setting.
    """
    print("Here's your random secure token:")
    print(token_hex())

@app.cli.command("create-packet")
def create_packet():
    """
    Example/test code for adding a new packet to the database.
    """
    print("Generating new rows...")

    freshman = Freshman(rit_username="bob1234", name="Bob Freshy", onfloor=True)
    db.session.add(freshman)

    packet = Packet(freshman=freshman)
    db.session.add(packet)

    db.session.add(UpperSignature(packet=packet, member="somehuman"))
    db.session.add(UpperSignature(packet=packet, member="reeehuman", eboard=True))

    db.session.commit()

    print("Done!")
