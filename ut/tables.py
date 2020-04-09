from .models import *
import django_tables2 as tables

from django_tables2 import A

class AttributeTable(tables.Table):
    h_link = tables.LinkColumn('edit_attribute', text='Edit', args=[A('pk'),], attrs={'a':{'class':'btn'}}, orderable=False)
    class Meta:
        model=Attributes
        template_name = "django_tables2/bootstrap4.html"

class ClassesTable(tables.Table):
    Edit = tables.LinkColumn('edit_class', text='Edit', args=[A('pk')], orderable=False)
    Attributes = tables.LinkColumn('attributes_view', text='View Attributes', args=[A('pk')], orderable=False)
    Instances = tables.LinkColumn ('instances', text='View Instances', args=[A('pk')], orderable=False)
    Templates = tables.LinkColumn ('change_formtemplate', text='View Template', args=[A('pk')], orderable=False)
    class Meta:
        model=Classes
        template_name = "django_tables2/bootstrap4.html"

