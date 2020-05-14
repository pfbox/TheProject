from django.views.generic import UpdateView,CreateView,ListView
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse,reverse_lazy
from django.shortcuts import render
from .tables import *
from .forms import *
from django.template.context_processors import csrf
import numpy as np
from django_tables2 import SingleTableView
from .filters import ClassesFilter


from .utclasses import *
from django_tables2 import RequestConfig

def index(request):
    context={'table_list':am.to_dict('records')}
    context['classes']=Classes.objects.all()
    return render(request,'ut/index.html',context)

from django.forms import ModelForm

def table(request,tablename):
    tm=am[am.TableName==tablename].iloc[0].Table
    qs=tm.objects.all()
    class t (tables.Table):
        class Meta:
            model=tm
            sortable=True
    table = t(qs)
    a='''\
    class mform(ModelForm): #ModelForm example
        class Meta:
            model=tm
            fields=[f.name for f in tm._meta.fields]

    form=mform()
    '''
    context = {'tablename':tablename, 'table':  table , 'Class_id': 0}
    return render(request, 'ut/showtable.html', context)

def showclass(request,Class_id):
    classname=Classes.objects.get(pk=Class_id).Class
    table=Attributes.objects.filter(Class_id=Class_id)
    context = {'classname':classname,'table':table}
    return render(request, 'ut/showtable.html', context)

def edit_instance(request,Class_id,Instance_id):
    if request.method=='POST':
        if request.POST.get('cancel'):
            return HttpResponseRedirect(reverse('ut:instances', args=(Class_id,)))
        else:
            form=InstanceForm(request.POST,Class_id=Class_id,Instance_id=Instance_id)
            if form.is_valid():
                save_instance_byname(Class_id=Class_id,Instance_id=Instance_id,instance=form.cleaned_data,passed_by_name=False)
                return HttpResponseRedirect(reverse('ut:instances', args=(Class_id,)))
    form=InstanceForm(Class_id=Class_id,Instance_id=Instance_id)

    context={}
    for a1 in Attributes.objects.filter(Class_id=Class_id,DataType_id=10):
        refclass_id=a1.Ref_Class.id
        refattr = a1.Ref_Attribute.Attribute
        if Instance_id==0:
            filter={refattr:-1}
        else:
            filter = {refattr:Instance_id}

        qs = create_rawquery_from_attributes(refclass_id, filter=filter)
        table = mytable(Class_id=refclass_id,style='ShortLayout',data=qs)
        context['table'+str(a1.id)+'']=table
    context['form'] = form
    return render(request,'ut/edit_instance.html',context)

a='''\
    fl = Classes.objects.get(pk=Class_id).editlist

    if Instance_id==0:
        code=get_next_counter(Class_id) # need to do some counter
    else:
        code=Instances.objects.get(pk=Instance_id).Code
    context = {'Name': 'showemptyform', 'Instance_id':Instance_id,
               'Code':code,'Class_id':Class_id}
    context['col1']=get_column(Class_id,'Column1',Instance_id).to_dict('records')
    context['col2']=get_column(Class_id,'Column2',Instance_id).to_dict('records')

    return render(request, 'ut/emptyclass.html', context)

def save_instance(request,Class_id,Instance_id=0):
    #Class_id=Instances.objects.get(pk=Instance_id).Class.id
    ins={}
    if request.method == 'POST':
        for key,val in request.POST.items():
            ins[key]=val
        ins['Instance_id']=Instance_id
        save_instance_byid(Class_id,ins)
    return HttpResponseRedirect(reverse('instances', args=(Class_id,)))
'''


def classestree_view(request):
    return render(request, "ut/classestree.html", {'table': Classes.objects.all()})

def classes_view(request):
    table = ClassesTable(Classes.objects.all())
    RequestConfig(request, paginate={"per_page": 10}).configure(table)
    return render(request,'ut/classes.html',{'table':table})


def classes_view2(request):
    classes_list=Classes.objects.all()
    classes_filter=ClassesFilter(request.GET,queryset=classes_list)
    table = ClassesTable(classes_list)
    RequestConfig(request, paginate={"per_page": 20}).configure(table)
    return render(request,'ut/classes.html',{'filter':classes_filter,'table':table})

class insances_view():
    def __init__(self,Class_id,filter={}):
        super().__init__(self);
        self.Class_id=Class_id
        self.filter=filter
    def get(self,request,Class_id,SaveToExl):
        self.filter = {}
        for key,value in request.GET.items():
            if (value!='')&(key not in ['sort','page']):
                pass

