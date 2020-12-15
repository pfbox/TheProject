from django.views.generic import View,UpdateView,CreateView,ListView,DeleteView
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse,reverse_lazy
from django.shortcuts import render
from .tables import *
from .forms import *
from django.template.context_processors import csrf
import numpy as np
from django_tables2 import SingleTableView
#from .filters import ClassesFilter
from django.db.models import Exists, OuterRef
import json

from .utclasses import *
from django_tables2 import RequestConfig
from django.contrib.auth.mixins import LoginRequiredMixin

def index(request):
    context={'table_list':am.to_dict('records')}
    context['classes']=Classes.objects.all()
    context['projects']=Projects.objects.all()
    context['reports']=Reports.objects.all()
    context['pr_rep_conn']=ProjectReportConn.objects.all()
    context['pr_cl_conn']=ProjectClassConn.objects.all()
    context['defaultreport']=get_reporttable(5)['table']
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

class delete_instance(LoginRequiredMixin,DeleteView):
    model = Instances
    success_url = reverse_lazy('ut:index')
    def get(self,*args,**kwargs):
        self.success_url = reverse_lazy('ut:instances',kwargs={'Class_id':kwargs['Class_id'],})
        return self.post(*args,**kwargs)

class edit_instance_base(View):
    def post(self,request,*args,**kwargs):
        Class_id=kwargs['Class_id']
        Instance_id=kwargs['Instance_id']
        if request.POST.get('cancel'):
            return HttpResponseRedirect(reverse('ut:instances', args=(Class_id,)))
        else:
            form=InstanceForm(request.POST,Class_id=Class_id,Instance_id=Instance_id,ReadOnly='False',validation=True)
            if form.is_valid():
                save_instance_byname(Class_id=Class_id,Instance_id=Instance_id,instance=form.cleaned_data,passed_by_name=False)
                return HttpResponseRedirect(reverse('ut:instances', args=(Class_id,)))

    def get(self,request,ReadOnly=False,*args,**kwargs):
        Class_id=kwargs['Class_id']
        Instance_id=kwargs['Instance_id']
        form = InstanceForm(Class_id=Class_id, Instance_id=Instance_id,ReadOnly=ReadOnly, validation=False)
        context = {}
        for a1 in Attributes.objects.filter(Class_id=Class_id, DataType_id=10):
            refclass_id = a1.Ref_Class.id
            refattr = a1.Ref_Attribute.Attribute
            if Instance_id == 0:
                filter = {refattr: -1}
            else:
                filter = {refattr: Instance_id}
            qs = create_rawquery_from_attributes(refclass_id, filter=filter)
            table = mytable(Class_id=refclass_id, style='ShortLayout', data=qs)
            context['table' + str(a1.id) + ''] = table
        context['form'] = form
        return render(request, 'ut/edit_instance.html', context)

class edit_instance(LoginRequiredMixin,edit_instance_base):
    pass

class view_instance(edit_instance_base):
    def get(self,request,ReadOnly=True,*args,**kwargs):
        return super().get(request,ReadOnly=ReadOnly,*args,**kwargs)

def classestree_view(request):
    return render(request, "ut/classestree.html", {'table': Classes.objects.all()})

def reports_view(request,Project_id=0):
    if Project_id==0:
        table = ReportsTable(Reports.objects.all())
    else:
        table =  ReportsTable(Reports.objects.annotate(connectionexists=Exists(ProjectReportConn.objects.filter(Class=OuterRef('pk'),Project_id=Project_id))).filter(connectionexists=True))
    RequestConfig(request, paginate={"per_page": 50}).configure(table)
    return render(request,'ut/reports.html',{'table':table,'Project_id':Project_id})

def projects_view(request):
    table = ProjectsTable(Projects.objects.all())
    RequestConfig(request, paginate={"per_page": 50}).configure(table)
    return render(request,'ut/projects.html',{'table':table})

def classes_view(request,Project_id=0):
    if Project_id==0:
        table = ClassesTable(Classes.objects.all())
    else:
        table =  ClassesTable(Classes.objects.annotate(connectionexists=Exists(ProjectClassConn.objects.filter(Class=OuterRef('pk'),Project_id=Project_id))).filter(connectionexists=True))
    RequestConfig(request, paginate={"per_page": 25}).configure(table)
    return render(request,'ut/classes.html',{'table':table,'classes':table,'Project_id':Project_id})

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

