from django import forms
from .utclasses import *
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.db.models import Count
from crispy_forms.layout import Layout, Submit, Row, Column

class AttributeForm(forms.ModelForm):
    class Meta:
        model=Attributes
        fields='__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))

        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial.update({'Class_id':instance.Class.id})
            self.Class_id=instance.Class.id
            self.fields['Class'].widget.attrs['disabled'] = 'true'
            self.fields['Class'].required = False
        else:
            self.fields['Class'].required = False
            self.fields['Class'].widget.attrs['disabled'] = 'true'
    def save(self,commit=True):
        Class_id=self.initial['Class_id'];
        self.instance.Class=Classes.objects.get(pk=Class_id)
        return super(AttributeForm, self).save(commit=commit)

class ClassesForm(forms.ModelForm):
    class Meta:
        model=Classes
        fields='__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))

class UploadInstances(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Upload'))

def create_form_field(Attribute_id):
    att=Attributes.objects.get(pk=Attribute_id)
    dt=att.DataType.id
    req=att.NotNullAtt
    valueslist=att.ValuesList
    if pd.isnull(valueslist) or (valueslist == ''):
        vl = ''
    else:
        try:
            vl=json.loads(valueslist)
        except:
            print ('Could not load list of values for field',att.Attribute,'Class',att.Class.Class)
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
        field=forms.CharField(widget=forms.Textarea,required=req)
    elif dt == 5:
        field=forms.DateField(required=req)
    elif dt == 6:
        if att.Ref_Class.id!=0:
            if att.Ref_Attribute.id==0:
                ch=[(i.id,i.Code) for i in Instances.objects.filter(Class_id=att.Class.id)]
            else:
                ch=[(v.Instance_id,v.char_value) for v in Values.objects.filter(Attribute_id=att.Ref_Attribute)]
        else:
            raise Exception('No reference values for the attribute {}'.format(att.Attribute))
        ch=[(0,'')]+ch
        field=forms.ChoiceField(choices=ch,required=req)
    elif dt == 7:
        field = forms.DateTimeFieldField(required=req)
    elif dt == 9: #boolean
        field=forms.ChoiceField(choices=[(0,'False'),(1,'True')],required=req)
    elif dt == 10:
        field=forms.ChoiceField(choises=['one','two','three'],required=req)
    elif dt == 11:
        field=forms.EmailField(required=req)
    elif dt == 12:
        field=forms.FloatField(required=req)
    else:
        raise Exception('Datatype {} does not exists.'.format(dt))
    return field



class InstanceForm(forms.Form):
#    class Meta:
#        model=Instances
#        fields=['Code']
#        Code=forms.CharField(max_length=255,required=True)
    fieldclass={1:'form-group col-md-12 mb-0',2:'form-group col-md-6 mb-0',3:'form-group col-md-4 mb-0',4:'form-group col-md-3 mb-0',5:'form-group col-md-3 mb-0',6:'form-group col-md-2 mb-0'} #'form-group col-md-6 mb-0'
    def __init__(self,*args,**kwargs):
        self.Class_id=kwargs.pop('Class_id')
        self.Instance_id = kwargs.pop('Instance_id')
        super().__init__(*args, **kwargs)
        cl=Classes.objects.get(pk=self.Class_id)
        for i,att in cl.editlist.iterrows():
            self.fields[att.Attribute]=create_form_field(att.id)
            if self.Instance_id!=0:
                if att.id==0:
                    self.initial[att.Attribute] = Instances.objects.get(pk=self.Instance_id).Code
                else:
                    self.initial[att.Attribute]=get_value(self.Instance_id,att.id)
            else:
                if att.id==0:
                    self.initial['Code']=get_next_counter(self.Class_id)
        #add Save Button
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout=Layout()
        ro=df_formlayouts[df_formlayouts.Class_id==self.Class_id].groupby('Row').size()
        for r,count in ro.items():
            layout_row=Row(cssclass='form-row')
            co=df_formlayouts[(df_formlayouts.Class_id==self.Class_id)&(df_formlayouts.Row==r)]
            for i,c in co.iterrows():
                att=Attributes.objects.get(pk=c.Attribute_id)
                layout_col=Column("{}".format(att.Attribute),css_class=self.fieldclass[count])
                layout_row.append(layout_col)
            self.helper.layout.append(layout_row)

        self.helper.add_input(Submit('submit','Save'))