def instances(request,Class_id,SaveToExl=False):
    filter = {}
    sort=None
    if request.method=='GET':
        if request.GET.get('sort'):
            sort=request.GET.get('sort')
        else:
            sort = request.GET.get('sortfield')
        for key, value in request.GET.items():
            if (value!='')&(key not in ['sort','page','submit','sortfield']):
                filter[key]=value
    filterform= FilterForm(Class_id=Class_id,filter=filter) #create_filter_set(Class_id,filter)

    qs=create_rawquery_from_attributes(Class_id,filter)
    if pd.isnull(sort):
        sort='Code'
    if SaveToExl:
        return export_instances_xls(request,qs)
    else:
        pass
    #h_link = tables.LinkColumn('ut:edit_instance', text=lambda x: x.Code, args=[A('Class_id'), A('pk')], orderable=False)

    table=mytable(Class_id=Class_id,style='TableLayout',data=qs)
    if not request.GET._mutable:
        request.GET._mutable = True
    request.GET['sort']=sort
    #print (request.GET)
    RequestConfig(request).configure(table)
#    table.order_by = sort
#    print ('sort=',sort)
    table.paginate(page=request.GET.get("page", 1), per_page=20)
    context = {'tablename':'Instances','Class_id':Class_id, 'table':table,'filterform':filterform,'sortfield':sort}
    return render(request, 'ut/showtable.html',  context)

def filters(request,Class_id):
    fl = fieldlist(Class_id)
    fl['ControlFilter'] = fl.id.apply(lambda x: create_filter(x))
    context = {'Name': 'ShowFilters', 'fieldlist': fl.to_dict('records'),'Class_id':Class_id}
    return render(request, 'ut/filters.html', context)

def attributes_view(request,Class_id):
    attlist=Attributes.objects.filter(Class_id=Class_id)
    table = AttributeTable(attlist)
    RequestConfig(request, paginate={"per_page": 20}).configure(table)
    return render(request,'ut/attributes.html',{'table':table,'Class_id':Class_id})


def edit_attribute(request,Attribute_id):
    at=Attributes.objects.get(pk=Attribute_id)
    form = AttributeForm(instance=at)
    return render(request,'ut/edit_attribute.html',{'form':form})

class AttributeCreateView(CreateView):
    model = Attributes
    template_name = 'ut/edit_attribute.html'
    form_class = AttributeForm

    def get_success_url(self):
        return reverse_lazy('ut:attributes_view', args = (self.Class_id,))

    def get_initial(self):
        initial = super().get_initial()
        self.Class_id = self.kwargs['Class_id']
        initial['Class']=self.model.objects.get(pk=self.Class_id)
        return initial

    def get_form_kwargs(self):
        kw=super(AttributeCreateView,self).get_form_kwargs()
        kw['initial']['Class_id']=self.Class_id
        return kw


class AttributeUpdateView(UpdateView):
    model = Attributes
    template_name = 'ut/edit_attribute.html'
    form_class = AttributeForm

    def get_success_url(self):
        return reverse_lazy('ut:attributes_view',args=(self.object.Class.id,))



class ClassesUpdateView(UpdateView):
    model = Classes
    template_name = 'ut\edit_attribute.html'
    form_class = ClassesForm

    def get_success_url(self):
        return reverse_lazy('ut:classes_view')

class ClassesCreateView(CreateView):
    model = Classes
    template_name = 'ut\edit_attribute.html'
    form_class = ClassesForm

    def get_success_url(self):
        return reverse_lazy('ut:classes_view')

a="""
def change_formtemplate(request,Class_id=0):
    if request.method=='POST':
        formlo={}
        formlo['Column1']=request.POST['column1']
        formlo['Column2']=request.POST['column2']
        lo=Layouts.objects.get(Class_id=Class_id)
        lo.FormLayout=json.dumps(formlo)
        lo.save()

    fl = Classes.objects.get(pk=Class_id).editlist
    if len(fl)>0:
        fl['Control']=fl.id.apply(lambda x: create_control(0,x))

    formlo=get_formlayout(Class_id)

    used=[]
    c1=get_column(Class_id,'Column1')
    c2=get_column(Class_id,'Column2')

    context={}
    context['Class_id']=Class_id
    if len(c1)>0:
        context['col1']=c1.to_dict('records')
        used=used+list(c1.id)
    if len(c2)>0:
        context['col2']=c2.to_dict('records')
        used=used+list(c2.id)
    if len(fl)>0:
        context['unused']=fl[~fl.id.isin(used)].to_dict('records')
        context['list1']=formlo['Column1']
        context['list2']=formlo['Column2']

    return render(request,'ut/formtemplate.html',context)
"""

import xlwt

from django.http import HttpResponse
from django.contrib.auth.models import User

import csv


def export_instances_csv(request,raw_qs):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Instances.csv"'
    writer = csv.writer(response)
    writer.writerow(list(raw_qs.columns))
    rows = raw_queryset_as_values_list(raw_qs)
    for row in rows:
        writer.writerow(row)
    return response

from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def export_instances_xls(request,raw_qs):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="instances.xlsx"'
    wb = Workbook()
    ws = wb.active
    ws.title='Instances'
    # Sheet header, first row
    ws.append(raw_qs.columns)
    rows=raw_queryset_as_values_list(raw_qs)
    for r in rows:
        ws.append(r)
    wb.save(response)
    return response

