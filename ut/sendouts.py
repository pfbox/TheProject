import smtplib
from ut.utclasses import *

def send_emails(to=[],subject='no subject',body='no body'):
    gmail_user = 'myultimatetracker@gmail.com'
    gmail_password = 'jvnauxaxbdrrqqay'

    sent_from = gmail_user
    #subject = 'OMG Super Important Message'
    #body = "Hey, what's up?\n\n- You"
    email_text = """\
    From: %s
    To: %s
    Subject: %s
    %s
    """ % (sent_from, ", ".join(to), subject, body)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(gmail_user, gmail_password)
    server.sendmail(sent_from, to, email_text)
    server.close()

def send_communication(comm_id):
    c = SendOuts.objects.get(pk=comm_id)
    query=c.Query
    emailfield=c.EmailField
    emailgrouping=c.EmailField
    template='template'


from django.template import engines
django_engine=engines['django']
template = django_engine.from_string("Hello {{ name }}!")

from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

subject = 'Subject'
html_message = render_to_string('mail_template.html', {'context': 'values'})
plain_message = strip_tags(html_message)
from_email = 'From <from@example.com>'
to = 'to@example.com'

mail.send_mail(subject, plain_message, from_email, [to], html_message=html_message)