class ReportRun(View):
    template='ut/showreport.html'
    def get(self,request,Report_id,Simple=False,*args,**kwargs):
        r=get_reporttable(Report_id)
        context={}
        context['table']=r['table']
        context['Report_id']=Report_id
        context['ReportName']=r['ReportName']
        #if not request.GET._mutable:
        #    request.GET._mutable = True
        # print (request.GET)
        #if request.GET.get('sort'):
        #RequestConfig(request).configure(table)
        #    table.order_by = sort
        #    print ('sort=',sort)
        #table.paginate(page=request.GET.get("page", 1), per_page=30)
        if Simple:
            self.template='ut/simplereport'
        return render(request, self.template, context)


class ReportRun(View):
    template='ut/showreport.html'
    def get(self,request,Report_id,*args,**kwargs):
        r=Reports.objects.get(pk=Report_id)
        sql=r.Query
        cursor=con.cursor()
        cursor.execute(sql)
        t=dictfetchall(cursor)
        extra_columns=[(c[0], tables.Column()) for c in cursor.description]
        context={}
        context['table']=ReportTable(data=t,extra_columns=extra_columns)
        context['Report_id']=Report_id
        context['ReportName']=r.Report
        #if not request.GET._mutable:
        #    request.GET._mutable = True
        # print (request.GET)
        #if request.GET.get('sort'):
        #RequestConfig(request).configure(table)
        #    table.order_by = sort
        #    print ('sort=',sort)
        #table.paginate(page=request.GET.get("page", 1), per_page=30)
        return render(request, self.template, context)

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
    filterform= InstanceFilterForm(Class_id=Class_id,filter=filter) #create_filter_set(Class_id,filter)

    qs=create_rawquery_from_attributes(Class_id,filter)
    #print (qs)
    if pd.isnull(sort):
        sort='Code'
    if SaveToExl:
        return export_instances_xls(request,qs)
    else:
        pass
    #h_link = tables.LinkColumn('ut:edit_instance', text=lambda x: x.Code, args=[A('Class_id'), A('pk')], orderable=False)

    table=mytable(Class_id=Class_id,style='TableLayout',data=qs)
    #print (table)
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

def attributes_view(request,Class_id):
    attlist=Attributes.objects.filter(Class_id=Class_id)
    table = AttributeTable(attlist)
    RequestConfig(request, paginate={"per_page": 20}).configure(table)
    return render(request,'ut/attributes.html',{'table':table,'Class_id':Class_id})

class filters_view(View):
    template='ut/filters.html'
    def get(self,request,*args,**kwargs):
        self.Class_id=kwargs['Class_id']
        context={'Class_id':self.Class_id}
        table = FilterTable(Filters.objects.filter(Class_id=self.Class_id))
        context['table']=table
        return render(request,self.template,context)

def edit_attribute(request,Attribute_id):
    at=Attributes.objects.get(pk=Attribute_id)
    form = AttributeForm(instance=at)
    return render(request,'ut/edit_attribute.html',{'form':form})

class ProjectEdit(UpdateView):
    model = Projects
    template_name = 'ut/edit_attribute.html'
    form_class = ProjectForm
    def get_success_url(self):
        return reverse_lazy('ut:projects_view')

class ProjectCreateVeiw(CreateView):
    model = Projects
    template_name = 'ut/edit_attribute.html'
    form_class = ProjectForm
    def get_success_url(self):
        return reverse_lazy('ut:projects_view')

class ReportEdit(UpdateView):
    model = Reports
    template_name = 'ut/edit_attribute.html'
    form_class = ReportForm
    def get_success_url(self):
        return reverse_lazy('ut:reports_view')

class ReportCreateVeiw(CreateView):
    model = Reports
    template_name = 'ut/edit_attribute.html'
    form_class = ReportForm
    def get_success_url(self):
        return reverse_lazy('ut:reports_view')

from bootstrap_modal_forms.generic import BSModalCreateView

class FilterCreateView(LoginRequiredMixin,CreateView):
    model = Filters
    template_name = 'ut/edit_attribute.html'
    form_class = FilterEditForm

    def get_success_url(self):
        return reverse_lazy('ut:filters_view', args = (self.Class_id,))

    def get_initial(self):
        initial = super().get_initial()
        self.Class_id = self.kwargs['Class_id']
        initial['Class']=Classes.objects.get(pk=self.Class_id)
        return initial

    def get_form_kwargs(self):
        kw=super(FilterCreateView,self).get_form_kwargs()
        kw['initial']['Class_id']=self.Class_id
        return kw

class FilterUpdateView(LoginRequiredMixin,UpdateView):
    model = Filters
    template_name = 'ut/edit_attribute.html'
    form_class = FilterEditForm

    def get_success_url(self):
        return reverse_lazy('ut:filters_view',args=(self.object.Class.id,))

