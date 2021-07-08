from ut.models import *
import django_tables2 as tables
import pandas as pd
from .tables import ReportTable
from django_pandas.io import read_frame
import numpy as np
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import re
from django.urls import reverse,reverse_lazy
from .widgets import utHeavyWidget, ImagePreviewWidget, PictureWidget
from datetime import datetime,date,time
from django.contrib.auth.models import User
from .constants import evUPDATE,evINSERT
from .utparser import UtParser
from django.db.models import Exists, OuterRef, Prefetch
from django_tables2.utils import A

from django_select2.forms import Select2MultipleWidget


from django.forms import DateInput,DateTimeInput,TimeInput,SplitDateTimeField,SplitDateTimeWidget

from django.apps import apps

app_models = apps.get_app_config('ut').get_models()
am=pd.DataFrame()
for a in app_models:
    am = am.append({'TableName': a._meta.verbose_name, 'Table': a},ignore_index=True)  # .to_dict()

from django.db import connection,connections
#con=connection #['readonly']
#df_classes=pd.DataFrame()#pd.read_sql('select * from ut_classes',con) #.set_index('id')
#df_attributes=pd.DataFrame()#pd.read_sql('select * from ut_attributes',con)#.set_index('id')
#df_datatypes=pd.DataFrame()#pd.read_sql('select * from ut_datatypes',con) #.set_index('id')
#df_inputtypes=pd.DataFrame()#pd.read_sql('select * from ut_inputtypes',con) #.set_index('id')
#df_formlayouts=pd.read_sql('select * from ut_formlayouts',con) #.set_index('id')
#df_filters=pd.DataFrame()

select_options_sql=r"""
select 
i.id, i.Code,v2.char_value from ut_instances i, ut_values v , ut_values v2
WHERE 
 v.Instance_id=i.id and 
v2.Instance_id=i.id and
i.Class_id = {cl} and
v.instance_value_id={val} and
v2.Attribute_id={att}
and v2.char_value like '%term%'
"""

#Values.objects(Attribute_id=Attribute_id,char_value__icontains=term, )

select_simple_options_sql="""
select 
i.id, case when {Attribute_id}=-1 then i.Code else v2.char_value end options  from ut_instances i
left outer join ut_values v2 on v2.Instance_id = i.id and v2.Attribute_id = {Attribute_id}
WHERE
i.Class_id={Class_id} 
"""

def value_if_null(x,val):
    if pd.isnull(x):
        return val
    else:
        return x

def get_instance(Class_id,Instance_id):
    sql=create_qs_sql(Class_id,Instance_id)['sql']
    rocon=connections['readonly']
    with rocon.cursor() as cursor:
        cursor.execute(sql)
        instance = dict(zip([column[0] for column in cursor.description], cursor.fetchone()))
    return instance

def get_instance_values(Class_id,Instance_id):
    values=memory_cache.get('instance-values-{}'.format(Instance_id))
    if not values:
        sql = create_val_sql(Class_id,Instance_id)
        rocon=connections['readonly']
        with rocon.cursor() as cursor:
            cursor.execute(sql)
            values = dict(zip([column[0] for column in cursor.description], cursor.fetchone()))
        memory_cache.set('instance-values-{}'.format(Instance_id),values)
    return values


def get_simple_options(Class_id,Attribute_id):
    rocon=connections['readonly']
    with rocon.cursor() as cursor:
        cursor.execute(select_simple_options_sql.format(Class_id=Class_id,Attribute_id=Attribute_id))
        dict=cursor.fetchall()
    return dict

def create_table_column(dt,width=50,attr={}):
    if dt in [5]:
        res=tables.DateColumn(attrs={'th': {'width': width}})
    elif dt in [7]:
        res = tables.DateTimeColumn(attrs={'th': {'width': width}})
    else:
        res = tables.Column(attrs={'th': {'width': width}})
    return res

def valuefield_property(attr):
    dt= attr.DataType.id
    attribute = attr.Attribute
    res = {}
    if attr.id == Default_Attribute:
        res[attribute] = 'ins.Code'
    elif dt == DT_Lookup:
            res[attribute] = '{tab}.{field}' \
                .format(tab=attr.RefAttrTableName, field=get_fieldname(attr.Ref_Attribute.DataType_id))
    elif dt == DT_External:
        res[attribute] = '{tab}.{field}'.format(tab=attr.ExternalTable, field=attr.ExternalField)
    elif dt in [DT_Table]:
        res[attribute] = '0 as Table__' + str(id) + '__'
    elif dt in [DT_Calculated]:
        res[attribute] = '{formula}'.format(formula=attr.Formula)
    else:
        res[attribute] = '{tab}.{field}'.format(tab=attr.TableName, id=id,field=get_fieldname(dt))
    return res

