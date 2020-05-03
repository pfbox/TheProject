from ut.models import *
import django_tables2 as tables
import pandas as pd
from django_pandas.io import read_frame
import numpy as np
from django.db import transaction

from django_tables2.utils import A

from django.apps import apps
app_models = apps.get_app_config('ut').get_models()
am=pd.DataFrame()
for a in app_models:
    am = am.append({'TableName': a._meta.verbose_name, 'Table': a},ignore_index=True)  # .to_dict()

from django.db import connection
con=connection
df_classes=pd.DataFrame()#pd.read_sql('select * from ut_classes',con) #.set_index('id')
df_attributes=pd.DataFrame()#pd.read_sql('select * from ut_attributes',con) #.set_index('id')
df_datatypes=pd.DataFrame()#pd.read_sql('select * from ut_datatypes',con) #.set_index('id')
df_inputtypes=pd.DataFrame()#pd.read_sql('select * from ut_inputtypes',con) #.set_index('id')
df_formlayouts=pd.read_sql('select * from ut_formlayouts',con) #.set_index('id')
#df_filters =pd.read_sql('select * from ut_filters',con)

from django_jinja_knockout.query import FilteredRawQuerySet

def create_rawquery_from_attributes(Class_id=0,filter={}):
    sql=Classes.objects.get(pk=Class_id).qs_sql + '\n' + create_filter_for_sql(filter)
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
    elif dt == 9:  # instance
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
                ref_class=Attributes.objects.get(pk=Attribute_id).Ref_Class
                ref_attr=Attributes.objects.get(pk=Attribute_id).Ref_Attribute
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

def create_filter_set(Class_id,oldfilter={}):
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

def create_filter_for_sql(filter={}):
    where = ''
    for key,val in filter.items():
        if 'min' in key:
            id=int(key[3:])
            type='min'
        elif 'max' in key:
            id=int(key[3:])
            type='max'
        else:
            id=int(key)
        #
        at=Attributes.objects.get(pk=id)
        id=at.id
        dt=at.DataType.id
        fieldname=get_fieldname(dt)
        tablename='val' + str(id)
        if id==0:
            where = where + ' and ' + "ins.Code='{}'".format(val)
        elif dt in [1,2]:
            if type=='min':
                where=where + ' and ' + tablename+'.'+fieldname+'>={}'.format(val)
            else:
                where=where + ' and ' + tablename+'.'+fieldname+'<={}'.format(val)
        elif dt in [5]:
            if type=='min':
                where=where + ' and ' + tablename+'.'+fieldname+">='{}'".format(val)
            else:
                where=where + ' and ' + tablename+'.'+fieldname+">='{}'".format(val)
        elif dt in [3,4]:
            where = where + ' and ' + tablename + '.' + fieldname + " like '%{}%'".format(val)
        elif dt in [6]:
            if int(val)!=0:
                where = where + ' and '+ tablename + '.' + fieldname + "={}".format(val)

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

def get_tablelayout(Class_id):
    try:
        res=Layouts.objects.get(Class_id=Class_id).TableLayout
    except Layouts.DoesNotExist:
        res={'settings':{},'layout':[]}
        a=Layouts(Class_id=Class_id,TableLayout=json.dumps(res))
        a.save()
    print ('Class_id  ',Class_id,'res',res)
    return res

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


