from ut.models import *
from ut.models import *
import django_tables2 as tables
import pandas as pd
from .tables import ReportTable
from django_pandas.io import read_frame
import numpy as np
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from django_tables2.utils import A

from django.apps import apps
app_models = apps.get_app_config('ut').get_models()
am=pd.DataFrame()
for a in app_models:
    am = am.append({'TableName': a._meta.verbose_name, 'Table': a},ignore_index=True)  # .to_dict()

from django.db import connection
con=connection
df_classes=pd.DataFrame()#pd.read_sql('select * from ut_classes',con) #.set_index('id')
df_attributes=pd.DataFrame()#pd.read_sql('select * from ut_attributes',con)#.set_index('id')
df_datatypes=pd.DataFrame()#pd.read_sql('select * from ut_datatypes',con) #.set_index('id')
df_inputtypes=pd.DataFrame()#pd.read_sql('select * from ut_inputtypes',con) #.set_index('id')
df_formlayouts=pd.read_sql('select * from ut_formlayouts',con) #.set_index('id')
df_filters=pd.DataFrame()

select_options_sql="""
select 
i.id, i.Code,v2.char_value from ut_instances i, ut_values v , ut_values v2
WHERE 
v.Instance_id=i.id and 
v2.Instance_id=i.id and
i.Class_id = {cl} and
v.instance_value_id={val} and
v2.Attribute_id={att} 
"""

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
    if id == 0:
        res[attribute] = 'ins.Code'
    elif dt == DT_Lookup:
            res[attribute] = '{tab}.{field}' \
                .format(tab=attr.RefAttrTableName, field=get_fieldname(DT_String))
    elif dt == DT_External:
        res[attribute] = '{tab}.{field}'.format(tab=attr.ExternalTable, field=attr.ExternalField)
    elif dt in [DT_Table]:
        res[attribute] = '0 as Table__' + str(id) + '__'
    elif dt in [DT_Calculated]:
        res[attribute] = '{formula}'.format(formula=attr.Formula)
    else:
        res[attribute] = '{tab}.{field}'.format(tab=attr.TableName, id=id,field=get_fieldname(dt))
    return res


def valuefield(id,df_attr):
    attr=df_attr[df_attr.id==id].iloc[0]
    dt= attr.DataType_id
    attribute=attr.Attribute
    ref_attribute_id=attr.Ref_Attribute_id
    res = {}
    if id == 0:
        res[attribute] = 'ins.Code'
    elif dt == DT_Lookup:
            res[attribute] = '{tab}.{field}' \
                .format(tab=attr.RefAttrTableName, field=get_fieldname(DT_String))
    elif dt == DT_External:
        res[attribute] = '{tab}.{field}'.format(tab=attr.ExternalTable, field=attr.ExternalField)
    elif dt in [DT_Table]:
        res[attribute] = '0 as Table__' + str(id) + '__'
    elif dt in [DT_Calculated]:
        res[attribute] = '{formula}'.format(formula=attr.Formula)
    else:
        res[attribute] = '{tab}.{field}'.format(tab=attr.TableName, id=id,field=get_fieldname(dt))
    return res

def selectfield(id,df_attr):
    attr=df_attr[df_attr.id==id].iloc[0]
    dt= attr.DataType_id
    attr=df_attr[df_attr.id==id].iloc[0]
    ref_attr = df_attr[df_attr.id==attr.Ref_Attribute_id].iloc[0]
    internal_attr = df_attr[df_attr.id==attr.InternalAttribute_id].iloc[0]

    attribute=attr.Attribute
    ref_attribute_id=attr.Ref_Attribute_id

    res = {}
    if id==0:
        res[attribute] = 'ins.Code'
    elif dt == DT_Instance:
        if ref_attribute_id == 0:
            res[attribute] = '{tab}.{field}'.format(tab=attr.RefTableName, field='"Code"')
        else:
            res[attribute] = '{tab}.{field}' \
                .format(tab=attr.RefAttrTableName, field=get_fieldname(ref_attr.DataType_id))
    elif dt == DT_Lookup:
            res[attribute] = '{tab}.{field}' \
                .format(tab=attr.RefAttrTableName, field=get_fieldname(DT_String))
    elif dt == DT_External:
        res[attribute] = '{tab}.{field}'.format(tab=attr.ExternalTable, field=attr.ExternalField)
    elif dt in [DT_Table]:
        res[attribute] = '0 as Table__' + str(id) + '__'
    elif dt in [DT_Calculated]:
        res[attribute] = '{formula}'.format(formula=attr.Formula)
    else:
        res[attribute] = '{tab}.{field}'.format(tab=attr.TableName, id=id,field=get_fieldname(dt))
    return res

