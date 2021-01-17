from django import forms
from django import forms
from .utclasses import *
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column,Field,Fieldset,MultiField,HTML,Button,Div
from bootstrap_datepicker_plus import DatePickerInput,DateTimePickerInput
from django.urls import reverse,reverse_lazy
from django_select2.forms import Select2MultipleWidget,ModelSelect2MultipleWidget

class ProjectForm(forms.ModelForm):
    class Meta:
        model=Projects
        fields='__all__'
        widgets = {'Classes_m2m': ModelSelect2MultipleWidget(search_fields=['Class__icontains'],attrs={'data-minimum-input-length': 0}),
                   'Reports_m2m': ModelSelect2MultipleWidget(search_fields=['Report__icontains'],attrs={'data-minimum-input-length': 0}),
                   'ViewGroups': ModelSelect2MultipleWidget(search_fields=['name__icontains'],attrs={'data-minimum-input-length': 0}),
                   'UpdateGroups': ModelSelect2MultipleWidget(search_fields=['name__icontains'],attrs={'data-minimum-input-length': 0}),
                   }
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


class FilterEditForm(forms.ModelForm):
    class Meta:
        model = Filters
        fields = '__all__'
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))

        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.initial.update({'Class_id':instance.Class.id})
            self.Class_id=instance.Class.id
        else:
            self.Class_id = kwargs['initial']['Class_id']


        self.fields['Attribute1'].queryset = Attributes.objects.filter(Q(Class_id=self.Class_id) | Q(Class_id=0))
        self.fields['Attribute2'].queryset = Attributes.objects.filter(Q(Class_id=self.Class_id) | Q(Class_id=0))
        self.fields['Attribute3'].queryset = Attributes.objects.filter(Q(Class_id=self.Class_id) | Q(Class_id=0))


        self.fields['Class'].widget.attrs['disabled'] = 'true'
        self.fields['Class'].required = False

    def save(self,commit=True):
        Class_id=self.initial['Class_id'];
        self.instance.Class=Classes.objects.get(pk=Class_id)
        return super(FilterEditForm, self).save(commit=commit)


class AttributeForm(forms.ModelForm):
    class Meta:
        model=Attributes
        fields='__all__'
        widgets = {'ViewGroups' : ModelSelect2MultipleWidget(search_fields=['name__icontains'],attrs={'data-minimum-input-length': 0}),
                   'UpdateGroups' : ModelSelect2MultipleWidget(search_fields=['name__icontains'],attrs={'data-minimum-input-length': 0}),
                   }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            self.fields['Ref_Attribute'].queryset = Attributes.objects.filter(Q(Class_id=instance.Ref_Class.id)|Q(Class_id=0))
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
        widgets = {
            'ViewGroups' : ModelSelect2MultipleWidget(search_fields=['name__icontains'],attrs={'data-minimum-input-length': 0}),
                   'UpdateGroups' : ModelSelect2MultipleWidget(search_fields=['name__icontains'],attrs={'data-minimum-input-length': 0}),
                   }
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
    fieldclass={1:'form-group col-md-12 mb-0',2:'form-group col-md-6 mb-0',3:'form-group col-md-4 mb-0',4:'form-group col-md-3 mb-0',5:'form-group col-md-3 mb-0',6:'form-group col-md-2 mb-0'} #'form-group col-md-6 mb-0'
    def __init__(self,*args,**kwargs):
        self.Class_id=kwargs.pop('Class_id')
        self.Instance_id = kwargs.pop('Instance_id')
        self.ReadOnly = kwargs.pop('ReadOnly')
        if 'validation' in kwargs:
            self.Validation = kwargs.pop('validation')
        super().__init__(*args, **kwargs)

        # get form initial values
        initrow={}
        if self.Instance_id!=0:
            sql = create_val_sql(self.Instance_id,self.Class_id)
            with con.cursor() as cursor:
                cursor.execute(sql)
                initrow=dict(zip([column[0] for column in cursor.description], cursor.fetchone()))
            pass

        for i,att in get_editfieldlist(self.Class_id,df_attributes).iterrows():
            if create_form_field_check(att):
                self.fields[att.Attribute]=create_form_field(att,values=initrow)
                self.fields[att.Attribute].widget.attrs['attr_id']=att.id
                self.fields[att.Attribute].widget.attrs['masterattr_id']=att.MasterAttribute_id
                self.fields[att.Attribute].widget.attrs['class']= \
                    'hierarchy_trigger' if att.hierarchy_trigger>0 else '' +  'lookup_trigger'    if att.lookup_trigger>0 else ''

                if self.ReadOnly or att.DataType_id in [DT_Lookup]:
                    self.fields[att.Attribute].widget.attrs['readonly'] = "readonly"
                    self.fields[att.Attribute].widget.attrs['disabled'] = "disabled"
                    #self.fields[att.Attribute].required = False

                if self.Instance_id!=0:
                    if att.DataType_id in [DT_ManyToMany]:
                        self.initial[att.Attribute]=list(Values_m2m.objects.filter(Instance_id=self.Instance_id,Attribute_id=att.id).values_list('instance_value_id',flat=True))
                    else:
                        self.initial[att.Attribute]=initrow[att.Attribute]
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


