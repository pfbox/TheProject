from ut.models import *
import django_tables2 as tables
import pandas as pd
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
#df_filters =pd.read_sql('select * from ut_filters',con)

from django_jinja_knockout.query import FilteredRawQuerySet

def create_table_column(dt,width=50,attr={}):
    if dt in [5]:
        res=tables.DateColumn(attrs={'th': {'width': width}})
    elif dt in [7]:
        res = tables.DateTimeColumn(attrs={'th': {'width': width}})
    else:
        res = tables.Column(attrs={'th': {'width': width}})
    return res

def selectfield(id,df_attr):
    attr=df_attr[df_attr.id==id].iloc[0]
    dt= attr.DataType_id
    attribute=attr.Attribute
    tablename=attr['TableName']
    externaltable=attr.ExternalTable
    externalfield=attr.ExternalField

    ref_attribute_id=attr.Ref_Attribute_id
    refattribute=df_attr[df_attr.id==ref_attribute_id].iloc[0]
    reftablename=refattribute.TableName
    refatttablename=refattribute.RefAttTableName
    refdt=refattribute.DataType_id
    res = {}
    if dt == 6:
        if ref_attribute_id == 0:
            res[attribute] = '{tab}.{field} as "{name}"'.format(tab=reftablename, field='"Code"',name=attribute)
        else:
            res[attribute] = '{tab}.{field} as "{name}"' \
                .format(tab=refatttablename, field=get_fieldname(refdt), name=attribute)
    elif dt == 8:
        res[attribute] = '{tab}.{field} as "{name}"'.format(tab=externaltable, field=externalfield,name=attribute)
    elif dt in [10]:
        res[attribute] = '0 as Table__' + str(id) + '__'
    else:
        res[attribute] = '{tab}.{field} as "{name}"'.format(tab=tablename, id=id,
                                                                 field=get_fieldname(dt), name=attribute)
    return res

def leftouter(id,df_attr):
    attr=df_attr[df_attr.id==id].iloc[0]
    dt= attr.DataType_id
    attribute=attr.Attribute
    tablename=attr['TableName']
    externaltable=attr.ExternalTable
    externaluq=attr.ExternalUq
    externalfield=attr.ExternalField
    internalattr=df_attr[df_attr.id==attr.InternalAttribute_id].iloc[0]
    ref_attribute_id=attr.Ref_Attribute_id
    refattribute=df_attr[df_attr.id==ref_attribute_id].iloc[0]
    reftablename=refattribute.TableName
    refatttablename=refattribute.RefAttTableName
    refdt=refattribute.DataType_id

    res={}
    if dt==8:
        res[externaltable] = 'LEFT OUTER JOIN {ext} as {ext} ON ({ext}.{uq}={loctab}.{locfield})'\
            .format(ext=externaltable,uq=externaluq,loctab=internalattr.TableName,locfield=get_fieldname(internalattr.DataType_id))
    else:
        res[tablename]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}.Instance_id=ins.id and {tab}.Attribute_id={id})'.format(val=Values._meta.db_table,tab=tablename,id=id)
        if dt == 6:
            res[reftablename]='LEFT OUTER JOIN {ins} as {reftab} ON ({reftab}.id={tab}.instance_value_id)'.format(ins=Instances._meta.db_table,tab=tablename,reftab=reftablename)
            if ref_attribute_id!=0:
                res[refatttablename] = 'LEFT OUTER JOIN {val} as {refval} ON ({refval}.Instance_id = {reftab}.id and {refval}.Attribute_id = {refatt})'\
                    .format(val=Values._meta.db_table,refval=refatttablename,refatt=ref_attribute_id,reftab=reftablename)

    return res

def calculated(dt):
    if dt==8:
        return True
    else:
        return False

from django import forms
from bootstrap_datepicker_plus import DatePickerInput

