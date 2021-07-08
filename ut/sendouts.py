from .utclasses import *

from django.core.mail import send_mail, send_mass_mail,EmailMessage
from django.conf import settings
from asgiref.sync import sync_to_async
from django.template import Template, Context

async def get_email_template(id):
    res = await sync_to_async(list)(EmailTemplates.objects.get(pk=id))
    return res

def send_class_email(Class_id,email_field,type='mass',email_template_id=None,filter={},static={},user=None):
    et = get_email_template(email_template_id)
    email_body=et.Template
    email_subject=et.SubjectTemplate
    sql=create_rawquery_sql(Class_id=Class_id,filter=filter,user=user)
    df_emails=pd.read_sql(sql,connections['readonly'])
    if type=='one':
        send_mail(email_subject,email_body,settings.EMAIL_HOST_USER,list(df_emails[email_field]))
    else:
        print ('im here')
        messages=[]
        for i,r in df_emails.iterrows():
            print(i, r)
            m=(email_subject,email_body,settings.EMAIL_HOST_USER,[r[email_field]])
            messages.append(m)
        send_mass_mail(messages)



def send_report_email(Report_id,email_field,email_subject='',email_body='',static={}):
    rep=get_report_df(Report_id)
    df_emails=rep['df']
    messages = []
    for i, r in df_emails.drop_duplicates(email_field).iterrows():
        body_template = Template(email_body)
        subject_template = Template(email_subject)
        context = Context({'Report':df_emails[df_emails[email_field]==r[email_field]].to_dict('records'),
                           'FirstRecord':r[email_field],
                           'FullReport':df_emails.to_dict('records')
                           }
                          )
        body=body_template.render(context)
        subject=subject_template.render(context)
        m = (subject, body, settings.EMAIL_HOST_USER, [r[email_field]])
        messages.append(m)
        break
    send_mass_mail(messages)


