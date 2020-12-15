from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
import pandas as pd
from django.db.models import Q
# Create your models here.

#Datatype Constants
DT_Integer = 1
DT_Float = 2
DT_String =3
DT_Text = 4
DT_Date = 5
DT_Instance = 6
DT_Datetime = 7
DT_External = 8
DT_Boolean = 9
DT_Table = 10
DT_Currency = 11
DT_Email = 12
DT_Time = 13
DT_Calculated=14
DT_Lookup=15

DT_NUMBERS = [DT_Integer,DT_Float,DT_Date,DT_Instance,DT_Datetime,DT_Boolean,DT_Currency]
DT_LETTERS = [DT_String,DT_Text,DT_External,DT_Email,DT_Lookup,DT_Calculated]

FT_Exact=1
FT_MinMax=2
FT_Contains=3
FT_Like=4

#ValuesTable
DT_Value_map={
DT_Integer : 'Values_Int',
DT_Float   : 'Values_Float',
DT_String  : 'Values_Char',
DT_Text    : 'Values_Text',
DT_Date    : 'Values_DateTime',
DT_Instance: 'Values_Instance',
DT_Datetime: 'Values_DateTime',
DT_External: '',
DT_Boolean : 'Values_Int',
DT_Table   : '',
DT_Currency: 'Values_Float',
DT_Email   : 'Values_Char',
DT_Time    : 'Values_DateTime',
DT_Calculated : ''
}

def get_fieldname(dt,attr_id=0):
    f = 'No fieldName'
    if   dt in [DT_Integer,DT_Boolean]: #int,boolean
        f = 'int_value'
    elif dt in [DT_Float,DT_Currency]:
        f = 'float_value' #float,currency
    elif dt in [DT_String,DT_Email]:
        f = 'char_value'
    elif dt in [DT_Text]:
        f = 'text_value'
    elif dt in [DT_Date,DT_Datetime,DT_Time]: #date,datetime,time
        f = 'datetime_value'
    elif dt in [DT_Instance]:
        f = 'instance_value_id'
    elif dt in [DT_Lookup]:
        f = 'char_value'
    else:
        raise Exception ('No {} datatype'.format(dt))
    return '"'+f+'"'

class Projects(models.Model):
    Project = models.CharField(max_length=100,unique=True)
    Description = models.TextField(null=True,blank=True)
    class Meta:
        verbose_name='Projects'

class Reports(models.Model):
    Report = models.CharField(max_length=100,unique=True)
    Description = models.TextField(null=True,blank=True)
    #ReportType =
    Query = models.TextField(null=True,blank=True)
    class Meta:
        verbose_name='Reports'

class SendOuts(models.Model):
    Query = models.TextField(null=True,blank=True)
    EmailField = models.CharField(max_length=50,null=False)
    EmailGroupFields = models.TextField(null=True,blank=True)
    EmailTemplate = models.TextField(null=True,blank=True)
    class Meta:
        verbose_name='SendOuts'

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

class ProjectClassConn(models.Model):
    Class =models.ForeignKey (Classes,on_delete=models.PROTECT)
    Project=models.ForeignKey(Projects,on_delete=models.PROTECT)

class ProjectReportConn(models.Model):
    Project=models.ForeignKey(Projects,on_delete=models.PROTECT)
    Report =models.ForeignKey(Reports,on_delete=models.PROTECT)
    Default = models.BooleanField(default=False)

#int,varchar,text,class
class DataTypes(models.Model):
    DataType = models.CharField(max_length=50, unique=True)
    FieldFilter = models.IntegerField(default=0)
    Filter1stName = models.CharField(default='min', max_length=50)
    Filter2ndName = models.CharField(default='max', max_length=50)
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

from django.db.models import F, Func

class get_tablename(Func):
    function = 'get_tablename'

from django.db.models.functions import Concat
from django.db.models import Value

class AttributeManager(models.Manager):
    def get_queryset(self):
        qs=super(AttributeManager,self).get_queryset()\
            .annotate(TableName=Concat(Value('"val'),'id',Value('"'),output_field=models.CharField()))\
            .annotate(RefTableName=Concat(Value('"val_ins'),'id',Value('"'),output_field=models.CharField())) \
            .annotate(RefAttrTableName=Concat(Value('"val_ins'), 'id', Value('"'), output_field=models.CharField()))\
            .annotate(Master=F('Ref_Class_id__Master'))
        return qs

class Attributes(models.Model):
    Class = models.ForeignKey(Classes,on_delete=models.PROTECT,related_name='+')
    Attribute = models.CharField(max_length=50)
    DataType = models.ForeignKey(DataTypes,on_delete=models.PROTECT)
    Ref_Class = models.ForeignKey(Classes,on_delete=models.PROTECT,related_name='+',default=0) #zerohere
    Ref_Attribute = models.ForeignKey('self',on_delete=models.PROTECT,related_name='+', default=0)
    Formula = models.TextField(null=True,blank=True)
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

    #TableName = models.CharField(max_length=100,null=True,blank=True)
    #additional fields from adding from AttributeManager
    objects = AttributeManager()

    class Meta:
        unique_together = ('Class','Attribute')
        verbose_name='Attributes'

    def __str__(self):
        if self.Class.id == 0:
            res = 'Default-->Default'
        else:
            res = self.Class.Class +'-->'+self.Attribute
        return res

class email_templates(models.Model):
    pass

