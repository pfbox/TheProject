from .utclasses import *

from django.core.mail import send_mail, send_mass_mail,EmailMessage
from django.conf import settings
from asgiref.sync import sync_to_async

def send_class_email():
    user=User.objects.get(username='admin')
    send_mail(user.email, user.username, settings.EMAIL_HOST_USER, ['pavel.fedoryaka@gmail.com'])