def valueleftouter(id):
    attr = Attributes.objects.get(pk=id)
    dt= attr.DataType_id
    internal_attr = attr = Attributes.objects.get(pk=attr.InternalAttribute_id)
    res={}
    if dt == DT_External:
        res[attr.ExternalTable] = 'LEFT OUTER JOIN {ext} as {ext} ON ({ext}.{uq}={loctab}.{locfield})'\
            .format(ext=attr.ExternalTable,uq=attr.ExternalUq,loctab=internal_attr.TableName,locfield=get_fieldname(internal_attr.DataType_id))
    elif dt == DT_Lookup:
        res[internal_attr.TableName]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}.Instance_id=ins.id and {tab}.Attribute_id={id}) --{attr} 1'\
            .format(val=Values._meta.db_table,tab=internal_attr.TableName,id=internal_attr.id,attr=attr.Attribute)
        res[internal_attr.RefTableName] = 'LEFT OUTER JOIN {ins} as {reftab} ON ({reftab}.id={tab}.instance_value_id) --{attr} 2' \
            .format(ins=Instances._meta.db_table, tab=internal_attr.TableName, reftab=internal_attr.RefTableName,attr=attr.Attribute)
        res[attr.RefAttrTableName] = 'LEFT OUTER JOIN {val} as {refval} ON ({refval}.Instance_id = {reftab}.id and {refval}.Attribute_id = {refatt}) --{attr} 3' \
                .format(val=Values._meta.db_table, refval=attr.RefAttrTableName, refatt=attr.Ref_Attribute_id,
                        reftab=internal_attr.RefTableName,attr=attr.Attribute)
    else:
        res[attr.TableName]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}.Instance_id=ins.id and {tab}.Attribute_id={id}) --{attr}'\
            .format(val=Values._meta.db_table,tab=attr.TableName,id=attr.id,attr=attr.Attribute)
    return res

def leftouter(id):
    attr = Attributes.objects.get(pk=id)
    dt= attr.DataType_id
    internal_attr = Attributes.objects.get(pk=attr.InternalAttribute_id)
    res={}
    if dt == DT_External:
        res[attr.ExternalTable] = 'LEFT OUTER JOIN {ext} as {ext} ON ({ext}.{uq}={loctab}.{locfield})'\
            .format(ext=attr.ExternalTable,uq=attr.ExternalUq,loctab=internal_attr.TableName,locfield=get_fieldname(internal_attr.DataType_id))
    elif dt == DT_Lookup:
        res[internal_attr.TableName]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}.Instance_id=ins.id and {tab}.Attribute_id={id}) --{attr} 1'\
            .format(val=Values._meta.db_table,tab=internal_attr.TableName,id=internal_attr.id,attr=attr.Attribute)
        res[internal_attr.RefTableName] = 'LEFT OUTER JOIN {ins} as {reftab} ON ({reftab}.id={tab}.instance_value_id) --{attr} 2' \
            .format(ins=Instances._meta.db_table, tab=internal_attr.TableName, reftab=internal_attr.RefTableName,attr=attr.Attribute)
        res[attr.RefAttrTableName] = 'LEFT OUTER JOIN {val} as {refval} ON ({refval}.Instance_id = {reftab}.id and {refval}.Attribute_id = {refatt}) --{attr} 3' \
                .format(val=Values._meta.db_table, refval=attr.RefAttrTableName, refatt=attr.Ref_Attribute_id,
                        reftab=internal_attr.RefTableName,attr=attr.Attribute)
    else:
        res[attr.TableName]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}.Instance_id=ins.id and {tab}.Attribute_id={id}) --{attr}'\
            .format(val=Values._meta.db_table,tab=attr.TableName,id=attr.id,attr=attr.Attribute)
        if dt == DT_Instance:
            res[attr.RefTableName]='LEFT OUTER JOIN {ins} as {reftab} ON ({reftab}.id={tab}.instance_value_id) --{attr}'\
                .format(ins=Instances._meta.db_table,tab=attr.TableName,reftab=attr.RefTableName,attr=attr.Attribute)
            if attr.Ref_Attribute_id!=Default_Attribute:
                res[attr.RefAttrTableName] = 'LEFT OUTER JOIN {val} as {refval} ON ({refval}.Instance_id = {reftab}.id and {refval}.Attribute_id = {refatt}) --{attr}'\
                    .format(val=Values._meta.db_table,refval=attr.RefAttrTableName,refatt=attr.Ref_Attribute_id,reftab=attr.RefTableName,attr=attr.Attribute)

    return res

def calculated(dt):
    if dt in [DT_External,DT_Calculated]:
        return True
    else:
        return False