def export_instances_xls_2(request,raw_qs):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="instances.xlsx"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Instances')
    # Sheet header, first row
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = raw_qs.columns
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    rows = raw_queryset_as_values_list(raw_qs)
    for row in rows:
        row_num += 1
        for col_num in range(len(columns)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response

#from somewhere import handle_uploaded_file

def handle_uploaded_file(f,Class_id):
    ins=pd.read_excel(f).to_dict('records')
    for rec in ins:
        save_instance_byname(Class_id=Class_id,instance=rec)

def load_instances(request,Class_id=0):
    if request.method == 'POST':
        form = UploadInstances(request.POST, request.FILES)
        if form.is_valid() and request.FILES['file']:
            handle_uploaded_file(request.FILES['file'],Class_id)
            return HttpResponseRedirect(reverse('instances', args=(Class_id,)))
    else:
        form = UploadInstances()
    return render(request, 'ut/loadinstances.html', {'form': form,'Class_id':Class_id})

from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
class ProtectView(LoginRequiredMixin, View) :
    def get(self, request):
        return render(request, 'ut/index.html')


class FormTemplateView(View):
    template = 'ut/formtemplate.html'
    def get(self, request,Class_id):
        table=Classes.objects.get(pk=Class_id).editattributes
        context={}
        if Layouts.objects.filter(Class=Class_id).exists():
            context['layout']=Layouts.objects.get(Class=Class_id).FormLayout
        context['table']=table
        context['Class_id']=Class_id
        return render(request, self.template, context)

    def post(self, request,Class_id) :
        if request.POST:
            #layout=json.loads(request.POST['layout'])
            lo_to_save=request.POST['layout']
            if Layouts.objects.filter(Class=Class_id).exists():
                rec=Layouts.objects.get(Class=Class_id)
                rec.FormLayout=lo_to_save
            else:
                rec=Layouts(FormLayout=lo_to_save,Class=Class_id)
            rec.save()

        return HttpResponseRedirect(reverse('ut:change_formtemplate',kwargs={'Class_id':Class_id}))

class TableTemplateView(View):
    template = 'ut/tabletemplate.html'
    def get(self, request,Class_id):
        table=Classes.objects.get(pk=Class_id).editattributes
        context={}
        if Layouts.objects.filter(Class=Class_id).exists():
            context['layout']=Layouts.objects.get(Class=Class_id).TableLayout
        context['table']=table
        context['Class_id']=Class_id
        return render(request, self.template, context)

    def post(self, request,Class_id) :
        if request.POST:
            print()
            #layout=json.loads(request.POST['layout'])
            lo_to_save=request.POST['layout']
            if Layouts.objects.filter(Class=Class_id).exists():
                rec=Layouts.objects.get(Class=Class_id)
                rec.TableLayout=lo_to_save
            else:
                rec=Layouts(TableLayout=lo_to_save,Class=Class_id)
            rec.save()

        return HttpResponseRedirect(reverse('ut:change_tabletemplate',kwargs={'Class_id':Class_id}))

from django.forms import formset_factory

class TestForm(forms.Form):
    id=forms.IntegerField()
    name=forms.CharField()

from crispy_forms.layout import LayoutObject, Submit, Row, Column, MultiField,Field,Div,Fieldset,TEMPLATE_PACK,HTML
from crispy_forms.helper import FormHelper
from django.template.loader import render_to_string

class FormSet1(LayoutObject):
    template='ut/test.html'
    def __init__(self,formset_name_in_context,template=None):
        self.formset_name_in_context = formset_name_in_context
        self.fields=[]
        if template:
            self.template=template
        def render (self,form,form_style,context,template_pack=TEMPLATE_PACK):
            formset = context[self.formset_name_in_context]
            print('i was here')
            return render_to_string(self.template,{'formset':formset})

class TestParentForm(forms.Form):
    parent=forms.CharField()
    child=forms.CharField()
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.helper=FormHelper()
        self.helper.layout=Layout(
            Div(
                Field('child'),
                HTML("""{% load render_table from django_tables2 %}  
                        {% if formset %} 
                        something {% render_table formset %}
                        {% else %}
                        Nothing  
                        {% endif %}
                        """),
                ),
            Field('parent'),
        )

class TestFormsetFactory(View):
    template = 'ut/test2.html'
    def get (self,request):
        cntx={}
        data = [
            {"width":100,"name": "Bradley","abc":'a'},
            {"name": "Stevie","abc":'c'},
        ]

        class NameTable(tables.Table):
            name = tables.Column()
            abc = tables.Column()

        table = NameTable(data)

        TestFormSet = formset_factory(TestForm, extra=2);
        cntx['form'] = TestParentForm()
        cntx['formset']=table
        return render(request,self.template,context=cntx)