def valueleftouter(id,df_attr):
    attr=df_attr[df_attr.id==id].iloc[0]
    dt= attr.DataType_id
    ref_attr = df_attr[df_attr.id==attr.Ref_Attribute_id].iloc[0]
    internal_attr = df_attr[df_attr.id==attr.InternalAttribute_id].iloc[0]

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

def leftouter(id,df_attr):
    attr=df_attr[df_attr.id==id].iloc[0]
    dt= attr.DataType_id
    ref_attr = df_attr[df_attr.id==attr.Ref_Attribute_id].iloc[0]
    internal_attr = df_attr[df_attr.id==attr.InternalAttribute_id].iloc[0]

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
            if attr.Ref_Attribute_id!=0:
                res[attr.RefAttrTableName] = 'LEFT OUTER JOIN {val} as {refval} ON ({refval}.Instance_id = {reftab}.id and {refval}.Attribute_id = {refatt}) --{attr}'\
                    .format(val=Values._meta.db_table,refval=attr.RefAttrTableName,refatt=attr.Ref_Attribute_id,reftab=attr.RefTableName,attr=attr.Attribute)

    return res

def calculated(dt):
    if dt in [DT_External,DT_Calculated]:
        return True
    else:
        return False

def get_options(Attribute_id=0,values={}) :
    attr=get_attribute(Attribute_id,df_attributes)
    instances={}
    if attr.MasterAttribute_id > 0:
        m_attr=get_attribute(attr.MasterAttribute_id,df_attributes)
        tmp=values.get(m_attr.Attribute)
        if pd.notnull(tmp):
            m_value=int(tmp)
        else:
            m_value=0

        if attr.Ref_Attribute_id == 0:
            for r in Values.objects.filter(instance_value_id=m_value,Instance__Class__id=attr.Ref_Class_id):
                instances[r.Instance_id]=r.Instance.Code
        else:
            for r in Instances.objects.raw(select_options_sql.format(val=m_value  ,cl=attr.Ref_Class_id,att=attr.Ref_Attribute_id)):
                instances[r.id]=r.char_value
    else:
        if attr.Ref_Attribute_id == 0:
            for r in Instances.objects.filter(Class_id=attr.Ref_Class_id):
                instances[r.id]=r.Code
        else:
            for r in Values.objects.filter(Attribute_id=attr.Ref_Attribute_id):
                instances[r.Instance_id]=r.char_value
    return instances

from django import forms
from bootstrap_datepicker_plus import DatePickerInput,DateTimePickerInput,TimePickerInput

def create_form_field_check(attr):
    dt = attr.DataType_id
    if dt in [DT_Calculated,DT_Table]:
        res=False
    else:
        res=True
    return res