def get_options(Attribute_id=0,SelectedInstance_id=None,values={},validation=False,term='') :
    attr=get_attribute(Attribute_id)
    instances={}
    if False: #(attr.MasterAttribute_id>0) and (not validation):
        m_attr=get_attribute(attr.MasterAttribute_id)
        tmp=values.get(m_attr.Attribute)
        if pd.notnull(tmp):
            m_value=int(tmp)
        else:
            m_value=0

        if attr.Ref_Attribute_id == Default_Attribute:
            for r in Values.objects.filter(instance_value_id=m_value,Instance__Class__id=attr.Ref_Class_id):
                instances[r.Instance_id]=r.Instance.Code
        else:
            for r in Instances.objects.raw(select_options_sql.format(val=m_value,cl=attr.Ref_Class_id,att=attr.Ref_Attribute_id)):
                instances[r.id]=r.char_value
    else:
        ref_attribute = attr.Ref_Attribute
        if ref_attribute.id == Default_Attribute:
            if pd.isnull(SelectedInstance_id):
                filter=Q(Class_id=attr.Ref_Class_id)
            else:
                filter = Q(Class_id=attr.Ref_Class_id)&Q(id=SelectedInstance_id)
            for r in Instances.objects.filter(filter):
                instances[r.id]=r.Code
        else:
            if pd.isnull(SelectedInstance_id):
                filter=Q(Attribute_id=ref_attribute.id)
            else:
                filter = Q(Attribute_id=ref_attribute.id)&Q(Instance_id=SelectedInstance_id)
            qs=Values.objects.filter(filter)
            use_ref=False
            while ref_attribute.DataType_id==DT_Instance:
                use_ref=True
                filter = filter&Q(**{'instance_value__values_ins__Attribute_id':ref_attribute.Ref_Attribute_id})
                qs=qs.select_related('instance_value').prefetch_related(Prefetch('instance_value__values_ins',to_attr='lookup_field'))
                ref_attribute=ref_attribute.Ref_Attribute
            for r in qs.filter(filter):
                instances[r.Instance_id]= r.instance_value.values_ins.first().char_value if use_ref else r.char_value
    return instances

from django import forms
#from bootstrap_datepicker_plus import DatePickerInput,DateTimePickerInput,TimePickerInput

def create_form_field_check(attr):
    dt = attr.DataType_id
    if dt in [DT_Calculated,DT_Table]:
        res=False
    else:
        res=True
    return res

from django.forms import ModelChoiceField

class MyModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.char_value

def create_form_field(attr,usedinfilter=False,filter={},readonly=False,values={},fn='',validation=False):
    if fn == '':
        FieldName=attr.Attribute
    else:
        FieldName=fn
    dt=attr.DataType_id
    if usedinfilter:
        req=False
        fclass='filterfield'
    else:
        req=attr.NotNullAtt
    valueslist=attr.ValuesList
    vl=''
    if pd.isnull(valueslist) or (valueslist == ''):
        vl = ''
    else:
        if re.search('^select',valueslist,re.IGNORECASE):
            try:
                rocon=connections['readonly']
                cursor=rocon.cursor()
                cursor.execute(valueslist)
                vl=cursor.fetchall()
            except:
                print ('Could not load values from sql-->'+valueslist+'<--')
        else:
            try:
                vl=json.loads(valueslist)
            except:
                print ('Could not load list of values for field',FieldName,'Class =',attr.Class_id,' String=',valueslist)


    if dt in [DT_Integer]:
        if vl=='':
            field=forms.IntegerField(required=req)
        else:
            field=forms.ChoiceField(choices=vl,required=req)
    elif dt in [DT_Boolean]:
        field = forms.ChoiceField(choices=[(0,'FALSE'),(1,'TRUE')], required=req)
    elif dt in [DT_Float]:
        if vl=='':
            field = forms.FloatField(required=req)
        else:
            field=forms.ChoiceField(choices=vl,required=req)
    elif dt in [DT_Lookup]:
        field=create_form_field(attr.Ref_Attribute)
    elif dt in [DT_String,DT_External]:
        if vl=='':
            field = forms.CharField(max_length=255, required=req)
        else:
            field=forms.ChoiceField(choices=vl,required=req)
    elif dt in [DT_Text]:
        field=forms.CharField(widget=forms.Textarea(attrs={'rows':1}),required=req)
    elif dt in [DT_Hyperlink]:
        field=forms.URLField(required=req)
    elif dt in [DT_Date]:
        field=forms.DateField(required=req, widget=DateInput(format=('%Y-%m-%d'),attrs={'class':'datefield','autocomplete': 'off'})
                              )
    elif dt in [DT_Datetime]:
        field=forms.DateTimeField(required=req, widget=DateTimeInput(format=('%Y-%m-%d %H:%M:%S'),attrs={'class':'datetimefield','autocomplete': 'off'}))
    elif dt in [DT_Time]:
        field = forms.TimeField(required=req, widget=TimeInput(format=('%H:%M'),attrs={'class':'timefield','autocomplete': 'off'}))
    elif dt in [DT_File]:
        field = forms.FileField(required=req, allow_empty_file=(not req))
    elif dt in [DT_Image]:
        field = forms.ImageField(required=req,allow_empty_file=(not req)) #,widget=PictureWidget
    elif dt in [DT_Instance]:
        if validation:
            field = forms.IntegerField(required=req)
        else:
            if True:#attr.InputType_id in [IT_Default, IT_Select2] : #usedinfilter: attr.InputType_id==IT_Select2:
                if usedinfilter:
                    op = {}
                else:
                    op = get_options(Attribute_id=attr.id,SelectedInstance_id=value_if_null(values.get(attr.Attribute),0),values=values, validation=validation)
                ch = [(k, v) for k, v in op.items()]
                field = forms.ChoiceField(choices=ch,required=req,
                    widget= utHeavyWidget(data_url=reverse_lazy('ut:ajax_get_attribute_options',kwargs={'Class_id':attr.Class_id,'Attribute_id':attr.id})
                                               ,attrs={"data-minimum-input-length": 0}
                                               ,dependent_fields= (attr.dependent_fields if not usedinfilter else None),
                ))
            elif attr.InputType_id == IT_RadioButton:
                op = get_options(Attribute_id=attr.id, values=values, validation=validation)
                ch = []
                ch = ch + [(0, '(None)')] + [(k, v) for k, v in op.items()]
                field=forms.ChoiceField(required=req,widget=forms.RadioSelect(choices=ch))
            else:
                op = get_options(Attribute_id=attr.id, values=values, validation=validation)
                if usedinfilter:
                    ch = [(-1, '(All)')]
                else:
                    ch = []
                ch = ch + [(0, '(None)')] + [(k, v) for k, v in op.items()]
                field=forms.ChoiceField(choices=ch,required=req)
    elif dt == [DT_Datetime]:
        field = forms.DateTimeField(required=req)
    elif dt == DT_Table: #list Do not use
        return False
    elif dt in [DT_Currency]: #Currency
        field = forms.FloatField(required=req)
    elif dt in [DT_Email]: #Email
        if not usedinfilter:
            field = forms.EmailField(required=req)
        else:
            field = forms.CharField(max_length=255,required=req)
    elif dt == DT_ManyToMany:
        ch=get_simple_options(Class_id=attr.Ref_Class_id,Attribute_id=attr.Ref_Attribute_id)
        field = forms.MultipleChoiceField(choices=ch,required=req
                                          ,widget=Select2MultipleWidget
                                          )
    elif dt == DT_Calculated:
        return False
    else:
        #print ('this exception')
        raise Exception('Datatype {} does not exists.'.format(dt))
    return field

