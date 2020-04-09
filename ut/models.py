from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
import pandas as pd
from django.db.models import Q
# Create your models here.

def get_fieldname(dt):
    f = 'No fieldName'
    if   dt == 1:
        f = 'int_value'
    elif dt == 2:
        f = 'float_value'
    elif dt == 3:
        f = 'char_value'
    elif dt == 4:
        f = 'text_value'
    elif dt == 5:
        f = 'datetime_value'
    elif dt == 6:
        f = 'instance_value_id'
    elif dt==9 : #boolean
        f='int_value'
    else:
        raise Exception ('No {} such datatype'.format(dt))
    return '"'+f+'"'

class Classes(models.Model):
    Class = models.CharField(max_length=50,unique=True)
    Master = models.ForeignKey('self',on_delete=models.PROTECT)
    Template = models.TextField(null=True,blank=True)
    UseAutoCounter = models.BooleanField(default=False,blank=True)
    Prefix = models.CharField(max_length=10,null=True,blank=True)
    CounterStrLen = models.IntegerField(default=10)
    class Meta:
        verbose_name='Classes'
    def __str__(self):
        return self.Class
    @property
    def qs_sql(self):
        atts=Attributes.objects.filter(Q(Class_id=self.id) #| Q(Class_id=0)
                                       )
        ss = {}
        lo = {}
        for a in atts:
            for key,val in a.selectfield.items():
                ss[key]=val
            for key,val in a.leftouter.items():
                lo[key]=val
        if len(ss)>0:
            co=','
        else:
            co=''
        sselect = 'select ins.id, ins.Code' +co + ',\n'.join(ss.values())
        sfrom='from {ins} ins\n'.format(ins=Instances._meta.db_table) +'\n'.join(lo.values())
        swhere = 'where ins.Class_id={}'.format(self.id)
        return sselect +'\n' + sfrom + '\n' + swhere
    @property
    def fieldlist(self):
        atts=Attributes.objects.filter(Class_id=self.id)
        return atts
    @property
    def editlist(self):
        atts=Attributes.objects.filter(Q(Class_id=self.id)|Q(id=0)).order_by('Class_id','id')
        return pd.DataFrame([x.__dict__ for x in atts if not x.Calculated])

    @property
    def fulllist(self):
        atts=Attributes.objects.filter(Class_id=self.id)
        return pd.DataFrame([x.__dict__ for x in atts])


#int,varchar,text,class
class DataTypes(models.Model):
    DataType = models.CharField(max_length=50,unique=True)
    class Meta:
        verbose_name='DataTypes'
    def __str__(self):
        return self.DataType

class InputTypes(models.Model):
    Inputtype = models.CharField(max_length=50,unique=True)
    HtmlLine = models.TextField(null=True)
    Description = models.TextField(null=True)
    class Meta:
        verbose_name = 'InputTypes'

class Attributes(models.Model):
    Class = models.ForeignKey(Classes,on_delete=models.PROTECT,related_name='+')
    Attribute = models.CharField(max_length=50)
    DataType = models.ForeignKey(DataTypes,on_delete=models.PROTECT)
    Ref_Class = models.ForeignKey(Classes,on_delete=models.PROTECT,related_name='+',default=0) #zerohere
    Ref_Attribute = models.ForeignKey('self',on_delete=models.PROTECT,related_name='+', default=0)
    InputType = models.ForeignKey(InputTypes,on_delete=models.PROTECT,default=0,blank=True)
    ReadOnly = models.BooleanField(default=False)
    Filtered = models.BooleanField(default=True)
    UniqueAtt = models.BooleanField(default=False)
    NotNullAtt = models.BooleanField(default=False)
    ShowInTable = models.BooleanField(default=True)
    #these fields handles the connection with external source
    # Externaltable.ExternalUq = values table wiht the right attribute (char or int), and ExternalField is shown
    ExternalTable = models.CharField(max_length=50,null=True,blank=True)
    ExternalUq = models.CharField(max_length=50,null=True,blank=True)
    InternalAttribute = models.ForeignKey('self',on_delete=models.PROTECT,related_name='+', default=0)
    ExternalField = models.CharField(max_length=50,null=True,blank=True)
    ValuesList = models.TextField(null=True,blank=True) #only for char, int & float
    class Meta:
        unique_together = ('Class','Attribute')
        verbose_name='Attributes'

    def __str__(self):
        if self.Class.id == 0:
            res = 'Default-->Default'
        else:
            res = self.Class.Class +'-->'+self.Attribute
        return res

    @property
    def tablename(self):
        return '"val{}"'.format(self.id)

    @property
    def reftablename(self):
        return '"val_ins{}"'.format(self.id)

    @property
    def refatttablename(self):
        return '"refval{}"'.format(self.id)

    @property
    def selectfield(self):
        res={}
        if self.DataType.id==6:
            if self.Ref_Attribute.id==0:
                res[self.Attribute]='{tab}.{field} as "{name}"'.format(tab=self.reftablename,field='"Code"',name=self.Attribute)
            else:
                res[self.Attribute]='{tab}.{field} as "{name}"'\
                    .format(tab=self.refatttablename,field=get_fieldname(self.Ref_Attribute.DataType.id),name=self.Attribute)
        elif self.DataType.id==8:
            res[self.Attribute]='{tab}.{field} as "{name}"'.format(tab=self.ExternalTable,field=self.ExternalField,name=self.Attribute)
        else:
            res[self.Attribute]='{tab}.{field} as "{name}"'.format(tab=self.tablename,id=self.id,field=get_fieldname(self.DataType.id),name=self.Attribute)
        return res

    @property
    def leftouter(self):
        res={}
        if self.DataType.id==8:
            res[self.ExternalTable] = 'LEFT OUTER JOIN {ext} as {ext} ON ({ext}.{uq}={loctab}.{locfield})'\
                .format(ext=self.ExternalTable,uq=self.ExternalUq,loctab=self.InternalAttribute.tablename,locfield=get_fieldname(self.InternalAttribute.DataType.id))
        else:
            res[self.tablename]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}.Instance_id=ins.id and {tab}.Attribute_id={id})'.format(val=Values._meta.db_table,tab=self.tablename,id=self.id)
            if self.DataType.id == 6:
                res[self.reftablename]='LEFT OUTER JOIN {ins} as {reftab} ON ({reftab}.id={tab}.instance_value_id)'.format(ins=Instances._meta.db_table,tab=self.tablename,reftab=self.reftablename)
                if self.Ref_Attribute.id!=0:
                    res[self.refatttablename] = 'LEFT OUTER JOIN {val} as {refval} ON ({refval}.Instance_id = {reftab}.id and {refval}.Attribute_id = {refatt})'\
                        .format(val=Values._meta.db_table,refval=self.refatttablename,refatt=self.Ref_Attribute.id,reftab=self.reftablename)

        return res
    @property
    def Calculated(self):
        res = False
        if self.DataType.id==8:
            res=True
        return res

