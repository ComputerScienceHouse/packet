import os

import firebase_admin
import requests
from firebase_admin import credentials, messaging

from packet import app

if not len(firebase_admin._apps):
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, 'serviceAccountKey.json')
    cred = credentials.Certificate(filename)
    default_app = firebase_admin.initialize_app(cred)


def subscribeToken(token):
    messaging.subscribe_to_topic(token, '100percent')


def packet_signed_notification(token, signer):
    message = messaging.Message(
        token=token,
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title='New Packet Signature!',
                body=signer + ' signed your packet! Congrats or I\'m Sorry',
                icon='https://profiles.csh.rit.edu/image/' + signer,
            ),
        )
    )
    response = messaging.send(message)
    app.logger.info("The notification ({}) sent out successfully".format(response))


def packet_100_percent_notification(token, freshman):
    message = messaging.Message(
        token=token,
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                title='New 100% on Packet!',
                body=freshman.name + ' got on packet!',
                icon='https://profiles.csh.rit.edu/image/' + freshman.rit_username,
            ),
        )
    )
    response = messaging.send(message)
    app.logger.info("The notification ({}) sent out successfully".format(response))


def notify_slack(name: str):
    """
    Sends a congratulate on sight decree to Slack
    """
    if app.config["SLACK_WEBHOOK_URL"] is None:
        app.logger.warn("SLACK_WEBHOOK_URL not configured, not sending message to slack.")
        return

    msg = f':pizza-party: {name} got :100: on packet! :pizza-party:'
    requests.put(app.config["SLACK_WEBHOOK_URL"], json={'text': msg})
    app.logger.info("Posted 100% notification to slack for " + name)