def filter_value(attr):
    if attr.DataType_id in DT_NUMBERS:
        res = '{val}'
    elif attr.DataType_id:
        res = "'{val}'"
    else:
        res = ''
    return res

def make_filter_expression(f):
    res={}
    for ft in filter_expression_columns:
        expr =  f[ft]
        if f.Attribute2_id != Default_Attribute:
            expr = expr + ' ' + f.Condition1 + ' ' + f[ft+'_at2']
        if f.Attribute3_id != Default_Attribute:
            expr = expr + ' ' + f.Condition2 + ' ' + f[ft+'_at3']
        res[ft] = ' and ('+expr+')'
    return res

def get_filter(Filter_id=0,Class_id=0,FilterName=''):
    if Filter_id!=0:
        res=Filters.objects.get(pk=Filter_id)
    else:
        res=Filters.objects.get(Class_id__in=[Class_id,Default_Class],Filter=FilterName)
    return res

def get_attribute(id):
    return Attributes.objects.get(pk=id)

def get_actionitems(Class_id):
    return  Attributes.objects.filter(DataType_id__in=[DT_ActionItem],Class_id__in=[Class_id])

def get_editfieldlist(Class_id):
    exclude=[DT_Calculated,DT_ActionItem]
    return  Attributes.objects.exclude(DataType_id__in=exclude).filter(Class_id__in=[Class_id,Default_Class])

def get_updatefieldlist(Class_id):
    exclude=[DT_Calculated,DT_Lookup]
    return  Attributes.objects.exclude(DataType_id__in=exclude).filter(Class_id__in=[Class_id,Default_Class])


def get_calulatedfieldlist(Class_id):
    return  Attributes.objects.filter(Class_id__in=[Class_id,Default_Class],DataType_id__in=[DT_Calculated])

def get_tableviewlist(Class_id):
    exclude=[DT_Table,DT_ManyToMany,DT_ActionItem]
    return  Attributes.objects.exclude(DataType_id__in=exclude).filter(Class_id__in=[Class_id,Default_Class])
        #df_attr[df_attr.Class_id.isin([Class_id,0])&(~df_attr.DataType_id.isin([DT_Table,DT_ManyToMany]))]

def get_fulllist(Class_id):
    return Attributes.objects.filter(Class_id__in=[Class_id,Default_Class])

def get_user_fulllist(Class_id):
    return Attributes.objects.filter(Class_id__in=[Class_id,Default_Class])

def create_orderby(Class_id,orderby):
    res=''
    ord=[]
    for key,val in orderby.items():
        ord.append(" {di}{key}{di} {val}".format(key=key,val=val,di=Default_Identifier))
    if len(ord)>0:
        res='Order by' + ','.join(ord)
    return res

