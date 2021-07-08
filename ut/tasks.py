from .utclasses import *

from django.core.mail import send_mail, send_mass_mail,EmailMessage
from django.conf import settings
from django.template import Template, Context
from django.utils.html import strip_tags
from django.core.mail import get_connection, EmailMultiAlternatives

def send_class_email():
    user=User.objects.get(username='admin')
    send_mail(user.email, user.username, settings.EMAIL_HOST_USER, ['pavel.fedoryaka@gmail.com'])

def send_report_email(Report_id,email_field,email_template_id,pk=None,changes={},filter={}):
    if pk:
        filter['id']=pk
    rep=get_report_df(Report_id,filter)
    df_emails=rep['df']
    et=EmailTemplates.objects.get(pk=email_template_id)
    email_body=et.Template
    email_subject=et.SubjectTemplate
    messages = []
    for i, r in df_emails.drop_duplicates(email_field).iterrows():
        body_template = Template(email_body)
        subject_template = Template(email_subject)
        cdict={ i.replace(' ','_'):v for i,v in r.items()}
        cdict['changes']=changes
        cdict['pk']=pk
        context = Context(cdict)
        body_html=body_template.render(context)
        body_plain=strip_tags(body_html)
        subject=subject_template.render(context)
        email = EmailMultiAlternatives(subject, body_plain, settings.EMAIL_HOST_USER, [r[email_field]])
        email.attach_alternative(body_html,'text/html')
        messages.append(email)
    return get_connection().send_messages(messages)
