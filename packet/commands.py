"""
Defines command-line utilities for use with the app
"""

from secrets import token_hex

from . import app

@app.cli.command("create-secret")
def create_secret():
    """
    Generates a securely random token. Useful for creating a value for use in the "SECRET_KEY" config setting.
    """
    print("Here's your random secure token:")
    print(token_hex())
