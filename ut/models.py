from django.db import models
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
import pandas as pd
from django.db.models import Q, Max, Min
from django.conf import settings
from django.contrib.auth.models import Group
from datetime import datetime, timedelta
from django_currentuser.middleware import get_current_user, get_current_authenticated_user
from django_currentuser.db.models import CurrentUserField
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.core.cache import caches


import pytz
# Create your models here.

#need to wrap the field mysql --> '`'; postgress, ms sql --> '"'
Default_Identifier = '"' #'"'
Current_Identifier = '"' # '`' --> for MySQL, '"' --> for postgres, '"' --> sqlite3
memory_cache = caches['memory']

#Constants
Default_Attribute = -1
Default_Class = -1
Default_Filter = -1
Default_Project = -1

#Input Types
IT_Default = -1
IT_Select2 = 1

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
DT_ManyToMany=16

DT_NUMBERS = [DT_Integer,DT_Float,DT_Date,DT_Instance,DT_Datetime,DT_Boolean,DT_Currency]
DT_LETTERS = [DT_String,DT_Text,DT_External,DT_Email,DT_Lookup,DT_Calculated,DT_Time]

DTG_Int = [DT_Integer,DT_Boolean] #1
DTG_Float = [DT_Float,DT_Currency] #2
DTG_String = [DT_String,DT_Email,DT_Lookup,DT_Time] #3
DTG_Text = [DT_Text] #4
DTG_Instance = [DT_Instance] #5
DTG_Date = [DT_Date,DT_Datetime] #5
DTG_ManyToMany = [DT_ManyToMany ] #6


FT_Exact=1
FT_MinMax=2
FT_Contains=3
FT_Like=4

def get_fieldname(dt):
    f = 'No fieldName'
    if   dt in [DT_Integer,DT_Boolean]: #int,boolean
        f = 'int_value'
    elif dt in [DT_Float,DT_Currency]:
        f = 'float_value' #float,currency
    elif dt in [DT_String,DT_Email,DT_Time]:
        f = 'char_value'
    elif dt in [DT_Text]:
        f = 'text_value'
    elif dt in [DT_Date,DT_Datetime]: #date,datetime,time
        f = 'datetime_value'
    elif dt in [DT_Instance]:
        f = 'instance_value_id'
    elif dt in [DT_Lookup]:
        f = 'char_value'
    elif dt in [DT_ManyToMany]:
        f = 'manytomany'
    else:
        raise Exception ('No {} datatype'.format(dt))
    return '{di}{f}{di}'.format(f=f,di=Default_Identifier)

class Reports(models.Model):
    Report = models.CharField(max_length=100,unique=True)
    Description = models.TextField(null=True,blank=True)
    Query = models.TextField(null=True,blank=True)
    ViewGroups = models.ManyToManyField(Group, related_name='+', blank=True)
    @property
    def QueryAdj(self):
        return self.Query.replace(Default_Identifier,Current_Identifier)
    @property
    def render_to_string(self):
        context={'Report_id':self.id}
        return render_to_string('ut/report.html',context)
    class Meta:
        verbose_name='Reports'
    def __str__(self):
        return self.Report

from tinymce.models import HTMLField

class EmailTemplates(models.Model):
    TemplateName = models.CharField(max_length=100,unique=True,null=False,blank=False)
    ToTemplate= models.CharField(max_length=255,null=True,blank=True)
    CcTemplate= models.CharField(max_length=255,null=True,blank=True)
    SubjectTemplate = models.CharField(max_length=255,null=True,blank=True)
    Template = HTMLField(null=True,blank=True)

class SendOuts(models.Model):
    Query = models.TextField(null=True,blank=True)
    EmailField = models.CharField(max_length=50,null=False)
    EmailGroupFields = models.TextField(null=True,blank=True)
    EmailTemplate = models.ForeignKey(EmailTemplates,related_name='+',null=True,blank=True,on_delete=models.PROTECT)
    class Meta:
        verbose_name='SendOuts'

class ClassManager(models.Manager):
    def get_queryset(self):
        qs=super(ClassManager,self).get_queryset()
        user=get_current_user()
        if (user is not None) and user.is_authenticated:
            if user.is_superuser==False:
                qs=qs.filter(Q(ViewGroups__in=Group.objects.filter(user=user))|Q(id=Default_Class))
        else:
            qs=qs.filter(id=None)
        return qs

