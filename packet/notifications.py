import requests
from firebase_admin import messaging

from packet import app


def subscribeToken(token):
    messaging.subscribe_to_topic(token, '100percent')


def packet_signed_notification(token, signer):
    message = messaging.Message(
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                token=token,
                title='New Packet Signature!',
                body=signer + ' signed your packet! Congrats or I\'m Sorry',
                icon='https://profiles.csh.rit.edu/image/' + signer,
            ),
        )
    )
    response = messaging.send(message)
    print('Successfully sent message:', response)


def packet_100_percent_notification(token, freshman):
    message = messaging.Message(
        webpush=messaging.WebpushConfig(
            notification=messaging.WebpushNotification(
                token=token,
                title='New 100% on Packet!',
                body=freshman.name + ' got on packet!',
                icon='https://profiles.csh.rit.edu/image/' + freshman.rit_username,
            ),
        )
    )
    response = messaging.send(message)
    print('Successfully sent message:', response)


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
