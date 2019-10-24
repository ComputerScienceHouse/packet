from flask import render_template
from flask_mail import Mail, Message

from packet import app

mail = Mail(app)


def send_start_packet_mail(packet):
    if app.config['MAIL_PROD']:
        recipients = ['<' + packet.freshman.rit_username + '@rit.edu>']
        msg = Message(subject='CSH Packet Starts ' + packet.start.strftime('%A, %B %-d'),
                      sender=app.config.get('MAIL_USERNAME'),
                      recipients=recipients)

        template = 'mail/packet_start'
        msg.body = render_template(template + '.txt', packet=packet)
        msg.html = render_template(template + '.html', packet=packet)
        app.logger.info('Sending mail to ' + recipients[0])
        mail.send(msg)


def send_report_mail(form_results, reporter):
    if app.config['MAIL_PROD']:
        recipients = ['<evals@csh.rit.edu>']
        msg = Message(subject='Packet Report',
                      sender=app.config.get('MAIL_USERNAME'),
                      recipients=recipients)

        person = form_results['person']
        report = form_results['report']

        template = 'mail/report'
        msg.body = render_template(template + '.txt', person=person, report=report, reporter=reporter)
        msg.html = render_template(template + '.html', person=person, report=report, reporter=reporter)
        app.logger.info('Sending mail to ' + recipients[0])
        mail.send(msg)