def create_form_field(attr,usedinfilter=False,filter={},readonly=False,values={},fn=''):
    if fn == '':
        FieldName=attr.Attribute
    else:
        FieldName=fn
    dt=attr.DataType_id
    if usedinfilter:
        req=False
    else:
        req=attr.NotNullAtt
    valueslist=attr.ValuesList
    vl=''
    if pd.isnull(valueslist) or (valueslist == ''):
        vl = ''
    else:
        try:
            vl=json.loads(valueslist)
        except:
            print ('Could not load list of values for field',FieldName,'Class =',attr.Class_id)
    if dt in [DT_Integer]:
        if vl=='':
            field=forms.IntegerField(required=req)
        else:
            field=forms.ChoiceField(choices=vl,required=req)
    elif dt in [DT_Float]:
        if vl=='':
            field = forms.FloatField(required=req)
        else:
            field=forms.ChoiceField(choices=vl,required=req)
    elif dt in [DT_String,DT_Lookup]:
        if vl=='':
            field = forms.CharField(max_length=255, required=req)
        else:
            field=forms.ChoiceField(choices=vl,required=req)
    elif dt in [DT_Text]:
        field=forms.CharField(widget=forms.Textarea(attrs={'rows':1}),required=req)
    elif dt in [DT_Date]:
        field=forms.DateField(required=req, input_formats=['%Y-%m-%d','%m/%d/%Y','%m/%d/%y'],
                              widget=DatePickerInput(format='%Y-%m-%d')
        )
    elif dt in [DT_Datetime]:
        field=forms.DateTimeField(required=req, input_formats=['%Y-%m-%d %H:%M','%m/%d/%Y %H:%M','%m/%d/%y %H:%M'],
                              widget=DateTimePickerInput(format='%Y-%m-%d %H:%M')
        )
    elif dt in [DT_Time]:
        field = forms.TimeField(required=req, input_formats=['%H:%M'],
                                    widget=DateTimePickerInput(format='%H:%M')
                                    )
    elif dt in [DT_Instance]:
        op=get_options(Attribute_id=attr.id,values=values)
        if usedinfilter:
            ch=[(-1,'(All)')]
        else:
            ch=[]
        ch=ch+[(0,'(None)')]+[(k, v) for k, v in op.items()]
        field=forms.ChoiceField(choices=ch,required=req)
    elif dt == [DT_Datetime]:
        field = forms.DateTimeField(required=req)
    elif dt == DT_Boolean: #boolean
        field=forms.ChoiceField(choices=[(0,'False'),(1,'True')],required=req)
    elif dt == DT_Table: #list Do not use
        return False
    elif dt in [DT_Currency]: #Currency
        field = forms.FloatField(required=req)
    elif dt in [DT_Email]: #Email
        if not usedinfilter:
            field = forms.EmailField(required=req)
        else:
            field = forms.CharField(max_length=255,required=req)
    elif dt == DT_Calculated:
        return False
    else:
        print ('this exception')
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

def set_attributes():
    old_sql_to_delete = """
    select at.*, mat.id as MasterAttribute_id, dcl.id as dependancies
    from ut_attributes at, ut_classes cl
    left outer join ut_attributes mat on (mat.DataType_id=6 and mat.Class_id=at.Class_id and mat.Ref_Class_id=cl.Master_id and mat.Ref_Class_id<>0)
    left outer join ut_classes dcl on (dcl.Master_id=at.Ref_Class_id and dcl.Master_id<>0)
    where at.Ref_Class_id=cl.id
    """

    at_sql="select * from ut_attributes"
    cl_sql="select * from ut_classes"

    df_attr = pd.read_sql(at_sql, con)
    df_cl   = pd.read_sql(cl_sql, con)

    df_attr = pd.merge(df_attr, df_cl[['id', 'Master_id']].rename(columns={'id':'Ref_Class_id'}),
                       on='Ref_Class_id', how='inner')

    df_attr_ref=df_attr.loc[(df_attr.DataType_id==DT_Instance)&(df_attr.Ref_Class_id!=0),['id','Class_id','Ref_Class_id']].rename(
                columns={'id':'MasterAttribute_id','Ref_Class_id':'Master_id'})

    df_attr = pd.merge(df_attr,df_attr_ref,on=['Class_id','Master_id'],how='left').astype({'MasterAttribute_id':'Int64'})

    dependancies=df_attr[(df_attr.MasterAttribute_id!=0)&(df_attr.DataType_id==DT_Instance)].groupby(['MasterAttribute_id']).agg({'id': 'max'})\
        .reset_index().rename(columns={'MasterAttribute_id':'id','id':'hierarchy_trigger'})
    df_attr = pd.merge(df_attr,dependancies,on=['id'],how='left')

    lookups = df_attr[(df_attr.DataType_id==DT_Lookup)&(df_attr.InternalAttribute_id!=0)]\
        .groupby('InternalAttribute_id').agg({'id':'max'}).reset_index()\
        .rename(columns={'id':'lookup_trigger','InternalAttribute_id':'id'})

    df_attr = pd.merge(df_attr,lookups,on='id',how='left')

    df_attr['TableName']=df_attr.id.apply(lambda x: '"val{}"'.format(x))

    df_attr['RefTableName']=df_attr.id.apply(lambda x: '"val_ins{}"'.format(x))
    df_attr['RefAttrTableName']=df_attr.id.apply(lambda x: '"refval{}"'.format(x))

    df_attr['SelectField']=df_attr.id.apply(lambda x: selectfield(x,df_attr))
    df_attr['ValueField']=df_attr.id.apply(lambda x: valuefield(x,df_attr))

    df_attr['LeftOuter'] = df_attr.id.apply(lambda x: leftouter(x,df_attr))
    df_attr['ValueLeftOuter']=df_attr.id.apply(lambda x: valueleftouter(x,df_attr))

    df_attr['Calculated'] = df_attr.DataType_id.apply(lambda x: calculated(x))
    df_attr['TableColumn']=df_attr.apply(lambda x: tables.Column )
    df_attr['MasterAttribute_id']=df_attr['MasterAttribute_id'].apply(lambda x:  0 if pd.isnull(x) else int(x))

    df_attr['FT_Exact']=df_attr.apply(lambda x: x.ValueField[x.Attribute]+ '=' + filter_value(x),axis=1)
    df_attr['FT_Contains'] = df_attr.apply(lambda x: x.ValueField[x.Attribute]+ " like '%{val}%'",axis=1)
    df_attr['FT_Like']= df_attr.apply(lambda x: x.ValueField[x.Attribute]+ " like '{val}'",axis=1)
    df_attr['FT_Min'] = df_attr.apply(lambda x: x.ValueField[x.Attribute]+ '>=' + filter_value(x),axis=1)
    df_attr['FT_Max'] = df_attr.apply(lambda x: x.ValueField[x.Attribute]+ '<=' + filter_value(x),axis=1)

    return df_attr