class Classes(models.Model):
    Class = models.CharField(max_length=50,unique=True)
    Master = models.ForeignKey('self',on_delete=models.PROTECT)
    Template = models.TextField(null=True,blank=True)
    UseAutoCounter = models.BooleanField(default=False,blank=True)
    Prefix = models.CharField(max_length=10,null=True,blank=True)
    CounterStrLen = models.IntegerField(default=10)
    DefaultEmailTemplate =models.ForeignKey(EmailTemplates,related_name='+',blank=True,null=True,on_delete=models.PROTECT)
    InsertGroups = models.ManyToManyField(Group,related_name='+',blank=True)
    ViewGroups = models.ManyToManyField(Group,related_name='+',blank=True)
    UpdateGroups = models.ManyToManyField(Group,related_name='+',blank=True)
    DeleteGroups = models.ManyToManyField(Group,related_name='+',blank=True)
    RightsFilteredByClass = models.ManyToManyField("self",related_name='+',blank=True)
    Class_query = models.TextField(null=True,blank=True)
    objects= ClassManager()
    allobjects = models.Manager()
    class Meta:
        verbose_name='Classes'
    def __str__(self):
        return self.Class

class ProjectManager(models.Manager):
    def get_queryset(self):
        qs=super(ProjectManager,self).get_queryset()
        user=get_current_user()
        if (user is not None) and user.is_authenticated:
            if user.is_superuser==False:
                qs=qs.filter(Q(ViewGroups__in=Group.objects.filter(user=user))|Q(id=Default_Project))
        else:
            qs=qs.filter(id=None)
        return qs

class Projects(models.Model):
    Project = models.CharField(max_length=100,unique=True)
    Description = models.TextField(null=True,blank=True)
    DefaultReport = models.ForeignKey(Reports,on_delete=models.SET_NULL,related_name='+',null=True,blank=True)
    Classes_m2m = models.ManyToManyField(Classes,blank=True)
    Reports_m2m = models.ManyToManyField(Reports,blank=True)
    ViewGroups = models.ManyToManyField(Group,related_name='+')
    UpdateGroups = models.ManyToManyField(Group,related_name='+')
    objects=ProjectManager()
    class Meta:
        verbose_name='Projects'

class InputTypes(models.Model):
    Inputtype = models.CharField(max_length=50,unique=True)
    HtmlLine = models.TextField(null=True)
    Description = models.TextField(null=True)
    class Meta:
        verbose_name = 'InputTypes'
    def __str__(self):
        return self.Inputtype

#int,varchar,text,class
class DataTypes(models.Model):
    DataType = models.CharField(max_length=50, unique=True)
    InputTypes=models.ManyToManyField(InputTypes,related_name='+',blank=True)
    FieldName=models.CharField(max_length=100,blank=True,null=True)
    class Meta:
        verbose_name='DataTypes'
    def __str__(self):
        return self.DataType

class AttributeManager(models.Manager):
    def get_queryset(self):
        qs=super(AttributeManager,self).get_queryset()
        user=get_current_user()
        if (user is not None) and user.is_authenticated:
            if user.is_superuser==False:
                qs=qs.filter(Q(ViewGroups__in=Group.objects.filter(user=user))|Q(id=Default_Attribute))
        else:
            qs=qs.filter(id=None)
        return qs

def valuefield_nd(attr):
    #attr=Attributes.objects.get(pk=id)
    id=attr.id
    dt= attr.DataType_id
    attribute=attr.Attribute
    ref_attribute_id=attr.Ref_Attribute_id
    if id == Default_Attribute:
        res='ins."Code"'
    elif dt == DT_Lookup:
        res='{tab}.{field}'.format(tab=attr.RefAttrTableName, field=get_fieldname(DT_String))
    elif dt == DT_External:
        res='"{tab}"."{field}"'.format(tab=attr.ExternalTable, field=attr.ExternalField)
    elif dt in [DT_Table]:
        res = '0 as Table__' + str(id) + '__'
    elif dt in [DT_Calculated]:
        res = '{formula}'.format(formula=attr.Formula)
    else:
        res = '{tab}.{field}'.format(tab=attr.TableName, id=id,field=get_fieldname(dt))
    return res