class Filters(models.Model):
    conditions=[('OR','OR'),('AND','AND')]
    fieldsizes=[(1,1),(2,2),(3,3),(4,4),(6,6),(12,12)]
    filtertypes=[(FT_Exact,'Exact'),(FT_MinMax,'Min and Max'),(FT_Contains,'Contains'),(FT_Like,'SQL Style LIKE')]
    Filter=models.CharField(max_length=50)
    Class=models.ForeignKey(Classes, on_delete=models.CASCADE)
    FilterType=models.IntegerField(choices=filtertypes,default=FT_Exact)
    Size=models.IntegerField(default=1,choices=fieldsizes)
    Attribute1=models.ForeignKey(Attributes, on_delete=models.CASCADE,related_name='+',default=0)
    Condition1=models.CharField(max_length=50,null=True,blank=True,choices=conditions,default='OR')
    Attribute2=models.ForeignKey(Attributes, on_delete=models.CASCADE,related_name='+',default=0)
    Condition2=models.CharField(max_length=50,null=True,blank=True,choices=conditions,default='OR')
    Attribute3=models.ForeignKey(Attributes, on_delete=models.CASCADE,related_name='+',default=0)
    Formula = models.TextField(null=True,blank=True)
    unique_together = ('Class', 'Filter')

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
    Instance = models.ForeignKey(Instances,on_delete=models.CASCADE, related_name='+')
    Attribute = models.ForeignKey(Attributes,on_delete=models.PROTECT)
#    Value=''
    int_value = models.IntegerField(null=True)
    char_value = models.CharField(max_length=255,null=True)
    text_value = models.TextField(null=True)
    float_value= models.FloatField(null=True)
    datetime_value = models.DateTimeField(null=True)
    instance_value = models.ForeignKey(Instances,on_delete=models.PROTECT, related_name='+',null=True)
    class Meta:
#        abstract = True
        unique_together = ('Instance','Attribute')
        verbose_name='Values'

    def save(self, *args, **kwargs): #rewrite save to check for unique & non null values
        att=self.Attribute
        #Add Datatypes Here
        Qs={DT_Integer:self.int_value,DT_Float:self.float_value,DT_String:self.char_value,DT_Text:self.text_value,
            DT_Date:self.datetime_value,DT_Datetime:self.datetime_value, DT_Instance:self.instance_value,DT_Email:self.char_value}
        Qn = {DT_Integer: 'int_value', DT_Float: 'float_value', DT_String: 'char_value', DT_Text: 'text_value',
              DT_Date:'datetime_value',DT_Datetime: 'datetime_value',DT_Instance: 'instance_value',DT_Email : 'char_value'}
        val=0
        #handle unique
        if att.UniqueAtt:
            if att.DataType.id in [DT_Integer,DT_String,DT_Date,DT_Email]:
                val_con=Q(**{Qn[att.DataType.id]:Qs[att.DataType.id]})
                val=Values.objects.filter(val_con&Q(Attribute_id=att.id)&(~Q(Instance_id=self.Instance.id)))
            else:
                pass
            if val.count()>0:
                raise Exception('Attribute "{}" for class "{}" is unique and the value "{}" has already used in the instance with id {}.'.format(att.Attribute,att.Class.Class,Qs[att.DataType.id],val[0].Instance.id))
        #handle not null value
        if att.NotNullAtt:
            if pd.isnull(Qs[att.DataType.id]):
                raise Exception('Attribute "{}" cannot be NULL'.format(att.Attribute))
        super().save(*args, **kwargs)

a="""
class Email_Templates(models.Model):
    Ones = 0
    Daily = 1
    Weekly = 2
    Monthly = 3
    frequencies=[(Daily,'Daily'),(Weekly,'Weekly'),(Monthly,'Monthly')]
    weekdays_short = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

    Class = models.ForeignKey(Classes,on_delete=models.PROTECT)
    Report = models.ForeingKey(Reports,on_delete=models.PROTECT)
"""

a='''
class Values_Int(Values):
    Value = models.IntegerField(null=True)
    class Meta:
        unique_together = ('Instance','Attribute')
        verbose_name='Values_Int'

class Values_Char(Values):
    Value = models.CharField(max_length=255, null=True)
    class Meta:
        unique_together = ('Instance', 'Attribute')
        verbose_name = 'Values_Char'

class Values_Text(Values):
    Value = models.TextField(null=True)
    class Meta:
        unique_together = ('Instance', 'Attribute')
        verbose_name = 'Values_Text'

class Values_Float(Values):
    Value = models.FloatField(null=True)
    class Meta:
        unique_together = ('Instance', 'Attribute')
        verbose_name = 'Values_Float'
        
class Values_DateTime(Values):
    Value = models.DateTimeField(null=True)
    class Meta:
        unique_together = ('Instance', 'Attribute')
        verbose_name = 'Values_DateTime'

class Values_Instance(Values):
    Value = models.ForeignKey(Instances, on_delete=models.PROTECT, related_name='+', null=True)
    class Meta:
        unique_together = ('Instance', 'Attribute')
        verbose_name = 'Values_Instance'

class Values_Image(Values):
    Value = models.ImageField(null=True)
    class Meta:
        unique_together = ('Instance', 'Attribute')
        verbose_name = 'Values_Image'
'''

import json
class Layouts(models.Model):
    Class = models.ForeignKey(Classes,on_delete=models.PROTECT)
    FormLayout  = models.TextField(null=True,blank=True)
    TableLayout = models.TextField(null=True,blank=True)
    ShortLayout = models.TextField(null=True,blank=True)

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

