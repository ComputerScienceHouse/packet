from flask import render_template
from flask_mail import Mail, Message

from packet import app

mail = Mail(app)


def send_mail(packet):
    if app.config['MAIL_PROD']:
        recipients = ["<" + packet.freshman.rit_username + "@rit.edu>"]
        msg = Message(subject="CSH Packet Starts " + packet.start.strftime('%D'),
                      sender=app.config.get("MAIL_USERNAME"),
                      recipients=recipients)

        template = 'mail/packet_start'
        msg.body = render_template(template + '.txt', packet=packet)
        msg.html = render_template(template + '.html', packet=packet)
        mail.send(msg)