def selectfield_nd(attr):
    id = attr.id
    dt= attr.DataType_id
    ref_attr = attr.Ref_Attribute
    ref_attribute_id=attr.Ref_Attribute_id
    if id==Default_Attribute:
        res = 'ins."Code"'
    elif dt == DT_Instance:
        if ref_attribute_id == Default_Attribute:
            res = '{tab}.{field}'.format(tab=attr.RefTableName, field='"Code"')
        else:
            res = '{tab}.{field}' \
                .format(tab=attr.RefAttrTableName, field=get_fieldname(ref_attr.DataType_id))
    elif dt == DT_Lookup:
            res = '{tab}.{field}' \
                .format(tab=attr.RefAttrTableName, field=get_fieldname(DT_String))
    elif dt == DT_External:
        res = '"{tab}"."{field}"'.format(tab=attr.ExternalTable, field=attr.ExternalField)
    elif dt in [DT_Table]:
        res = '0 as Table__' + str(id) + '__'
    elif dt in [DT_Calculated]:
        res = '{formula}'.format(formula=attr.Formula)
    else:
        res = '{tab}.{field}'.format(tab=attr.TableName, id=id,field=get_fieldname(dt))
    return res

def valueleftouter(attr):
    #attr = Attributes.objects.get(pk=id)
    dt= attr.DataType_id
    internal_attr = attr.InternalAttribute
    res={}
    if dt == DT_External:
        res[attr.ExternalTable] = 'LEFT OUTER JOIN {ext} as {ext} ON ({ext}.{uq}={loctab}.{locfield})'\
            .format(ext=attr.ExternalTable,uq=attr.ExternalUq,loctab=internal_attr.TableName,locfield=get_fieldname(internal_attr.DataType_id))
    elif dt == DT_Lookup:
        res[internal_attr.TableName]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}."Instance_id"=ins.id and {tab}."Attribute_id"={id}) /* {attr} 1 */'\
            .format(val=Values._meta.db_table,tab=internal_attr.TableName,id=internal_attr.id,attr=attr.Attribute)
        res[internal_attr.RefTableName] = 'LEFT OUTER JOIN {ins} as {reftab} ON ({reftab}.id={tab}."instance_value_id") /* {attr} 2 */' \
            .format(ins=Instances._meta.db_table, tab=internal_attr.TableName, reftab=internal_attr.RefTableName,attr=attr.Attribute)
        res[attr.RefAttrTableName] = 'LEFT OUTER JOIN {val} as {refval} ON ({refval}."Instance_id" = {reftab}.id and {refval}."Attribute_id" = {refatt}) /* {attr} 3 */' \
                .format(val=Values._meta.db_table, refval=attr.RefAttrTableName, refatt=attr.Ref_Attribute_id,
                        reftab=internal_attr.RefTableName,attr=attr.Attribute)
    else:
        res[attr.TableName]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}."Instance_id"=ins.id and {tab}."Attribute_id"={id}) /* {attr} */'\
            .format(val=Values._meta.db_table,tab=attr.TableName,id=attr.id,attr=attr.Attribute)
    return res

def leftouter(attr):
    #attr = Attributes.objects.get(pk=id)
    dt= attr.DataType_id
    internal_attr = attr.InternalAttribute

    res={}

    if dt == DT_External:
        res[attr.ExternalTable] = 'LEFT OUTER JOIN {ext} as {ext} ON ({ext}.{uq}={loctab}.{locfield})'\
            .format(ext=attr.ExternalTable,uq=attr.ExternalUq,loctab=internal_attr.TableName,locfield=get_fieldname(internal_attr.DataType_id))
    elif dt == DT_Lookup:
        res[internal_attr.TableName]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}."Instance_id"=ins.id and {tab}."Attribute_id"={id}) /* {attr} 1 */'\
            .format(val=Values._meta.db_table,tab=internal_attr.TableName,id=internal_attr.id,attr=attr.Attribute)
        res[internal_attr.RefTableName] = 'LEFT OUTER JOIN {ins} as {reftab} ON ({reftab}.id={tab}.instance_value_id) /* {attr} 2 */' \
            .format(ins=Instances._meta.db_table, tab=internal_attr.TableName, reftab=internal_attr.RefTableName,attr=attr.Attribute)
        res[attr.RefAttrTableName] = 'LEFT OUTER JOIN {val} as {refval} ON ({refval}."Instance_id" = {reftab}.id and {refval}."Attribute_id" = {refatt}) /* {attr} 3 */' \
                .format(val=Values._meta.db_table, refval=attr.RefAttrTableName, refatt=attr.Ref_Attribute_id,
                        reftab=internal_attr.RefTableName,attr=attr.Attribute)
    else:
        res[attr.TableName]= 'LEFT OUTER JOIN {val} as {tab} ON ({tab}."Instance_id"=ins.id and {tab}."Attribute_id"={id}) /* {attr} */ '\
            .format(val=Values._meta.db_table,tab=attr.TableName,id=attr.id,attr=attr.Attribute)
        if dt == DT_Instance:
            res[attr.RefTableName]='LEFT OUTER JOIN {ins} as {reftab} ON ({reftab}.id={tab}.instance_value_id) /* {attr} */'\
                .format(ins=Instances._meta.db_table,tab=attr.TableName,reftab=attr.RefTableName,attr=attr.Attribute)
            if attr.Ref_Attribute_id!=Default_Attribute:
                res[attr.RefAttrTableName] = 'LEFT OUTER JOIN {val} as {refval} ON ({refval}."Instance_id" = {reftab}.id and {refval}."Attribute_id" = {refatt}) /* {attr} */'\
                    .format(val=Values._meta.db_table,refval=attr.RefAttrTableName,refatt=attr.Ref_Attribute_id,reftab=attr.RefTableName,attr=attr.Attribute)

    return res

