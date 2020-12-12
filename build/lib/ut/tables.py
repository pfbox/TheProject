from .models import *
import django_tables2 as tables

from django_tables2 import A

class AttributeTable(tables.Table):
    h_link = tables.LinkColumn('ut:edit_attribute', text='Edit', args=[A('pk'),], attrs={'a':{'class':'btn'}}, orderable=False)
    class Meta:
        model=Attributes
        template_name = "django_tables2/bootstrap4.html"

class ClassesTable(tables.Table):
    Edit = tables.LinkColumn('ut:edit_class', text='Edit', args=[A('pk')], orderable=False)
    Attributes = tables.LinkColumn('ut:attributes_view', text='View Attributes', args=[A('pk')], orderable=False)
    Instances = tables.LinkColumn ('ut:instances', text='View Instances', args=[A('pk')], orderable=False)
    Templates = tables.LinkColumn ('ut:change_formtemplate', text='View Template', args=[A('pk')], orderable=False)
    class Meta:
        model=Classes
        template_name = "django_tables2/bootstrap4.html"

class ProjectsTable(tables.Table):
    Edit = tables.LinkColumn('ut:edit_project', text='Edit', args=[A('pk')], orderable=False)
    class Meta:
        model=Projects
        template_name = "django_tables2/bootstrap4.html"

class ReportsTable(tables.Table):
    Edit = tables.LinkColumn('ut:edit_report', text='Edit', args=[A('pk')], orderable=False)
    class Meta:
        model=Reports
        template_name = "django_tables2/bootstrap4.html"

def get_tablelayout(Class_id,field='TableLayout'):
    try:
        res=Layouts.objects.get(Class_id=Class_id).__dict__[field]
    except Layouts.DoesNotExist:
        res={'settings':{},'layout':[{'name':'Code','width':50,'visible':True}]}
        a=Layouts(Class_id=Class_id,TableLayout=json.dumps(res),ShortLayout=json.dumps(res))
        a.save()
    return res


class ReportTable(tables.Table):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        #template_name="django_tables2/semantic.html"
        #attrs = {"class": "table table-hover table-striped table-sm table-bordered table-responsive"}
        attrs = {"class": "table table-hover table-striped table-sm table-responsive"}
        fields=()

from string import Template
class mytable(tables.Table):
    def __init__(self,Class_id=0,style='TableLayout',*args,**kwargs):
        self.Class_id=Class_id
        self.Style=style
        self.layout=get_tablelayout(self.Class_id,style)
        a=Template("""<a href="{% url "ut:view_instance" $classid record.pk %}"><i class="far fa-eye"></i></a>
             <a href="{% url "ut:edit_instance" $classid record.pk %}"><i class="far fa-edit"></i></a>
             <a onclick="return confirm('Are you sure you want to delete {{record.Code}} code?')" href="{% url "ut:delete_instance" $classid record.pk %}"><i class="far fa-trash-alt"></i></a>  
          """).substitute(classid=Class_id)
        t_link = tables.TemplateColumn(a, attrs={'th':{'align':'right'}},orderable=False)
#        existing_columns = [f.name for f in Instances._meta.get_fields()]
        tl = self.layout
        try:
            atts = json.loads(tl)['layout']
        except:
            atts = [{'name':'Code','width':50}]
        extra_columns = [(f['name'], tables.Column(attrs={'th': {'width': f['width']}})) for f in atts] + [
            ('Action', t_link)]  # +[('Edit2',h_link)]
        kwargs['extra_columns']=extra_columns
        super().__init__(*args, **kwargs)
#        self.Meta.fields=fields
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        #template_name="django_tables2/semantic.html"
        model=Instances
        #attrs = {"class": "table table-hover table-striped table-sm table-bordered table-responsive"}
        attrs = {"class": "table table-hover table-striped table-sm table-responsive"}
        fields=()
