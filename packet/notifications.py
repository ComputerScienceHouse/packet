from datetime import datetime
from typing import Any, Callable, TypeVar, cast

import onesignal

from packet import app, intro_onesignal_client, csh_onesignal_client
from packet.models import NotificationSubscription, Packet

post_body = {
    'contents': {'en': 'Default message'},
    'headings': {'en': 'Default Title'},
    'chrome_web_icon': app.config['PROTOCOL'] + app.config['SERVER_NAME'] + '/static/android-chrome-512x512.png',
    'chrome_web_badge': app.config['PROTOCOL'] + app.config['SERVER_NAME'] + '/static/android-chrome-512x512.png',
    'url': app.config['PROTOCOL'] + app.config['SERVER_NAME'],
}

WrappedFunc = TypeVar('WrappedFunc', bound=Callable)


def require_onesignal_intro(func: WrappedFunc) -> WrappedFunc:
    """
    Decorator to require the OneSignal intro client to be available.

    Args:
        func (WrappedFunc): The function to wrap.

    Returns:
        WrappedFunc: The wrapped function.
    """

    def require_onesignal_intro_wrapper(*args: list, **kwargs: dict) -> Any:
        """
        Wrapper function to check for the OneSignal intro client.

        Args:
            *args: Positional arguments to pass to the wrapped function.
            **kwargs: Keyword arguments to pass to the wrapped function.

        Returns:
            Any: The result of the wrapped function or None if the client is unavailable.
        """

        if intro_onesignal_client:
            return func(*args, **kwargs)

        return None

    return cast(WrappedFunc, require_onesignal_intro_wrapper)


def require_onesignal_csh(func: WrappedFunc) -> WrappedFunc:
    """
    Decorator to require the OneSignal CSH client to be available.

    Args:
        func (WrappedFunc): The function to wrap.

    Returns:
        WrappedFunc: The wrapped function.
    """

    def require_onesignal_csh_wrapper(*args: list, **kwargs: dict) -> Any:
        """
        Wrapper function to check for the OneSignal CSH client.

        Args:
            *args: Positional arguments to pass to the wrapped function.
            **kwargs: Keyword arguments to pass to the wrapped function.

        Returns:
            Any: The result of the wrapped function or None if the client is unavailable.
        """

        if csh_onesignal_client:
            return func(*args, **kwargs)

        return None

    return cast(WrappedFunc, require_onesignal_csh_wrapper)


def send_notification(notification_body: dict, subscriptions: list, client: onesignal.Client) -> None:
    """
    Send a notification to a list of OneSignal subscriptions.

    Args:
        notification_body (dict): The body of the notification to send.
        subscriptions (list): The list of subscriptions to send the notification to.
        client (onesignal.Client): The OneSignal client to use for sending the notification.

    Returns:
        None
    """

    tokens: list[str] = list(map(lambda subscription: subscription.token, subscriptions))

    if not tokens:
        return

    notification = onesignal.Notification(post_body=notification_body)
    notification.post_body['include_player_ids'] = tokens
    onesignal_response = client.send_notification(notification)

    if onesignal_response.status_code == 200:
        app.logger.info('The notification ({}) sent out successfully'.format(notification.post_body))
    else:
        app.logger.warn('The notification ({}) was unsuccessful'.format(notification.post_body))


@require_onesignal_intro
def packet_signed_notification(packet: Packet, signer: str) -> None:
    """
    Send a notification when a packet is signed.

    Args:
        packet (Packet): The packet that was signed.
        signer (str): The username of the person who signed the packet.
    """

    subscriptions = NotificationSubscription.query.filter_by(freshman_username=packet.freshman_username)

    if not subscriptions:
        return

    notification_body = post_body
    notification_body['contents']['en'] = signer + ' signed your packet!'
    notification_body['headings']['en'] = 'New Packet Signature!'
    notification_body['chrome_web_icon'] = 'https://profiles.csh.rit.edu/image/' + signer
    notification_body['url'] = app.config['PROTOCOL'] + app.config['PACKET_INTRO']

    send_notification(notification_body, subscriptions, intro_onesignal_client)


@require_onesignal_csh
@require_onesignal_intro
def packet_100_percent_notification(packet: Packet) -> None:
    """
    Send a notification when a packet is completed with 100%.

    Args:
        packet (Packet): The packet that was completed.
    """

    member_subscriptions = NotificationSubscription.query.filter(cast(Any, NotificationSubscription.member).isnot(None))

    intro_subscriptions = NotificationSubscription.query.filter(
        cast(Any, NotificationSubscription.freshman_username).isnot(None)
    )

    if member_subscriptions or intro_subscriptions:
        notification_body = post_body
        notification_body['contents']['en'] = packet.freshman.name + ' got 💯 on packet!'
        notification_body['headings']['en'] = 'New 100% on Packet!'
        # TODO: Issue #156
        notification_body['chrome_web_icon'] = 'https://profiles.csh.rit.edu/image/' + packet.freshman_username

        send_notification(notification_body, member_subscriptions, csh_onesignal_client)
        send_notification(notification_body, intro_subscriptions, intro_onesignal_client)


@require_onesignal_intro
def packet_starting_notification(packet: Packet) -> None:
    """
    Send a notification when a packet is starting.

    Args:
        packet (Packet): The packet that is starting.
    """

    subscriptions = NotificationSubscription.query.filter_by(freshman_username=packet.freshman_username)

    if not subscriptions:
        return

    notification_body = post_body
    notification_body['contents']['en'] = 'Log into your packet, and get started meeting people!'
    notification_body['headings']['en'] = 'Your packet has begun!'
    notification_body['url'] = app.config['PROTOCOL'] + app.config['PACKET_INTRO']
    notification_body['send_after'] = packet.start.strftime('%Y-%m-%d %H:%M:%S')

    send_notification(notification_body, subscriptions, intro_onesignal_client)


@require_onesignal_csh
def packets_starting_notification(start_date: datetime) -> None:
    """
    Send a notification when packets are starting.

    Args:
        start_date (datetime): The start date of the packets.
    """

    member_subscriptions = NotificationSubscription.query.filter(cast(Any, NotificationSubscription.member).isnot(None))

    if not member_subscriptions:
        return

    notification_body = post_body
    notification_body['contents']['en'] = 'New packets have started, visit packet to see them!'
    notification_body['headings']['en'] = 'Packets Start Today!'
    notification_body['send_after'] = start_date.strftime('%Y-%m-%d %H:%M:%S')

    send_notification(notification_body, member_subscriptions, csh_onesignal_client)