def create_limit_offset(Class_id,limit=None,offset=None):
    lostr=''
    if not pd.isnull(limit):
        lostr=lostr + ' LIMIT {}'.format(limit)
    if not pd.isnull(offset):
        lostr=lostr + ' OFFSET {}'.format(offset)
    return lostr

def create_search_all(columns,search=''):
    tmp=[]
    for c in columns:
        tmp.append("lower(cast({f} AS VARCHAR)) like lower('%{s}%')".format(f=c,s=search))
    return ' and (' +' or '.join(tmp) + ')'

def create_rawquery_sql(Class_id=0,filter={},masterclassfilter={},orderby={},search='',limit=None,offset=None,user=None):
    sql_col= create_qs_sql(Class_id=Class_id,user=user)
    columns= sql_col['selectfields'] #real db field (not aliases)
    # order by create by aliases
    # searchig all fields only if search > ''
    sql = sql_col['sql'] + '\n' \
          + create_filter_for_sql(Class_id=Class_id, filter=filter,masterclassfilter=masterclassfilter) + '\n' \
          + (create_search_all(columns=columns,search=search) if search!='' else '' ) +'\n' \
          + create_orderby(Class_id=Class_id,orderby=orderby) + '\n' \
          + create_limit_offset(Class_id=Class_id,limit=limit,offset=offset)
    #print (sql)
    return sql.replace(Default_Identifier,Current_Identifier)

def create_rawquery_from_attributes(Class_id=0,filter={},masterclassfilter={},orderby={},search='',offset=None,limit=None):
    sql=create_rawquery_sql(Class_id,filter,masterclassfilter,orderby=orderby,search=search,offset=offset,limit=limit)
    qs=Instances.objects.raw(sql)
    return qs

def create_count_sql(Class_id=0,filter={},masterclassfilter={},search=''):
    sql = create_rawquery_sql(Class_id=Class_id, filter=filter, masterclassfilter=masterclassfilter,search=search)
    sql = 'select 0 as id, count(*) as Count from (' + sql + ') ct'
    return sql

def create_val_sql(Class_id,Instance_id):
    sql=memory_cache.get('val-sql-{}'.format(Class_id))
    if not sql:
        atts=get_tableviewlist(Class_id=Class_id)
        ss = {'id':'ins.id','Code':'ins."Code"'}
        lo = {'ins' : '{} ins '.format(Instances._meta.db_table)}
        for a in atts:
            if a.id != Default_Attribute:
                ss[a.Attribute]=a.ValueField
                for key,val in a.ValueLeftOuter.items():
                    lo[key]=val
        if len(ss)>0:
            co=','
        else:
            co=''
        calcfields=get_calulatedfieldlist(Class_id)
        for cf in calcfields:
            for key,val in ss.items():
                if ('"'+key+'"') in ss[cf.Attribute]:
                    ss[cf.Attribute]=ss[cf.Attribute].replace('"'+key+'"',val)
        #print (ss,lo)
        sselect = 'select ' + ',\n'.join(["{f}  as {di}{a}{di}".format(f=ss[i],a=i,di=Default_Identifier) for i in ss ])
        sfrom='from ' +'\n'.join(lo.values())
        swhere = 'where ins.id={}'
        sql=sselect +'\n' + sfrom + '\n' + swhere
        memory_cache.set('val-sql-{}'.format(Class_id),sql)
    return sql.format(Instance_id)

