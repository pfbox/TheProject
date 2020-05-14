from .models import Attributes
import django.forms

class Attr():
    def __init__(self,attr):
        for i,v in attr.values:
            setattr(self,i,v)


