from django import forms
from django import forms
from .utclasses import *
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column,Field,Fieldset,MultiField,HTML,Button
from bootstrap_datepicker_plus import DatePickerInput,DateTimePickerInput
from django.urls import reverse,reverse_lazy

class ProjectForm(forms.ModelForm):
    class Meta:
        model=Projects
        fields='__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))

class ReportForm(forms.ModelForm):
    class Meta:
        model=Reports
        #fields=['ID','Report','Description']
        fields='__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))

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
            self.fields['Ref_Attribute'].queryset = Attributes.objects.filter(Class_id=instance.Ref_Class.id)
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
    file = forms.FileField()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Upload'))

from .formtemplate import *

class InstanceForm(forms.Form):
#    class Meta:
#        model=Instances
#        fields=['Code']
#        Code=forms.CharField(max_length=255,required=True)
    fieldclass={1:'form-group col-md-12 mb-0',2:'form-group col-md-6 mb-0',3:'form-group col-md-4 mb-0',4:'form-group col-md-3 mb-0',5:'form-group col-md-3 mb-0',6:'form-group col-md-2 mb-0'} #'form-group col-md-6 mb-0'
    def __init__(self,*args,**kwargs):
        self.Class_id=kwargs.pop('Class_id')
        self.Instance_id = kwargs.pop('Instance_id')
        self.ReadOnly = kwargs.pop('ReadOnly')
        if 'validation' in kwargs:
            self.Validation = kwargs.pop('validation')
        super().__init__(*args, **kwargs)

        for i,att in get_editfieldlist(self.Class_id,df_attributes).iterrows():
            if create_form_field(att):
                self.fields[att.Attribute]=create_form_field(att)
                if self.ReadOnly:
                    self.fields[att.Attribute].widget.attrs['readonly'] = "readonly"
                    self.fields[att.Attribute].widget.attrs['disabled'] = "disabled"
                    #self.fields[att.Attribute].required = False

                if self.Instance_id!=0:
                    if att.id==0:
                        self.initial[att.Attribute] = Instances.objects.get(pk=self.Instance_id).Code
                    else:
                        self.initial[att.Attribute]=get_value(self.Instance_id,att.id)
                else:
                    if att.id==0 and not self.Validation:
                        self.initial['Code']=get_next_counter(self.Class_id)
        #add Save Button
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        layout={}
        try:
            rawlayout=json.loads(Layouts.objects.get(Class_id=self.Class_id).FormLayout)
            NinRow = rawlayout['settings']['NinRow']
            master = container(mel={'top': 0, 'left': 0, 'width': NinRow, 'height': 1200}, rawlayout=rawlayout['layout'])
            master.split_by_con()
            layout=master.print_elements()
        except:
            print ("layout for the class "+ str(self.Class_id) + " was not found")

        try:
            self.helper.layout= get_layout(self.Class_id,layout,'Layout')
        except:
            print ("layout for the class "+ str(self.Class_id) + " didn't work")
            raise
            #raise
        #self.helper.layout.append(lo)
        a=""""""
            #self.helper.layout.append(layout_row)
        b=""""""
        if self.ReadOnly:
            self.helper.add_input(Submit('cancel','Cancel'))
        else:
            self.helper.add_input(Submit('submit','Save'))
            self.helper.add_input(Submit('cancel','Cancel'))

from string import Template

def get_layout(Class_id,layout,mastertype='Row',level=0):
    master=globals()[mastertype]()
    for k,v in layout.items():
        setts=k.split(':')
        clname=setts[0]
        cssclass=setts[3]
        cls = globals()[clname]
        if type(v)==dict:
            master.append(get_layout(Class_id,v,clname,level+1))
        else:
            try:
                attr=Attributes.objects.get(Class_id=Class_id,Attribute=v)
                dt=attr.DataType.id
            except ObjectDoesNotExist:
                id=0
                dt=0
            if dt in [10]:
                a=Template("""
                {% load render_table from django_tables2 %}
                <div class="tableishere"><label>$attname</label> 
                    {% if table$tb %}
                       {% render_table table$tb  %}
                    {% else %}
                       'no such table'
                    {% endif %}                
                 </div>
                """)
                master.append(HTML(a.substitute(tb=attr.id,attname=attr.Attribute)))
            elif clname=='Column': #form-group flex-grow-1 d-flex flex-column
                master.append(cls(v,css_class=cssclass))
            else:
                r=cls(css_class='form-row')
                c=Column(v,css_class=cssclass)
                r.append(c)
                master.append(r)
    return master

class Subform(forms.Field):
    def __init__(self,*args,**kwargs):
        super().__init__(self)

class FilterForm(forms.Form):
    def __init__(self,Class_id=0,filter={},*args,**kwargs):
        self.Class_id=Class_id #kwargs.pop('Class_id')
        #self.Class_id=kwargs.pop('filter')
        super().__init__(*args, **kwargs)
        #add Save Button
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout=Layout()
        r=Row()
        for i,att in get_editfieldlist(self.Class_id,df_attributes).iterrows():
            dt=DataTypes.objects.get(pk=att.DataType_id)
            if att.Filtered and dt.id not in [DT_Table]:
                if dt.FieldFilter > 1:
                    min=dt.Filter1stName
                    max=dt.Filter2ndName
                    self.fields['__min__'+att.Attribute] = create_form_field(att,usedinfilter=True)
                    self.fields['__min__'+att.Attribute].initial=filter.get('__min__'+att.Attribute)
                    self.fields['__min__'+att.Attribute].label = att.Attribute+' '+min
                    self.fields['__max__'+att.Attribute] = create_form_field(att,usedinfilter=True)
                    self.fields['__max__' + att.Attribute].initial = filter.get('__max__' + att.Attribute)
                    self.fields['__max__'+att.Attribute].label = att.Attribute+' '+max
                    r.append(Fieldset('',Row(Column('__min__'+att.Attribute),Column('__max__'+att.Attribute)),css_class='formgroup col-sm-2'))
                else:
                    self.fields[att.Attribute]=create_form_field(att,usedinfilter=True)
                    self.fields[att.Attribute].initial = filter.get(att.Attribute)
                    r.append(Column(att.Attribute,css_class='form-group col-sm-1'))
        self.helper.layout.append(r)
        self.helper.layout.append(HTML('<input type="hidden" id="sortfield" name="sortfield" value="{{sortfield}}">'))
        self.helper.add_input(Submit('submit','Filter'))
        self.helper.add_input(Submit('reset', 'Reset'))
        self.helper.add_input(Button('cancel', 'Cancel',css_class='btn-primary'))
        self.helper.add_input(Button('save_to_xls', 'Save to xls',css_class='btn-primary',onclick="location.href='"+str(reverse_lazy('ut:instances',args=(self.Class_id,1)))+"'"))
        self.helper.add_input(Button('load_from_xls', 'Load from xls',css_class='btn-primary',
                                     onclick="location.href='"+str(reverse_lazy('ut:loadinstances',args=(self.Class_id,)))+"'"))


from bootstrap_modal_forms.forms import BSModalModelForm

class BookModelForm(BSModalModelForm):
    Intfield=forms.IntegerField()
    CharField=forms.CharField(max_length=50)