def create_qs_sql(Class_id=0,Instance_id=0,user=None):
    if user:
        user_id = 1#await sync_to_async(User.objects.get, thread_sensitive=True)(username=user)
    else:
        user_id=get_current_user().id
    atts=get_tableviewlist(Class_id=Class_id)
    #default for instances id, code, and instance table
    ss = {'id':'ins.id','Code':'ins."Code"'}
    lo = {'ins' : '"{}" ins '.format(Instances._meta.db_table)}
    ajax_columns = {'id': 'data', 'Code': 'data'}
    hl = {}
    for a in atts:
        if a.DataType_id== DT_Lookup:
            dt = a.Ref_Attribute.DataType_id
        else:
            dt = a.DataType_id
        if dt == DT_Hyperlink:
            if a.Ref_Attribute_id != Default_Attribute:
                hl[a.Attribute]=a.Ref_Attribute_id
            ajax_columns[a.Attribute] = 'hlink'
        elif (dt == DT_Instance) and (a.DataType_id!=DT_Lookup):
            ajax_columns[a.Attribute] = 'instance'
        elif dt in [DT_File,DT_Image]:
            ajax_columns[a.Attribute] = 'file'
        else:
            ajax_columns[a.Attribute] = 'data'

        if a.id != Default_Attribute:
            for key, val in a.LeftOuter().items():
                lo[key] = val

            if a.DataType_id==DT_Instance and a.Ref_Attribute.DataType_id == DT_Instance:
                ref_attribute=a.Ref_Attribute
                while ref_attribute.DataType_id == DT_Instance:
                    for key, val in ref_attribute.LeftOuter(mfield=a.ValueField).items():
                        if key not in [lo]:
                            lo[key] = val
                    select_field=ref_attribute.SelectedField
                    ref_attribute=ref_attribute.Ref_Attribute
                ss[a.Attribute]=select_field
            else:
                ss[a.Attribute]=a.SelectedField


    if len(ss)>0:
        co=','
    else:
        co=''

    calcfields=get_calulatedfieldlist(Class_id)
    for cf in calcfields:
        for key,val in ss.items():
            if ('"'+key+'"') in ss[cf.Attribute]:
                ss[cf.Attribute]=ss[cf.Attribute].replace('"'+key+'"',val)

    sselect = 'select ' + ',\n'.join(["{f}  as {di}{a}{di}".format(f=ss[i],a=i,di=Default_Identifier) for i in ss ])
    sfrom='from ' + '\n'.join(lo.values())
    ins_condition=''
    if Instance_id!=0:
        ins_condition=' and ins."id"={}'.format(Instance_id)
    swhere = """ 
    where ins."Class_id"={Class_id} {instance}
    and 
    (exists (select * from "ut_classes_ViewGroups" vg, auth_user_groups ug where vg.group_id=ug.group_id and user_id = {user_id})
    or 
    ins."Owner_id"={user_id}
    or
    exists (select * from auth_user where id = {user_id} and is_superuser={true})
    )
    """.format(Class_id=Class_id, user_id=user_id,instance=ins_condition,true='true')
    sql=sselect +'\n' + sfrom + '\n' + swhere
    return {'sql':sql,'columns':ss.keys(),'selectfields':ss.values(),'ajax_columns':ajax_columns}

def get_value(Instance_id,Attribute_id):
    DataType=Attributes.objects.get(pk=Attribute_id).DataType.id
    if Instance_id == 0:
        value=''
    else:
        if not Values.objects.filter(Instance_id=Instance_id,Attribute_id=Attribute_id).exists():
            value = ''
        else:
            v = Values.objects.get(Instance_id=Instance_id, Attribute_id=Attribute_id)
            if DataType == DT_Integer:
                value=v.int_value
            elif DataType in [DT_Float,DT_Currency]:
                value=v.float_value
            elif DataType in [DT_String,DT_Email,DT_Time]:
                value=v.char_value
            elif DataType in [DT_Text,DT_Hyperlink]:
                value=v.text_value
            elif DataType in (DT_Date,DT_Datetime):
                value=v.datetime_value
            elif DataType == DT_Instance:
                if pd.isnull(v.instance_value):
                    value=0
                else:
                    value=v.instance_value.id
            elif DataType == DT_Lookup:
                value = ''
            elif DataType == DT_Boolean:
                value=v.int_value
            else:
                raise ('Wrong DataType')
    return value

def qs_to_table(qs,m,url,args=[A('pk'),]):
    class h_table(tables.Table):
        h_link = tables.LinkColumn(url, text= 'edit', args=args, orderable=False)
        class Meta:
            model=m
    return h_table(qs)

def save_attribute(Instance_id,Attribute_id,value,passed_by_name=False):
    t0=datetime.now()
    #print (t0,'internal save')
    at=Attributes.objects.get(pk=Attribute_id)
    DataType = at.DataType.id
    #print (datetime.now()-t0, 'after get attribute')
    if DataType==DT_ManyToMany:
        if type(value)==list:
            int_values = [int(i) for i in value]
            #get all available values
            old_values = list(Values_m2m.objects.filter(Instance_id=Instance_id, Attribute_id=Attribute_id).values_list('instance_value_id',flat=True))
            for i in int_values:
                if not i in old_values:
                    vm=Values_m2m(Instance_id=Instance_id,Attribute_id=Attribute_id,instance_value_id=i)
                    vm.save()
            for old_i in old_values:
                if not old_i in int_values:
                    Values_m2m.objects.get(Instance_id=Instance_id,Attribute_id=Attribute_id,instance_value_id=old_i).delete()
    else:
        defaults={}
        if pd.isnull(value):
            val = ''
        else:
            val = value

        if DataType in [DT_Integer,DT_Boolean]: #int
            if val=='':
                val=None
            defaults={'int_value':val}
        elif DataType in [DT_Float,DT_Currency]: #float, currency
            if val=='':
                val=None
            defaults={'float_value':val}
        elif DataType in [DT_String,DT_Email]: #char,email
            if val=='':
                val=None
            defaults={'char_value':val}
        elif DataType in [DT_Text,DT_Hyperlink]: #text
            if val=='':
                val=None
            defaults={'text_value':val}
        elif DataType in [DT_Date,DT_Datetime] : #date,datetime
            if val!='':
                tz=timezone.utc #!!!need to set up timezone here
                val=pd.to_datetime(val)
                if val.tzinfo is None:
                    val=tz.localize(val)
            else:
                val=None
            defaults={'datetime_value':val}
        elif DataType in [DT_Time]: #time only
            if val!='':
                val=val.strftime('%H:%M:%S')
            else:
                val=None
            defaults={'char_value':val}
        elif DataType in [DT_File,DT_Image]:
            if val:
                defaults={'file_value':val}
            else:
                defaults={'file_value':None}
        elif DataType == DT_Instance: #instance
            if val=='':
                val = None
            else:
                if passed_by_name:
                    ref_class=at.Ref_Class.id
                    ref_attr= at.Ref_Attribute.id
                    if ref_attr==Default_Attribute:
                        val=Instances.objects.get(Class_id=ref_class,Code=value).id
                    else:
                        val=Values.objects.get(Attribute_id=ref_attr,char_value=value).Instance.id
            defaults={'instance_value_id':val}
        #print(datetime.now() - t0, 'before save')
        if DataType in [DT_File,DT_Image]:
            Values_files.objects.update_or_create(Instance_id=Instance_id, Attribute_id=Attribute_id, defaults=defaults)
        else:
            Values.objects.update_or_create(Instance_id=Instance_id, Attribute_id=Attribute_id, defaults=defaults)
        #print(datetime.now() - t0, 'after save',at.Attribute)