def create_form_field(attr,usedinfilter=False,filter={}):
    print ('create_form_field_called')
    FieldName=attr.Attribute
    dt=attr.DataType_id
    if usedinfilter:
        req=False
    else:
        req=attr.NotNullAtt
    valueslist=attr.ValuesList
    if pd.isnull(valueslist) or (valueslist == ''):
        vl = ''
    else:
        try:
            vl=json.loads(valueslist)
        except:
            print ('Could not load list of values for field',FieldName,'Class =',attr.Class_id)
    if dt == 1:
        if vl=='':
            field=forms.IntegerField(required=req)
        else:
            field=forms.ChoiceField(choices=vl,required=req)
    elif dt ==2:
        if vl=='':
            field = forms.FloatField(required=req)
        else:
            field=forms.ChoiceField(choices=vl,required=req)
    elif dt == 3:
        if vl=='':
            field = forms.CharField(max_length=255, required=req)
        else:
            field=forms.ChoiceField(choices=vl,required=req)
    elif dt == 4:
        field=forms.CharField(widget=forms.Textarea(attrs={'rows':1}),required=req)
    elif dt == 5:
        field=forms.DateField(required=req, input_formats=['%Y-%m-%d','%m/%d/%Y','%m/%d/%y'],
                              widget=DatePickerInput(format='%Y-%m-%d')
        )
    elif dt == 6:
        if attr.Ref_Class_id!=0:
            if attr.Ref_Attribute_id==0:
                ch=[(i.id,i.Code) for i in Instances.objects.filter(Class_id=attr.Ref_Class_id)]
            else:
                ch=[(v.Instance_id,v.char_value) for v in Values.objects.filter(Attribute_id=attr.Ref_Attribute_id)]
        else:
            raise Exception('No reference values for the attribute {}'.format(attr.Attribute))
        ch=[(0,'')]+ch
        field=forms.ChoiceField(choices=ch,required=req)
    elif dt == 7:
        field = forms.DateTimeField(required=req)
    elif dt == 9: #boolean
        field=forms.ChoiceField(choices=[(0,'False'),(1,'True')],required=req)
    elif dt == 10: #list Do not use
        return False
    elif dt == 11: #EmailField
        field=forms.EmailField(required=req)
    elif dt == 12: #Currency
        field=forms.FloatField(required=req)
    else:
        raise Exception('Datatype {} does not exists.'.format(dt))
    return field


def set_attributes():
    df_attr = pd.read_sql('select * from ut_attributes', con)
    df_attr['TableName']=df_attr.id.apply(lambda x: '"val{}"'.format(x))
    df_attr['RefTableName']=df_attr.id.apply(lambda x: '"val_ins{}"'.format(x))
    df_attr['RefAttTableName']=df_attr.id.apply(lambda x: '"refval{}"'.format(x))
    df_attr['SelectField']=df_attr.id.apply(lambda x: selectfield(x,df_attr))
    df_attr['LeftOuter'] = df_attr.id.apply(lambda x: leftouter(x,df_attr))
    df_attr['Calculated'] = df_attr.DataType_id.apply(lambda x: calculated(x))
    df_attr['TableColumn']=df_attr.apply(lambda x: tables.Column )
    return df_attr

def get_attribute(id,df_attr):
    return df_attr[df_attr.id==id].iloc[0]

def get_editfieldlist(Class_id,df_attr):
    return df_attr[df_attr.Class_id.isin([Class_id,0])&(~df_attr.Calculated)]

def get_tableviewlist(Class_id,df_attr):
    return df_attr[df_attr.Class_id.isin([Class_id,0])&(~df_attr.DataType_id.isin([10]))]

def get_fulllist(Class_id,df_attr):
    return df_attr[df_attr.Class_id.isin([Class_id,0])]

def create_rawquery_from_attributes(Class_id=0,filter={}):
    sql=Classes.objects.get(pk=Class_id).qs_sql + '\n' + create_filter_for_sql(Class_id,filter)
    qs=Instances.objects.raw(sql)
#    fqs = FilteredRawQuerySet.clone_raw_queryset(
#            raw_qs=qs, relation_map={
#            }
#        )
    return qs

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
        elif rec.DataType_id==3:
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

def get_value(Instance_id,Attribute_id):
    DataType=Attributes.objects.get(pk=Attribute_id).DataType.id
    if Instance_id == 0:
        value=''
    else:
        if not Values.objects.filter(Instance_id=Instance_id,Attribute_id=Attribute_id).exists():
            value = ''
        else:
            v = Values.objects.get(Instance_id=Instance_id, Attribute_id=Attribute_id)
            if DataType == 1:
                value=v.int_value
            elif DataType == 2:
                value=v.float_value
            elif DataType == 3:
                value=v.char_value
            elif DataType == 4:
                value=v.text_value
            elif DataType == 5:
                value=v.datetime_value
            elif DataType == 6:
                if pd.isnull(v.instance_value):
                    value=0
                else:
                    value=v.instance_value.id
            elif DataType == 9:
                value=v.int_value
            else:
                raise ('Wrong DataType')
    return value

