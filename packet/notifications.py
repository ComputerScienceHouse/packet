import onesignal

from packet import app, onesignal_client
from packet.models import NotificationSubscription

post_body = {
    "contents": {"en": "Default message"},
    "headings": {"en": "Default Title"},
    "chrome_web_icon": app.config["PROTOCOL"] + app.config["SERVER_NAME"] + "/static/android-chrome-512x512.png",
    "chrome_web_badge": app.config["PROTOCOL"] + app.config["SERVER_NAME"] + "/static/android-chrome-512x512.png",
    "url": app.config["PROTOCOL"] + app.config["SERVER_NAME"]
}


def packet_signed_notification(packet, signer):
    subscriptions = NotificationSubscription.query.filter_by(freshman_username=packet.freshman_username)
    if subscriptions:
        tokens = list(map(lambda subscription: subscription.token, subscriptions))

        notification = onesignal.Notification(post_body=post_body)
        notification.post_body["contents"]["en"] = signer + ' signed your packet! Congrats or I\'m Sorry'
        notification.post_body["headings"]["en"] = 'New Packet Signature!'
        notification.post_body["chrome_web_icon"] = 'https://profiles.csh.rit.edu/image/' + signer
        notification.post_body["include_player_ids"] = tokens

        onesignal_response = onesignal_client.send_notification(notification)
        if onesignal_response.status_code == 200:
            app.logger.info("The notification ({}) sent out successfully".format(notification.post_body))


def packet_100_percent_notification(packet):
    subscriptions = NotificationSubscription.query.all()
    if subscriptions:
        tokens = list(map(lambda subscription: subscription.token, subscriptions))

        notification = onesignal.Notification(post_body=post_body)
        notification.post_body["contents"]["en"] = packet.freshman.name + ' got 💯 on packet!'
        notification.post_body["headings"]["en"] = 'New 100% on Packet!'
        # TODO: Issue #156
        notification.post_body["chrome_web_icon"] = 'https://profiles.csh.rit.edu/image/' + packet.freshman_username
        notification.post_body["include_player_ids"] = tokens

        onesignal_response = onesignal_client.send_notification(notification)
        if onesignal_response.status_code == 200:
            app.logger.info("The notification ({}) sent out successfully".format(notification.post_body))