class AttributeCreateView(LoginRequiredMixin,CreateView):
    model = Attributes
    template_name = 'ut/edit_attribute.html'
    form_class = AttributeForm

    def get_success_url(self):
        return reverse_lazy('ut:attributes_view', args = (self.Class_id,))

    def get_initial(self):
        initial = super().get_initial()
        self.Class_id = self.kwargs['Class_id']
        initial['Class']=Classes.objects.get(pk=self.Class_id)
        return initial

    def get_form_kwargs(self):
        kw=super(AttributeCreateView,self).get_form_kwargs()
        kw['initial']['Class_id']=self.Class_id
        return kw

class AttributeUpdateView(LoginRequiredMixin,UpdateView):
    model = Attributes
    template_name = 'ut/edit_attribute.html'
    form_class = AttributeForm

    def get_success_url(self):
        return reverse_lazy('ut:attributes_view',args=(self.object.Class.id,))

class ClassesUpdateView(LoginRequiredMixin,UpdateView):
    model = Classes
    template_name = 'ut/edit_attribute.html'
    form_class = ClassesForm

    def get_success_url(self):
        return reverse_lazy('ut:classes_view')

class ClassesCreateView(LoginRequiredMixin,CreateView):
    model = Classes
    template_name = 'ut/edit_attribute.html'
    form_class = ClassesForm

    def get_success_url(self):
        return reverse_lazy('ut:classes_view')

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
            return HttpResponseRedirect(reverse('ut:instances', args=(Class_id,)))
    else:
        form = UploadInstances()
    return render(request, 'ut/loadinstances.html', {'form': form,'Class_id':Class_id})

class ProtectView(LoginRequiredMixin, View) :
    def get(self, request):
        return render(request, 'ut/index.html')

class FormTemplateView(View):
    template = 'ut/formtemplate.html'
    def get(self, request,Class_id):
        table=get_editfieldlist(Class_id,df_attributes)
        context={}
        if Layouts.objects.filter(Class=Class_id).exists():
            context['layout']=Layouts.objects.get(Class=Class_id).FormLayout
        context['table']=table.to_dict('records')
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
                rec=Layouts(FormLayout=lo_to_save,Class_id=Class_id)
            rec.save()

        return HttpResponseRedirect(reverse('ut:change_formtemplate',kwargs={'Class_id':Class_id}))

class TableTemplateView(View):
    template = 'ut/tabletemplate.html'
    def get(self, request,Style,Class_id):
        table= get_editfieldlist(Class_id,df_attributes).to_dict('records')
        context={}
        if Layouts.objects.filter(Class=Class_id).exists():
            context['layout']=getattr(Layouts.objects.get(Class=Class_id),Style)
        context['table']=table
        context['Class_id']=Class_id
        context['Style']=Style
        return render(request, self.template, context)

    def post(self, request,Style,Class_id) :
        if request.POST:
            #layout=json.loads(request.POST['layout'])
            lo_to_save=request.POST['layout']
            if Layouts.objects.filter(Class=Class_id).exists():
                rec=Layouts.objects.get(Class=Class_id)
            else:
                rec=Layouts(Class=Class_id)
            setattr(rec,Style,lo_to_save)
            rec.save()

        return HttpResponseRedirect(reverse('ut:change_tabletemplate',kwargs={'Style':Style,'Class_id':Class_id}))

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
            return render_to_string(self.template,{'formset':formset})

from django.http import JsonResponse
def ajax_change_master(request,Attribute_id):
    value = int(request.GET['value'])
    m_attr=get_attribute(Attribute_id,df_attributes)
    Ref_Class_id=df_attributes[df_attributes.id==Attribute_id].Ref_Class_id.max()
    Class_id=df_attributes[df_attributes.id==Attribute_id].Class_id.max()
    data={}
    data['MasterAttribute_id']=Ref_Class_id
    attrs={}
    #find all attributes who depends on that Attribute_id
    for i,a in df_attributes[(df_attributes.MasterAttribute_id==Attribute_id)&(df_attributes.Class_id==Class_id)].iterrows():
        instances=get_options(a.id,{m_attr.Attribute:value})
        attrs[a.id]=instances
    data['attrs']=attrs

    #find lookups
    lookups={}
    for i,a in df_attributes[(df_attributes.DataType_id==DT_Lookup)&(df_attributes.InternalAttribute_id==Attribute_id)].iterrows():
        if value !=0 :
            lookups[a.id]=Values.objects.filter(Attribute_id=a.Ref_Attribute_id,Instance_id=value).values()[0]['char_value']
        else:
            lookups[a.id]='(None)'
    data['lookups']=lookups
    return JsonResponse(data)