class Counters(models.Model):
    Class=models.OneToOneField(Classes,on_delete=models.CASCADE)
    CurrentCounter = models.IntegerField(default=0)

class Instances(models.Model):
    Class = models.ForeignKey(Classes,on_delete=models.PROTECT)
    #Master = models.ForeignKey('self',on_delete=models.PROTECT,null=True)
    Code = models.CharField(max_length=20)
    class Meta:
        unique_together = ('Class','Code')
        verbose_name='Instances'
    def __str__(self):
        return self.Code

class Values(models.Model):
    Instance = models.ForeignKey(Instances,on_delete=models.CASCADE,related_name='+')
    Attribute = models.ForeignKey(Attributes,on_delete=models.PROTECT)
    int_value = models.IntegerField(null=True)
    char_value = models.CharField(max_length=255,null=True)
    text_value = models.TextField(null=True)
    float_value= models.FloatField(null=True)
    datetime_value = models.DateTimeField(null=True)
    instance_value = models.ForeignKey(Instances,on_delete=models.PROTECT,related_name='+',null=True)
    class Meta:
        unique_together = ('Instance','Attribute')
        verbose_name='Values'

    def save(self, *args, **kwargs): #rewrite save to check for unique & non null values
        att=self.Attribute
        Qs={1:self.int_value,2:self.float_value,3:self.char_value,4:self.text_value,5:self.datetime_value,6:self.instance_value}
        val=0
        #handle unique
        if att.UniqueAtt:
            if att.DataType.id in [1,3,5]:
                val_con=Q(Qs[att.DataType.id])
                val=Values.objects.filter(Q(char_value=self.char_value)&Q(Attribute_id=att.id)&(~Q(Instance_id=self.Instance.id)))
            else:
                pass
            if val.count()>0:
                raise Exception('Attribute "{}" for class "{}" is unique and already used in instance with id {}.'.format(att.Attribute,att.Class.Class,val[0].Instance.id))
        #handle not null value
        if att.NotNullAtt:
            if pd.isnull(Qs[att.DataType.id]):
                raise Exception('Attribute "{}" cannot be NULL'.format(att.Attribute))
        super().save(*args, **kwargs)


import json
class Layouts(models.Model):
    Class = models.ForeignKey(Classes,on_delete=models.PROTECT)
    FormLayout = models.TextField(null=True,blank=True)
    TableLayout= models.TextField(null=True,blank=True)

    @property
    def form_dict(self):
        if not pd.isnull(self.FormLayout):
            res=json.loads(self.FormLayout)
        else:
            res=json.loads('{"Column1":"","Column2":""}')
        return res

    @property
    def table_dict(self):
        if not pd.isnull(self.TableLayout):
            res=json.loads(self.TableLayout)
        else:
            res=json.loads('{"Row1":""}')
        return res

class FormLayouts(models.Model):
    Class = models.ForeignKey(Classes,on_delete=models.PROTECT)
    Attribute = models.ForeignKey(Attributes,on_delete=models.PROTECT)
    Row = models.IntegerField(default=0)
    Column = models.IntegerField(default=0)