def create_control_old(Instance_id,Attribute_id,read_only=False): #looks like I don't need it anymore
    at=Attributes.objects.get(pk=Attribute_id)
    ro=''
    if at.ReadOnly:
        ro='readonly'
    it=at.InputType.id
    dt=at.DataType.id
    valueslist=at.ValuesList
    value=get_value(Instance_id,Attribute_id)
    if   dt == 1: #int
        if valueslist=='':
            return '<input class="form-control" type="number" name="{name}" {ro} value="{val}" >'\
            .format(name=at.id,ro=ro,val=value)
        else:
            return '<select class="form-control" name="{name}">'
    elif dt == 2: #float
        return '<input class="form-control" type="number" step="0.01" {ro} name="{name}" value="{val}" >'\
            .format(name=at.id,ro=ro,val=value)
    elif dt == 3: #char
        return '<input class="form-control" type="text" name="{name}" value="{val}" {ro}>'\
            .format(name=at.id,ro=ro,val=value)
    elif dt == 4: #text
        return '<textarea class="form-control" rows="4" cols="50" name="{name}" {ro}>{val}</textarea>'\
            .format(name=at.id,ro=ro,val=value)
    elif dt == 5: #date
        if (type(value)!=str)&(not pd.isnull(value)):
            value=value.strftime("%Y-%m-%d")
        return '<input class="form-control" type="date" rows="4" cols="50" {ro} name="{name}" value="{val}">'\
            .format(name=at.id,ro=ro,val=value)
    elif dt == 6: #instance
        ins=Instances.objects.filter(Class_id=at.Ref_Class.id).values_list('id', 'Code')
        options = '<option value=0></option>' + ' '.join(['<option value={} {}>{}</option>'.format(list(o)[0], 'selected' if value==list(o)[0] else '',list(o)[1]) for o in ins]) #(value.id==list(o)[0])
        return '<select class="form-control" name="{name}" {ro}> {op} </select>'.format(name=at.id,ro=ro,val=options)
    elif dt in [9,10,11,12]:
        pass
    else:
        raise('DataType does not exists --create_control')

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
    if DataType == 1: #int
        if val!='':
            v.int_value=int(val)
        else:
            v.int_value=None
    elif DataType == 2: #float
        if val!='':
            v.float_value=float(val)
        else:
            v.float_value=None
    elif DataType == 3: #char
        if val!='':
            v.char_value=val
        else:
            v.char_value=None
    elif DataType == 4: #text
        if val!='':
            v.text_value=val
        else:
            v.text_value=None
    elif DataType == 5: #date
        if val!='':
            v.datetime_value=val
        else:
            v.datetime_value=None
    elif DataType == 6: #instance
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
    elif DataType == 9: #boolean
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

def cgreate_filter_set(Class_id,oldfilter={}):
    #building filter form content
    classattributes = Attributes.objects.filter(Class_id=Class_id,Filtered=True)
    filterform = create_filter(0, oldfilter)
    for at in classattributes:
        filterform = filterform + create_filter(at.id,oldfilter)
    return filterform

def get_val_by_name(key,d={}):
    if key in d.keys():
        res=d[key]
    else:
        res=''
    return res