def calculated(dt):
    if dt in [DT_External,DT_Calculated]:
        return True
    else:
        return False

def filter_value(dt):
    if dt in DT_NUMBERS:
        res = '{val}'
    elif dt in DT_LETTERS:
        res = "'{val}'"
    else:
        res = ''
    return res

class Attributes(models.Model):
    Class = models.ForeignKey(Classes,on_delete=models.PROTECT,related_name='+')
    Attribute = models.CharField(max_length=50)
    DataType = models.ForeignKey(DataTypes,on_delete=models.PROTECT)
    InputType = models.ForeignKey(InputTypes,null=False,blank=False,on_delete=models.PROTECT,default=IT_Default)
    Ref_Class = models.ForeignKey(Classes,on_delete=models.PROTECT,related_name='+',default=Default_Class) #zerohere
    Ref_Attribute = models.ForeignKey('self',on_delete=models.PROTECT,related_name='+', default=Default_Attribute)
    Formula = models.TextField(null=True,blank=True)
    ReadOnly = models.BooleanField(default=False)
    Filtered = models.BooleanField(default=True)
    UniqueAtt = models.BooleanField(default=False)
    NotNullAtt = models.BooleanField(default=False)
    ShowInTable = models.BooleanField(default=True)
    #these fields handles the connection with external source
    # Externaltable.ExternalUq = values table wiht the right attribute (char or int), and ExternalField is shown
    ExternalTable = models.CharField(max_length=50,null=True,blank=True)
    ExternalUq = models.CharField(max_length=50,null=True,blank=True)
    InternalAttribute = models.ForeignKey('self',on_delete=models.PROTECT,related_name='+' ,default=Default_Attribute)
    ExternalField = models.CharField(max_length=50,null=True,blank=True)
    ValuesList = models.TextField(null=True,blank=True) #only for char, int & float
    ## sytem fields used for sql building
    UseExternalTables=models.BooleanField(default=False) #if you'd like to generate internal fields
    ViewGroups = models.ManyToManyField(Group,related_name='+')
    UpdateGroups = models.ManyToManyField(Group,related_name='+')
    objects = AttributeManager()
    allobjects = models.Manager()
    @cached_property
    def TableName(self):
        return '{di}val{id}{di}'.format(id=self.id,di=Default_Identifier)
    @cached_property
    def RefTableName(self):
        return '{di}val_ins{id}{di}'.format(id=self.id,di=Default_Identifier)
    @cached_property
    def RefAttrTableName(self):
        return '{di}refval{id}{di}'.format(id=self.id,di=Default_Identifier)
    @cached_property
    def Calcultated(self):
        return calculated(self.DataType_id)
    @cached_property
    def SelectedField(self):
        return selectfield_nd(self)
    @cached_property
    def ValueField(self):
        return valuefield_nd(self)
    @cached_property
    def LeftOuter(self):
        return leftouter(self)
    @cached_property
    def ValueLeftOuter(self):
        return valueleftouter(self)
    @cached_property
    def FT_Exact(self):
        return self.ValueField + '=' + filter_value(self.DataType_id)
    @cached_property
    def FT_Contains(self):
        return self.ValueField + " like '%{val}%'"
    @cached_property
    def FT_Like(self):
        return self.ValueField + " like '{val}'"
    @cached_property
    def FT_Min(self):
        return self.ValueField + '>=' + filter_value(self.DataType_id)
    @cached_property
    def FT_Max(self):
        return self.ValueField  + '<=' + filter_value(self.DataType_id)
    def __str__(self):
        return self.Class.Class + '-->' + self.Attribute
    @cached_property
    def cache_key(self):
        return 'attr-id-{}'.format(self.id)

    def set_cached_properties(self):
        # MasterAttribute
        MasterAttribute = None
        ma = Attributes.allobjects.exclude(Ref_Class_id=Default_Attribute) \
            .filter(DataType_id=DT_Instance, Ref_Class_id=self.Ref_Class.Master_id, Class_id=self.Class_id).exists()
        if ma:
            MasterAttribute = Attributes.allobjects.exclude(Ref_Class_id=0) \
                .filter(DataType_id=DT_Instance, Ref_Class_id=self.Ref_Class.Master_id,
                        Class_id=self.Class_id).first()
        # MasterAttribute_id
        MasterAttribute_id = 0
        if MasterAttribute:
            MasterAttribute_id = MasterAttribute.id

        # get lookup_trigger
        lookup_trigger = 0
        for a in Attributes.allobjects.exclude(InternalAttribute=0).filter(DataType_id=DT_Lookup,
                                                                           InternalAttribute_id=self.id):
            lookup_trigger = a.id

        # hierarchy_trigger
        hierarchy_trigger = 1
