from typing import TypedDict, List, Union, cast

from flask import render_template
from flask_mail import Mail, Message

from packet import app
from packet.models import Packet

mail: Mail = Mail(app)


class ReportForm(TypedDict):
    """
    A form for submitting a report.

    Attributes:
        person (str): The name of the person being reported.
        report (str): The content of the report.
    """

    person: str
    report: str


def send_start_packet_mail(packet: Packet) -> None:
    """
    Send an email notification when a CSH packet starts.

    Args:
        packet (Packet): The packet that is starting.
    """

    if not app.config['MAIL_PROD']:
        return

    recipients: list[str] = ['<' + str(packet.freshman.rit_username) + '@rit.edu>']

    msg: Message = Message(
        subject='CSH Packet Starts ' + packet.start.strftime('%A, %B %-d'),
        sender=app.config.get('MAIL_USERNAME'),
        recipients=cast(List[Union[str, tuple[str, str]]], recipients),
    )

    template: str = 'mail/packet_start'

    msg.body = render_template(template + '.txt', packet=packet)
    msg.html = render_template(template + '.html', packet=packet)

    app.logger.info('Sending mail to ' + recipients[0])
    mail.send(msg)


def send_report_mail(form_results: ReportForm, reporter: str) -> None:
    """
    Send an email notification when a report is submitted.

    Args:
        form_results (ReportForm): The results of the report form.
        reporter (str): The name of the person submitting the report.
    """

    if not app.config['MAIL_PROD']:
        return

    recipients: list[str] = ['<evals@csh.rit.edu>']
    msg: Message = Message(
        subject='Packet Report',
        sender=app.config.get('MAIL_USERNAME'),
        recipients=cast(List[Union[str, tuple[str, str]]], recipients),
    )

    person = form_results['person']
    report = form_results['report']

    template = 'mail/report'
    msg.body = render_template(template + '.txt', person=person, report=report, reporter=reporter)
    msg.html = render_template(template + '.html', person=person, report=report, reporter=reporter)
    app.logger.info('Sending mail to ' + recipients[0])
    mail.send(msg)