att_columns=['id','DataType_id','FT_Exact','FT_Contains','FT_Like','FT_Min','FT_Max']
filter_expression_columns=['FT_Exact','FT_Contains','FT_Like','FT_Min','FT_Max']
def make_filter_expression(f):
    res={}
    for ft in filter_expression_columns:
        expr =  f[ft]
        if f.Attribute2_id !=0:
            expr = expr + ' ' + f.Condition1 + ' ' + f[ft+'_at2']
        if f.Attribute3_id !=0:
            expr = expr + ' ' + f.Condition2 + ' ' + f[ft+'_at3']
        res[ft] = ' and ('+expr+')'
    return res

def set_filters():
    ft_sql="select * from ut_filters"
    df_filters=pd.read_sql(ft_sql, con)
    df_filters = pd.merge(df_filters,df_attributes[att_columns],left_on='Attribute1_id',right_on='id',how='left',suffixes=['','_at1'])
    df_filters = pd.merge(df_filters,df_attributes[att_columns],left_on='Attribute2_id',right_on='id',how='left',suffixes=['','_at2'])
    df_filters = pd.merge(df_filters,df_attributes[att_columns],left_on='Attribute2_id',right_on='id',how='left',suffixes=['','_at3'])
    df_filters['Expression']=df_filters.apply(lambda x: make_filter_expression(x),axis=1)
    return df_filters

def get_filter(Filter_id=-1,Class_id=0,FilterName=''):
    if Filter_id!=-1:
        res=df_filters[df_filters.id==Filter_id].iloc[0]
    else:
        res=df_filters[df_filters.Class_id.isin([Class_id,0])&(df_filters.Filter==FilterName)].iloc[0]
    return res

def get_attribute(id,df_attr=df_attributes):
    return df_attr[df_attr.id==id].iloc[0]

def get_editfieldlist(Class_id,df_attr):
    return df_attr[df_attr.Class_id.isin([Class_id,0])&(~df_attr.Calculated)]

def get_calulatedfieldlist(Class_id,df_attr):
    return df_attr[(df_attr.Class_id==Class_id)&(df_attr.DataType_id==DT_Calculated)]

def get_tableviewlist(Class_id,df_attr):
    return df_attr[df_attr.Class_id.isin([Class_id,0])&(~df_attr.DataType_id.isin([10]))]

def get_fulllist(Class_id,df_attr):
    return df_attr[df_attr.Class_id.isin([Class_id,0])]

def create_rawquery_sql(Class_id=0,filter={}):
    return create_qs_sql(Class_id) + '\n' + create_filter_for_sql(Class_id, filter)

def create_rawquery_from_attributes(Class_id=0,filter={}):
    sql=create_rawquery_sql(Class_id,filter)
    qs=Instances.objects.raw(sql)
    return qs

def get_qs_instance_sql():
    pass