class InstanceFilterForm(forms.Form):
    def __init__(self,Class_id=0,filter={},*args,**kwargs):
        self.Class_id=Class_id #kwargs.pop('Class_id')
        #self.Class_id=kwargs.pop('filter')
        super().__init__(*args, **kwargs)
        #add Save Button
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout=Layout()
        r=Row()
        for f in Filters.objects.filter(Q(Class_id=self.Class_id)|Q(Class_id=0)):
            att=get_attribute(f.Attribute1.id,df_attributes)
            Attribute=f.Attribute1.Attribute
            if f.FilterType == FT_MinMax:
                self.fields['__min__'+f.Filter] = create_form_field(att,usedinfilter=True,fn=f.Filter)
                self.fields['__min__'+f.Filter].initial=filter.get('__min__'+f.Filter)
                self.fields['__min__'+f.Filter].label = False
                self.fields['__min__' + f.Filter].help_text = 'min'
                self.fields['__max__'+f.Filter] = create_form_field(att,usedinfilter=True,fn=f.Filter)
                self.fields['__max__'+f.Filter].initial = filter.get('__max__' + f.Filter)
                self.fields['__max__'+f.Filter].label = False
                self.fields['__max__' + f.Filter].help_text = 'max'
                r.append(Div(HTML('<label>{}</label>'.format(f.Filter)),
                             Row(Column('__min__'+f.Filter),
                                 Column('__max__'+f.Filter)
                                 )
                             ,css_class='form-group col-sm-{}'.format(f.Size)))
            else:
                self.fields[f.Filter]=create_form_field(att,usedinfilter=True,fn=f.Filter)
                self.fields[f.Filter].initial = filter.get(f.Filter)
                r.append(Column(f.Filter,css_class='col-sm-{}'.format(f.Size)))

        self.helper.layout.append(r)
        self.helper.layout.append(HTML('<input type="hidden" id="sortfield" name="sortfield" value="{{sortfield}}">'))
        self.helper.add_input(Submit('submit','Filter'))
        self.helper.add_input(Submit('reset', 'Reset'))
        self.helper.add_input(Button('cancel', 'Cancel',css_class='btn-primary'))
        self.helper.add_input(Button('save_to_xls', 'Save to xls',css_class='btn-primary',onclick="location.href='"+str(reverse_lazy('ut:instances',args=(self.Class_id,1)))+"'"))
        self.helper.add_input(Button('load_from_xls', 'Load from xls',css_class='btn-primary',
                                     onclick="location.href='"+str(reverse_lazy('ut:loadinstances',args=(self.Class_id,)))+"'"))


#from bootstrap_modal_forms.forms import BSModalModelForm

#class BookModelForm(BSModalModelForm):
#    Intfield=forms.IntegerField()
#    CharField=forms.CharField(max_length=50)