def df_to_table(df):
    class t(tables.Table):
        class Meta:
            fields=list(df.columns)
    table=t(df.to_dict('records'))
    return table

def get_val_by_name(key,d={}):
    if key in d.keys():
        res=d[key]
    else:
        res=''
    return res

#this procedure creates a filter for the query that will be executed on the server
def create_filter_for_sql(Class_id,filter={},masterclassfilter={}):
    d={FT_Exact:'FT_Exact',FT_Contains:'FT_Contains',FT_Like:'FT_Like'}
    where = ''
    for key,val in filter.items():
        type = ''
        if '__min__' in key:
            name=key[7:]
            type='FT_Min'
        elif '__max__' in key:
            name=key[7:]
            type='FT_Max'
        else:
            name=key

        f=get_filter(Class_id=Class_id,FilterName=name)
        if type=='':
            type=d[f.FilterType]
        #
        if val!='' and (not (val=='-1' and f.Attribute1.DataType.id==6)):
            where = where + f.Expression[type].format(val=val)

    for key,val in masterclassfilter.items():
        attr=Attributes.objects.filter(Class_id=Class_id,DataType_id=DT_Instance,Attribute=key)
        tab = attr[0].TableName
        where = where + ' and  {}.instance_value_id={}'.format(tab,val)

    return where

def get_next_counter(Class_id):
    res = ''
    if Classes.objects.get(pk=Class_id).UseAutoCounter:
        try:
            Counter=Counters.objects.get(Class_id=Class_id)
        except:
            Counter=Counters(Class_id=Class_id)

        pref=Counter.Class.Prefix
        cno =Counter.Class.CounterStrLen
        Counter.CurrentCounter+=1
        Counter.save()
        next= Counter.CurrentCounter
        res= pref + str(next).rjust(cno,'0')
    return res

def get_formlayout(Class_id):
    try:
        res=Layouts.objects.get(Class_id=Class_id).form_dict
    except Layouts.DoesNotExist:
        res={'settings':{},'layout':[]}
        a=Layouts(Class_id=Class_id,FormLayout=json.dumps(res))
        a.save()
    return res

a="""
def get_column(Class_id,col_name,Instance_id=0,type='FORM'):
    if type=='FORM':
        fl = Classes.objects.get(pk=Class_id).editlist
        if (len(fl)>0):
            pass
            #fl['Control']=fl.id.apply(lambda x: create_control(Instance_id,x))
        formlo=get_formlayout(Class_id)
    else:
        fl = Classes.objects.get(pk=Class_id).fulllist
        formlo=get_tablelayout(Class_id)

    res=pd.DataFrame()
    for f in formlo[col_name].split(','):
        if (f.strip()!='')&(f.strip()<='9'):
            id=int(f.strip())
            res=res.append(fl[fl.id==id])
    return res
"""

def raw_queryset_as_values_list_old(raw_qs):
    columns = raw_qs.columns
    for row in raw_qs:
        yield tuple( getattr(row, col) for col in columns )

def raw_queryset_as_values_list(raw_qs):
    columns = raw_qs.columns
    res=[]
    for row in raw_qs:
        res.append(tuple( getattr(row, col) for col in columns ))
    return res

def raw_queryset_as_dict(sql):
    res=[]
    #columns = raw_qs.columns
    rocon=connections['readonly']
    with rocon.cursor() as cursor:
        cursor.execute(sql)
        columns=cursor.description
        res = dictfetchall(cursor)
    return res