#        for a in Attributes.objects.exclude(id=self.id).filter(Class_id=self.Class_id):
#            print('im here')
#            if a.MasterAttribute_id != 0 and a.MasterAttribute_id == self.id:
#                hierarchy_trigger = a.id
        # lookup_trigger

        dependent_fields = {}
        ma = MasterAttribute
        while pd.notnull(ma):
            dependent_fields[ma.Attribute] = ma.Attribute
            try:
                ma = Attributes.allobjects.exclude(Ref_Class_id=Default_Attribute) \
                    .filter(DataType_id=DT_Instance, Ref_Class_id=ma.Ref_Class.Master_id,
                            Class_id=self.Class_id).first()
            except:
                ma = None

        properties = {
            'lookup_trigger': lookup_trigger,
            'hierarchy_trigger': hierarchy_trigger,
            'MasterAttribute': MasterAttribute,
            'MasterAttribute_id': MasterAttribute_id,
            'dependent_fields': dependent_fields
        }
        memory_cache.set(self.cache_key, properties)

    @cached_property
    def cached_important_properties(self):
        pps = memory_cache.get(self.cache_key)
        if pd.isnull(pps):
            self.set_cached_properties()
            pps = memory_cache.get(self.cache_key)
        return pps

    @property
    def MasterAttribute(self):
        return self.cached_important_properties['MasterAttribute']

    @property
    def MasterAttribute_id(self):
        return self.cached_important_properties['MasterAttribute_id']

    @property
    def dependent_fields(self):
        return self.cached_important_properties['dependent_fields']

    @property
    def hierarchy_trigger(self):
        return self.cached_important_properties['hierarchy_trigger']

    @property
    def lookup_trigger(self):
        return self.cached_important_properties['lookup_trigger']


att_columns=['id','DataType_id','FT_Exact','FT_Contains','FT_Like','FT_Min','FT_Max']
filter_expression_columns=['FT_Exact','FT_Contains','FT_Like','FT_Min','FT_Max']