def create_val_sql(Instance_id,Class_id):
    atts=get_tableviewlist(Class_id=Class_id,df_attr=df_attributes)
    #print (atts)
    ss = {}
    lo = {}
    for i,a in atts.iterrows():
        if a.id != 0:
            for key,val in a.ValueField.items():
                ss[key]=val
            for key,val in a.ValueLeftOuter.items():
                lo[key]=val
    if len(ss)>0:
        co=','
    else:
        co=''
    calcfields=get_calulatedfieldlist(Class_id,df_attributes)
    for i,cf in calcfields.iterrows():
        for key,val in ss.items():
            if ('"'+key+'"') in ss[cf.Attribute]:
                ss[cf.Attribute]=ss[cf.Attribute].replace('"'+key+'"',val)
    #print (ss)

    sselect = 'select ins.id, ins.Code' +co + ',\n'.join(['{}  as "{}"'.format(ss[i],i) for i in ss ])
    sfrom='from {ins} ins\n'.format(ins=Instances._meta.db_table) +'\n'.join(lo.values())
    swhere = 'where ins.id={}'.format(Instance_id)
    return sselect +'\n' + sfrom + '\n' + swhere


def create_qs_sql(Class_id):
    atts=get_tableviewlist(Class_id=Class_id,df_attr=df_attributes)
    #print (atts)
    ss = {}
    lo = {}
    for i,a in atts.iterrows():
        if a.id != 0:
            for key,val in a.SelectField.items():
                ss[key]=val
            for key,val in a.LeftOuter.items():
                lo[key]=val
    if len(ss)>0:
        co=','
    else:
        co=''

    calcfields=get_calulatedfieldlist(Class_id,df_attributes)
    for i,cf in calcfields.iterrows():
        for key,val in ss.items():
            if ('"'+key+'"') in ss[cf.Attribute]:
                ss[cf.Attribute]=ss[cf.Attribute].replace('"'+key+'"',val)
    #print (ss)

    sselect = 'select ins.id, ins.Code' +co + ',\n'.join(['{}  as "{}"'.format(ss[i],i) for i in ss ])
    sfrom='from {ins} ins\n'.format(ins=Instances._meta.db_table) +'\n'.join(lo.values())
    swhere = 'where ins.Class_id={}'.format(Class_id)
    return sselect +'\n' + sfrom + '\n' + swhere

b=""""
def create_queryset_from_attributes(Class_id):
    qs=Instances.objects.filter(Class_id=Class_id)
    sselect={}
    sfrom  =[]
    swhere= []
    fl=fieldlist(Class_id)
    for i,rec in fl.iterrows():
        if   rec.DataType_id==1:
            vfield_name='int_value'
        elif rec.DataType_id==2:
            vfield_name='float_value'
        elif rec.DataType_id ==3:
            vfield_name='char_value'
        elif rec.DataType_id==4:
            vfield_name='text_value'
        elif rec.DataType_id==5:
            vfield_name='datetime_value'
        elif rec.DataType_id==6:
            vfield_name='instance_value_id'
        sselect[rec.Attribute] = 'val'+str(rec.id)+'.'+ vfield_name
        sfrom.append('"ut_values" as "'+'val'+str(rec.id)+'"')
        swhere.append('val'+str(rec.id)+'.Instance_id="ut_instances".id and val'+str(rec.id)+'.Attribute_id='+str(rec.id))

    return qs.extra(select=sselect,tables=sfrom,where=swhere)
"""

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
            elif DataType in (DT_String,DT_Email,DT_Time):
                value=v.char_value
            elif DataType == DT_Text:
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
    if pd.isnull(value):
        val=''
    else:
        val=value
    at=Attributes.objects.get(pk=Attribute_id)
    DataType = at.DataType.id
    if not Values.objects.filter(Instance_id=Instance_id,Attribute_id=Attribute_id).exists():
        v = Values(Instance_id=Instance_id,Attribute_id=Attribute_id)
    else:
        v = Values.objects.get(Instance_id=Instance_id,Attribute_id=Attribute_id)
    if DataType == DT_Integer: #int
        if val!='':
            v.int_value=int(val)
        else:
            v.int_value=None
    elif DataType in [DT_Float,DT_Currency]: #float, currency
        if val!='':
            v.float_value=float(val)
        else:
            v.float_value=None
    elif DataType in [DT_String,DT_Email]: #char,email
        if val!='':
            v.char_value=val
        else:
            v.char_value=None
    elif DataType == DT_Text: #text
        if val!='':
            v.text_value=val
        else:
            v.text_value=None
    elif DataType in [DT_Date,DT_Datetime] : #date,datetime
        if val!='':
            v.datetime_value=val
        else:
            v.datetime_value=None
    elif DataType in [DT_Time]: #time only
        if val!='':
            val=val.strftime('%H:%M:%S')
            v.char_value=val
        else:
            v.char_value=None
    elif DataType == DT_Instance: #instance
        if val=='':
            v.instance_value = None
        else:
            if passed_by_name:
                ref_class=Attributes.objects.get(pk=Attribute_id).Ref_Class.id
                ref_attr=Attributes.objects.get(pk=Attribute_id).Ref_Attribute.id
                if ref_attr==0:
                    val=Instances.objects.get(Class_id=ref_class,Code=value).id
                else:
                    val=Values.objects.get(Attribute_id=ref_attr,char_value=value).Instance.id
            try:
                v.instance_value=Instances.objects.get(pk=int(val))
            except Instances.DoesNotExist:
                v.instance_value=None
    elif DataType == DT_Boolean: #boolean
        if val!='':
            v.int_value=int(val)
        else:
            v.int_value=None
    v.save()