@transaction.atomic
def save_instance_byid(Class_id,instance={}):
    #Class_id=Instances.objects.get(pk=Instance_id).Class.id
        code=instance['Code']
        Instance_id=instance['Instance_id']
        if Instance_id==0:
            ins=Instances(Class_id=Class_id,Code=code)
        else:
            ins=Instances.objects.get(pk=Instance_id)
            ins.Code=code
        ins.save()
        fl=get_updatefieldlist(Class_id)
        for rec in fl:
            if str(rec.id) in instance.keys():
                save_attribute(ins.id,rec.id,instance[str(rec.id)])
        return True

def get_difference(new={},old={},key_list=[]):
    diff={}
    for key,val in new.items():
        if key in key_list:
            if val=='':
                new_val=None
            else:
                new_val=val
            old_val = old.get(key)
            if old_val == '':
                old_value=None
            date_equal=False
            if isinstance(new_val, date) and pd.notnull(old_val):
                if isinstance(old_val,datetime):
                    date_equal=old_val.date()==new_val
                else:
                    date_equal=old_val==new_val
            elif isinstance(new_val, time):
                date_equal=old_val==str(new_val)
            equal = (old_val==new_val) or date_equal or (pd.isnull(old_val) and pd.isnull(new_val))
            if not equal:
                diff[key]=new_val
    return diff

def save_instance_byname(Class_id,Instance_id=0,instance={},safe=False,passed_by_name=True):
    #print (instance)
    event = evUPDATE
    with transaction.atomic():
        res=False
        if not safe:
            user = get_current_user()
        else:
            user = User.objects.get(pk=1)

        cl=Classes.objects.get(pk=Class_id)
        fl=get_updatefieldlist(Class_id)
        upd_attributes=dict((x.Attribute,x.pk) for x in fl)
        keys_list=upd_attributes.keys()
        if Instance_id==0:
            old_instance={}
        else:
            old_instance = get_instance_values(Class_id, Instance_id)
        for_update=get_difference(instance,old_instance,keys_list)
        if for_update=={}:
            return Instance_id
        else:
            code=instance.get('Code')
            if code=='':
                code=None
            if (Instance_id==0) and (passed_by_name) and pd.isnull(code):
                code=get_next_counter(Class_id)
        #    Instance_id
            if Instance_id==0:
                ins=Instances(Class_id=Class_id,Code=code,Owner=user)
            else:
                ins=Instances.objects.get(pk=Instance_id)
                if for_update.get('Code'):
                    ins.Code=code
                    for_update.pop('Code')
            ins.Updated=datetime.now(tz=timezone.utc)
            if user:
                ins.Updatedby=user
            ins.save(safe=safe)
            res=ins.id
            for name,value in for_update.items():
                save_attribute(ins.id,upd_attributes[name],value,passed_by_name=passed_by_name)
        try:
            memory_cache.set('instance-values-{}'.format(Instance_id),instance)
        except:
            print ("memory_cache has not been saved")
    if Instance_id == 0:
        event=evINSERT
    try:
        call_class_event(Class_id,event,pk=res,instance=instance,changes=for_update)
    except:
        raise
    return res

def call_class_event(Class_id,event=evINSERT,pk=None,instance={},changes={}):
    cl=Classes.objects.get(pk=Class_id)
    if event==evINSERT:
        if cl.OnInsertEvent:
            ev = UtParser()
            ev['pk'] = pk
            ev['instance'] = instance
            ev['changes']  = changes
            res=ev.evaluate(cl.OnInsertEvent)
    elif event==evUPDATE:
        if cl.OnUpdateEvent:
            ev = UtParser()
            ev['pk'] = pk
            ev['instance'] = instance
            ev['changes']  = changes
            res=ev.evaluate(cl.OnUpdateEvent)

def dictfetchall(cursor):
    #Return all rows from a cursor as a dict
    columns = [col[0] for col in cursor.description]
    return [
       dict(zip(columns, row))
       for row in cursor.fetchall()
    ]

def get_report_df(Report_id,filter={}):
    r = Reports.objects.get(pk=Report_id)
    sql = r.Query
    if len(filter)>0:
        sql_filter= 'where '+' and '.join([ ('cast("{}"'+" as varchar)='{}'").format(i,k) for i,k in filter.items()])
        sql = 'select * from ({sql}) as full_report {filter}'.format(sql=sql,filter=sql_filter)
    df = pd.read_sql(sql,connections['readonly'])
    return {'df': df,'ReportName':r.Report}

def get_reporttable(Report_id):
    r = Reports.objects.get(pk=Report_id)
    sql = r.Query
    rocon=connections['readonly']
    cursor = rocon.cursor()
    cursor.execute(sql)
    t = dictfetchall(cursor)
    extra_columns = [(c[0], tables.Column()) for c in cursor.description]
    return {'table': ReportTable(data=t,extra_columns=extra_columns),
            'ReportName':r.Report}

def get_parent_classes(Class_id):
    res=[Class_id]
    pid=Class_id
    while pid!=Default_Class:
        pid=Classes.objects.get(pk=pid).Parent_id
        res.append(pid)
    return res