class Filters(models.Model):
    conditions=[('OR','OR'),('AND','AND')]
    fieldsizes=[(1,1),(2,2),(3,3),(4,4),(6,6),(12,12)]
    filtertypes=[(FT_Exact,'Exact'),(FT_MinMax,'Min and Max'),(FT_Contains,'Contains'),(FT_Like,'SQL Style LIKE')]
    Filter=models.CharField(max_length=50)
    Class=models.ForeignKey(Classes, on_delete=models.CASCADE)
    FilterType=models.IntegerField(choices=filtertypes,default=FT_Exact)
    Size=models.IntegerField(default=1,choices=fieldsizes)
    Attribute1=models.ForeignKey(Attributes, on_delete=models.CASCADE,related_name='+',default=Default_Attribute)
    Condition1=models.CharField(max_length=50,null=True,blank=True,choices=conditions,default='OR')
    Attribute2=models.ForeignKey(Attributes, on_delete=models.CASCADE,related_name='+',default=Default_Attribute)
    Condition2=models.CharField(max_length=50,null=True,blank=True,choices=conditions,default='OR')
    Attribute3=models.ForeignKey(Attributes, on_delete=models.CASCADE,related_name='+',default=Default_Attribute)
    Formula = models.TextField(null=True,blank=True)
    ViewGroups = models.ManyToManyField(Group,related_name='+')
    UpdateGroups = models.ManyToManyField(Group,related_name='+')
    @property
    def Expression(self):
        res = {}
        for ft in filter_expression_columns:
            expr = getattr(self.Attribute1,ft)
            if self.Attribute2.id != Default_Attribute:
                expr = expr + ' ' + self.Condition1 + ' ' + getattr(self.Attribute2,ft)
            if self.Attribute3.id != Default_Attribute:
                expr = expr + ' ' + self.Condition2 + ' ' + getattr(self.Attribute3,ft)
            res[ft] = ' and (' + expr + ')'
        return res
    class Meta:
        unique_together = ('Class', 'Filter')

class Counters(models.Model):
    Class=models.OneToOneField(Classes,on_delete=models.CASCADE)
    CurrentCounter = models.IntegerField(default=0)

class InstancesManager(models.Manager):
    def get_queryset(self):
        qs=super(InstancesManager,self).get_queryset()
        return qs

class Instances(models.Model):
    Class = models.ForeignKey(Classes,on_delete=models.PROTECT)
    Code = models.CharField(max_length=20)
    Updatedby = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='+')
    Updated = models.DateTimeField(auto_now_add=True)
    Owner = CurrentUserField(related_name='+')
    Created = models.DateTimeField(auto_now_add=True)
    objects=InstancesManager()
    class Meta:
        unique_together = ('Class','Code')
        verbose_name='Instances'
    def __str__(self):
        return self.Code

    def save(self,*args,**kwargs):
        #check for editing rights
        user=get_current_user()
        Class_id=self.Class_id
        if user.is_superuser or Classes.objects.filter(id=Class_id,UpdateGroups__in=Group.objects.filter(user=user)).exists() \
                or (self.Owner == user and (not self.pk is None)):
            super().save(*args,**kwargs)
        else:
            if self.pk is None:
                raise Exception("User {} does not have rights to insert record of class {}".format(user.username,self.Class.Class))
            else:
                raise Exception("User {} does not have rights to update record of class {}".format(user.username,self.Class.Class))

    def delete(self,*args,**kwargs):
        #check for editing rights
        user=get_current_user()
        Class_id=self.Class_id
        if user.is_superuser or Classes.objects.filter(id=Class_id,UpdateGroups__in=Group.objects.filter(user=user)).exists()\
                or self.Owner == user:
            super().delete(*args,**kwargs)
        else:
            raise Exception("User {} does not have rights to delete record".format(user.username))

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
    def __str__(self):
        return self.char_value if not pd.isnull(self.char_value) else 'Object {}'.format(self.id)

    class Meta:
        unique_together = ('Instance','Attribute')
        verbose_name='Values'

    def save(self, *args, **kwargs): #rewrite save to check for unique & non null values
        att=self.Attribute
        #Add Datatypes Here
        Qs={DT_Integer:self.int_value,DT_Float:self.float_value,DT_String:self.char_value,DT_Text:self.text_value,
            DT_Time:self.char_value,DT_Date:self.datetime_value,DT_Datetime:self.datetime_value, DT_Instance:self.instance_value,DT_Email:self.char_value}
        Qn = {DT_Integer: 'int_value', DT_Float: 'float_value', DT_String: 'char_value', DT_Text: 'text_value',
              DT_Time: 'char_value', DT_Date:'datetime_value',DT_Datetime: 'datetime_value',DT_Instance: 'instance_value',DT_Email : 'char_value'}
        val=0
        #handle unique
        if att.UniqueAtt:
            if att.DataType.id in [DT_Integer,DT_String,DT_Date,DT_Email,DT_Time,DT_Datetime]:
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

class Values_m2m(models.Model):
    Instance = models.ForeignKey(Instances,on_delete=models.CASCADE)
    Attribute = models.ForeignKey(Attributes,on_delete=models.PROTECT)
    instance_value = models.ForeignKey(Instances,on_delete=models.CASCADE, related_name='+')
    class Meta:
        verbose_name='Values_m2m'
        unique_together=('Instance_id','Attribute_id','instance_value_id')

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