def fieldlist(Class_id):
    output = pd.read_sql('select * from ut_attributes where Class_id={}'.format(Class_id),con)
    #output = df_attributes[df_attributes.Class_id==Class_id] #read_frame(Attributes.objects.filter(Class_id=Class_id))
    return output

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
def create_filter_for_sql(Class_id,filter={}):
    print (filter)
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
        print (f.Expression,f.Expression[type])
        if val!='' and (not (val=='-1' and f.DataType_id==6)):
            where = where + f.Expression[type].format(val=val)
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
        #print (res)
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

def raw_queryset_as_values_list(raw_qs):
    columns = raw_qs.columns
    for row in raw_qs:
        yield tuple( getattr(row, col) for col in columns )

def raw_queryset_as_dict(raw_qs):
    res=[]
    columns = raw_qs.columns
    for row in raw_qs:
        r={}
        for col in columns:
            r[col]=getattr(row,col)
        res.append(r)
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
        fl=get_editfieldlist(Class_id,df_attributes)
        for index,rec in fl.iterrows():
            if str(rec.id) in instance.keys():
                save_attribute(ins.id,rec.id,instance[str(rec.id)])
        return True

@transaction.atomic
def save_instance_byname(Class_id,Instance_id=0,instance={},passed_by_name=True):
    #Class_id=Instances.objects.get(pk=Instance_id).Class.id
    code=instance['Code']
    print ('class_id=',Class_id,'Instance=',Instance_id,instance)
    if code=='':
        code=None
    if (Instance_id==0) and (passed_by_name) and pd.isnull(code):
        code=get_next_counter(Class_id)
#    Instance_id
    if Instance_id==0:
        ins=Instances(Class_id=Class_id,Code=code)
        ins.save()
    else:
        ins=Instances.objects.get(pk=Instance_id)
        ins.Code=code
        ins.save()
    fl=get_editfieldlist(Class_id,df_attributes)
    for index,rec in fl.iterrows():
        name=Attributes.objects.get(pk=rec.id).Attribute
        if name in instance.keys() and (index!=0):
            save_attribute(ins.id,rec.id,instance[name],passed_by_name=passed_by_name)
    return True

def dictfetchall(cursor):
    #Return all rows from a cursor as a dict
    columns = [col[0] for col in cursor.description]
    return [
       dict(zip(columns, row))
       for row in cursor.fetchall()
    ]

def get_report_df(Report_id):
    r = Reports.objects.get(pk=Report_id)
    sql = r.Query
    df = pd.read_sql(sql,con)
    return {'df': df,'ReportName':r.Report}

def get_reporttable(Report_id):
    r = Reports.objects.get(pk=Report_id)
    sql = r.Query
    cursor = con.cursor()
    cursor.execute(sql)
    t = dictfetchall(cursor)
    extra_columns = [(c[0], tables.Column()) for c in cursor.description]
    return {'table': ReportTable(data=t,extra_columns=extra_columns),
            'ReportName':r.Report}


df_attributes=set_attributes()
df_filters = set_filters()

from django.dispatch import receiver
@receiver(models.signals.post_save, sender=Attributes)
def update_attributes(sender, instance, **kwargs):
    global df_attributes
    global df_filters
    from .utclasses import set_attributes
    df_attributes=set_attributes()
    print ('Reset Attributes. ',instance.Attribute,'changed')
    df_filters = set_filters()











