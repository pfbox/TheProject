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
    for i, r in df_emails.iterrows(): # No need for drop duplicates
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


def save_availability(availability,Game_id,TeamPlayer_id):
    Class_id = 35
    qs_team = Values.objects.filter(Attribute_id=162, instance_value_id=Game_id)
    qs_player = Values.objects.filter(Attribute_id=163, instance_value_id=TeamPlayer_id).values_list('Instance_id',
                                                                                                     flat=True)
    instance_exists = qs_team.filter(Instance_id__in=qs_player)

    with transaction.atomic():
        if len(instance_exists) == 0:
            Instance_id = 0
            code = get_next_counter(Class_id)
        else:
            Instance = instance_exists[0].Instance
            Instance_id = Instance.id
            code = Instance.Code
        instance = {'Game': Game_id, 'Team': 83, 'Player': TeamPlayer_id, 'Availability': availability, 'Code': code}
        save_instance_byname(safe=True, Class_id=Class_id, Instance_id=Instance_id, instance=instance,
                             passed_by_name=False)