def create_filter(Attribute_id,filter={}):
    #building html code for specific control
    at=Attributes.objects.get(pk=Attribute_id)
    if at.Attribute in filter.keys():
        value=filter[at.Attribute]
    else:
        value=''
    dt=at.DataType.id
    id=at.id



    cl="form-control form-control-xs"
    attribute=at.Attribute
    res='<div class ="d-inline-flex p-2 bd-highlight" >' \
        '<div class ="container rounded" style="border:1px solid #cecece;" >' \
        '<div class ="form-group" >'
    res=res+'<label>'+attribute+'</label><br><div class="input-group">'
    if   dt == 1: #int
        res=res+'<input class="{cl}" type="number" name="min{name}" placeholder="min" value="{minval}">'
        res=res+'<span class="input-group-addon">-</span>'
        res=res+'<input class="{cl}" type="number" name="max{name}" placeholder="max" value="{maxval}">'
        res=res.format(att=attribute,name=id,minval=get_val_by_name('min'+str(id),filter),maxval=get_val_by_name('max'+str(id),filter),cl=cl)
    elif dt == 2: #float
        res=res+'<input type="number" class="{cl}" step="{step}" name="min{name}" placeholder="min" value="{minval}">'
        res=res+'<span class="input-group-addon">-</span>'
        res=res+'<input type="number" class="{cl}" step="{step}" name="max{name}" placeholder="max" value="{maxval}">'
        res=res.format(att=attribute,name=id,minval=get_val_by_name('min'+str(id)),maxval=get_val_by_name('max'+str(id)), step=0.01,cl=cl)
    elif dt in [3,4]: #char & #text
        res=res+'<input type="text" class="{cl}" name="{name}" value="{val}">'.format(att=attribute,name=at.id,cl=cl,val=get_val_by_name(str(id),filter))
    elif dt == 5: #date
        res=res+'<input class="{cl}" type="date" name="min{name}" value={fromval}>'
        res=res+'<span class="input-group-addon">-</span>'
        res=res+'<input class="{cl}" type="date" name="max{name}" value={toval}>'
        res=res.format(att=attribute,name=at.id,cl=cl,fromval=get_val_by_name('from'+str(id),filter),toval=get_val_by_name('to'+str(id),filter))
    elif dt == 6: #instance
        val=get_val_by_name(str(id),filter)
        try:
            val=int(val)
        except:
            val=0

        ins=Instances.objects.filter(Class_id=at.Ref_Class.id).values_list('id', 'Code')
        options = '<option value=0></option>' + ' '.join(['<option value="{value}" {sel}>{opt}</option>'.format(value=list(o)[0],sel='selected' if val==list(o)[0] else '', opt=list(o)[1]) for o in ins])#(value.id==list(o)[0])

        res=res+'<select class="{cl}" name="{name}">{opt}</select>'.format(att=attribute,name=id,opt=options,cl=cl)
    elif dt == 9:  # instance
        pass
    else:
        raise('DataType does not exists --create_control')
    res=res+'</div></div></div></div>'
    return res

#this procedure creates a filter for the query that will be executed on the server
def create_filter_for_sql(Class_id,filter={}):
    where = ''
    for key,val in filter.items():
        if '__min__' in key:
            name=key[7:]
            type='min'
        elif '__max__' in key:
            name=key[7:]
            type='max'
        else:
            name=key
        #
        if name=='Code':
            id=0
        else:
            try:
                at=Attributes.objects.get(Class_id=Class_id,Attribute=name)
                id=at.id
                dt=at.DataType.id
                fieldname=get_fieldname(dt)
                tablename='val' + str(id)
            except ObjectDoesNotExist:
                print ('Attributes for',key,'have not been not found')
                id=-1
        if id<0:
            pass
        elif id==0:
            where = where + ' and ' + "ins.Code='{}'".format(val)
        elif dt in [1,2]:
            if type=='min':
                where=where + ' and ' + tablename+'.'+fieldname+'>={}'.format(val)
            else:
                where=where + ' and ' + tablename+'.'+fieldname+'<={}'.format(val)
        elif dt in [5,7]:
            if type=='min':
                where=where + ' and ' + tablename+'.'+fieldname+">='{}'".format(val)
            else:
                where=where + ' and ' + tablename+'.'+fieldname+"<='{}'".format(val)
        elif dt in [3,4,11,12]:
            where = where + ' and ' + tablename + '.' + fieldname + " like '%{}%'".format(val)
        elif dt in [6]:
            if int(val)!=0:
                where = where + ' and '+ tablename + '.' + fieldname + "={}".format(val)
        elif dt in [9]:
            where = where + ' and ' + tablename + '.' + fieldname + " = {}".format(val)
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
        fl=Classes.objects.get(pk=Class_id).editlist
        for index,rec in fl.iterrows():
            if str(rec.id) in instance.keys():
                save_attribute(ins.id,rec.id,instance[str(rec.id)])
        return True

@transaction.atomic
def save_instance_byname(Class_id,Instance_id=0,instance={},passed_by_name=True):
    #Class_id=Instances.objects.get(pk=Instance_id).Class.id
    code=instance['Code']
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
    fl=Classes.objects.get(pk=Class_id).editlist
    for index,rec in fl.iterrows():
        name=Attributes.objects.get(pk=rec.id).Attribute
        if name in instance.keys() and (index!=0):
            save_attribute(ins.id,rec.id,instance[name],passed_by_name=passed_by_name)
    return True

df_attributes=set_attributes()

from django.dispatch import receiver
@receiver(models.signals.post_save, sender=Attributes)
def update_attributes(sender, instance, **kwargs):
    global df_attributes
    from .utclasses import set_attributes
    df_attributes=set_attributes()
    print ('Reset Attributes. ',instance.Attribute,'changed')




