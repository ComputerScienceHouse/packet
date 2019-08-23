import onesignal

from packet import app, intro_onesignal_client, csh_onesignal_client
from packet.models import NotificationSubscription

post_body = {
    "contents": {"en": "Default message"},
    "headings": {"en": "Default Title"},
    "chrome_web_icon": app.config["PROTOCOL"] + app.config["SERVER_NAME"] + "/static/android-chrome-512x512.png",
    "chrome_web_badge": app.config["PROTOCOL"] + app.config["SERVER_NAME"] + "/static/android-chrome-512x512.png",
    "url": app.config["PROTOCOL"] + app.config["SERVER_NAME"]
}


def send_notification(notification_body, subscriptions, client):
    tokens = list(map(lambda subscription: subscription.token, subscriptions))
    if tokens:
        notification = onesignal.Notification(post_body=notification_body)
        notification.post_body["include_player_ids"] = tokens
        onesignal_response = client.send_notification(notification)
        if onesignal_response.status_code == 200:
            app.logger.info("The notification ({}) sent out successfully".format(notification.post_body))
        else:
            app.logger.warn("The notification ({}) was unsuccessful".format(notification.post_body))


def packet_signed_notification(packet, signer):
    subscriptions = NotificationSubscription.query.filter_by(freshman_username=packet.freshman_username)
    if subscriptions:
        notification_body = post_body
        notification_body["contents"]["en"] = signer + " signed your packet! Congrats or I'm Sorry"
        notification_body["headings"]["en"] = "New Packet Signature!"
        notification_body["chrome_web_icon"] = "https://profiles.csh.rit.edu/image/" + signer
        notification_body["url"] = app.config["PROTOCOL"] + app.config["PACKET_INTRO"]

        send_notification(notification_body, subscriptions, intro_onesignal_client)


def packet_100_percent_notification(packet):
    member_subscriptions = NotificationSubscription.query.filter(NotificationSubscription.member.isnot(None))
    intro_subscriptions = NotificationSubscription.query.filter(NotificationSubscription.freshman_username.isnot(None))
    if member_subscriptions or intro_subscriptions:
        notification_body = post_body
        notification_body["contents"]["en"] = packet.freshman.name + " got 💯 on packet!"
        notification_body["headings"]["en"] = "New 100% on Packet!"
        # TODO: Issue #156
        notification_body["chrome_web_icon"] = "https://profiles.csh.rit.edu/image/" + packet.freshman_username

        send_notification(notification_body, member_subscriptions, csh_onesignal_client)
        send_notification(notification_body, intro_subscriptions, intro_onesignal_client)


def packet_starting_notification(packet):
    subscriptions = NotificationSubscription.query.filter_by(freshman_username=packet.freshman_username)
    if subscriptions:
        notification_body = post_body
        notification_body["contents"]["en"] = "Log into your packet, and get started meeting people!"
        notification_body["headings"]["en"] = "Your packet has begun!"
        notification_body["url"] = app.config["PROTOCOL"] + app.config["PACKET_INTRO"]
        notification_body["send_after"] = packet.start.strftime("%Y-%m-%d %H:%M:%S")

        send_notification(notification_body, subscriptions, intro_onesignal_client)


def packets_starting_notification(start_date):
    member_subscriptions = NotificationSubscription.query.filter(NotificationSubscription.member.isnot(None))
    if member_subscriptions:
        notification_body = post_body
        notification_body["contents"]["en"] = "New packets have started, visit packet to see them!"
        notification_body["headings"]["en"] = "Packets Start Today!"
        notification_body["send_after"] = start_date.strftime("%Y-%m-%d %H:%M:%S")

        send_notification(notification_body, member_subscriptions, csh_onesignal_client)
