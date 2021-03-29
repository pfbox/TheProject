from django import forms
from .utclasses import *
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column,Field,Fieldset,MultiField,HTML,Button,Div,ButtonHolder
#from bootstrap_datepicker_plus import DatePickerInput,DateTimePickerInput
from django.urls import reverse,reverse_lazy
from django_select2.forms import Select2MultipleWidget,ModelSelect2MultipleWidget, ModelSelect2Widget
from django.template import Template, Context
from tinymce.widgets import TinyMCE


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


class AttributeForm(forms.ModelForm):
    class Meta:
        model=Attributes
        fields='__all__'
        widgets = {'ViewGroups' : ModelSelect2MultipleWidget(search_fields=['name__icontains'],attrs={'data-minimum-input-length': 0}),
                   'UpdateGroups' : ModelSelect2MultipleWidget(search_fields=['name__icontains'],attrs={'data-minimum-input-length': 0}),
                   }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        #self.Class_id=self.initials['Class_id']

        self.fields['Class'].queryset = Classes.objects.all()
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.Class_id = self.initial['Class']
            self.Ref_Class = self.initial['Ref_Class']
            self.initial.update({'Class_id':instance.Class.id})
            self.Class_id=instance.Class.id
            self.fields['Class'].widget.attrs['disabled'] = 'true'
            self.fields['Class'].required = False
            self.fields['Ref_Attribute'].queryset = Attributes.objects.filter(
                Q(Class_id=self.Ref_Class) | Q(Class_id=0))
            self.fields['InternalAttribute'].queryset = Attributes.objects.filter(
                Q(Class_id=self.Class_id) | Q(Class_id=0))
        else:
            self.Class_id=0
            self.Ref_Class=0
            self.fields['Class'].required = False
            self.fields['Class'].widget.attrs['disabled'] = 'true'
            self.fields['Ref_Class'].queryset = Classes.objects.all()
            self.fields['Ref_Attribute'].queryset = Attributes.objects.all()
            self.fields['InternalAttribute'].queryset = Attributes.objects.filter(Q(Class_id=self.Class_id)| Q(Class_id=0))


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
            'DeleteGroups': ModelSelect2MultipleWidget(search_fields=['name__icontains'],
                                                       attrs={'data-minimum-input-length': 0}),
            'InsertGroups': ModelSelect2MultipleWidget(search_fields=['name__icontains'],
                                                       attrs={'data-minimum-input-length': 0}),
            'RightsFilteredByClass': ModelSelect2MultipleWidget(search_fields=['Class__icontains'],
                                                       attrs={'data-minimum-input-length': 0})
                   }
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

class UploadInstances(forms.Form):
    #error_choises=((0,'Ignore'),(1,'Raise'))
    file = forms.FileField()
    Commit = forms.ChoiceField(choices=((100,'Every 100'),(1000,'Every 1k'),(10000,'Every 10k')))
    Errors = forms.ChoiceField(choices=(('ignore','Ignore'),('raise','Raise')))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Upload'))

from .formtemplate import *

from django_select2 import forms as s2forms
class InstanceForm(forms.Form):
    fieldclass={1:'form-group col-md-12 mb-0',2:'form-group col-md-6 mb-0',3:'form-group col-md-4 mb-0',4:'form-group col-md-3 mb-0',5:'form-group col-md-3 mb-0',6:'form-group col-md-2 mb-0'} #'form-group col-md-6 mb-0'
    def __init__(self,*args,**kwargs):
        print (datetime.now(),'form __init__')
        self.Class_id=kwargs.pop('Class_id')
        self.Instance_id = kwargs.pop('Instance_id')
        self.ReadOnly = kwargs.pop('ReadOnly')
        if 'validation' in kwargs:
            self.Validation = kwargs.pop('validation')
        if 'next' in kwargs:
            self.Next = kwargs.pop('next')
        if 'defaults' in kwargs:
            self.Defaults=kwargs.pop('defaults')
        else:
            self.Defaults={}
        super().__init__(*args, **kwargs)

        # get form initial values
        #initrow={}
        it=datetime.now()
        if self.Instance_id!=0:
            initrow=get_instance_values(self.Class_id,self.Instance_id)
        else:
            if len(self.Defaults)>0:
                initrow=self.Defaults
            else:
                initrow={}
        print ('initrow done in:',datetime.now()-it)

        old=datetime.now()
        for att in get_editfieldlist(self.Class_id).iterator():
            if create_form_field_check(att):
                print (datetime.now()-old,'--before create field')
                self.fields[att.Attribute]=create_form_field(att,values=initrow,validation=self.Validation)
                self.fields[att.Attribute].label = att.Attribute
                self.fields[att.Attribute].widget.attrs['attr_id']=att.id
                print (datetime.now()-old,'--before masterattribute_id')
                if att.DataType_id == DT_Instance:
                    if att.MasterAttribute_id > 0:
                        self.fields[att.Attribute].widget.attrs['masterattr_id']=att.MasterAttribute_id
                    print(datetime.now() - old, '--before hierarchy and lookup')
                    widgetclass=self.fields[att.Attribute].widget.attrs.get('class')
                    widgetclass= '' if pd.isnull(self.fields[att.Attribute].widget.attrs.get('class')) else widgetclass
                    self.fields[att.Attribute].widget.attrs['class']= widgetclass \
                        +(' hierarchy_trigger' if att.hierarchy_trigger>0 else '') + (' lookup_trigger' if att.lookup_trigger>0 else '')
                print (datetime.now()-old,'-- before Readonly')
                if self.ReadOnly or att.DataType_id in [DT_Lookup]:
                    self.fields[att.Attribute].widget.attrs['readonly'] = "readonly"
                    self.fields[att.Attribute].widget.attrs['disabled'] = "disabled"
                    #self.fields[att.Attribute].required = False
                print (datetime.now()-old,'-- before manytomany')
                if self.Instance_id!=0:
                    if att.DataType_id in [DT_ManyToMany]:
                        self.initial[att.Attribute]=list(Values_m2m.objects.filter(Instance_id=self.Instance_id,Attribute_id=att.id).values_list('instance_value_id',flat=True))
                    else:
                        self.initial[att.Attribute]=initrow[att.Attribute]
                else:
                    if not self.Validation:
                        if att.id==0:
                            self.initial['Code']=get_next_counter(self.Class_id)
                        if len(self.Defaults)>0:
                            if att.Attribute in self.Defaults:
                               self.initial[att.Attribute] = self.Defaults[att.Attribute]
            new=datetime.now()
            diff=new-old
            print (diff,att.Attribute)
            old=new

        #add Save Button
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.attrs = {'data-instance-id':'{}'.format(self.Instance_id),'data-class-id':'{}'.format(self.Class_id),
                             'data-send-instance-email-link':reverse_lazy('ut:send_instance_email_modal',args=(self.Class_id,))}
        self.helper.form_class = 'instanceform'
        self.helper.labels_uppercase = True
        layout={}
        try:
            rawlayout=json.loads(Layouts.objects.get(Class_id=self.Class_id).FormLayout)
            NinRow = rawlayout['settings']['NinRow']
            lo= []
            for obj in rawlayout['layout']:
                if obj['name'] in get_editfieldlist(self.Class_id).values_list('Attribute',flat=True):
                    lo.append(obj)
            master = container(mel={'top': 0, 'left': 0, 'width': NinRow, 'height': 1200}, rawlayout=lo)
            master.split_by_con()
            layout=master.print_elements()
        except:
            print ("layout for the class "+ str(self.Class_id) + " was not found")

        self.helper.layout=Layout(HTML("""
        <div class="modal-header"><h5 class="modal-title" id="exampleModalLongTitle">  Edit instance </h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>
        """))
        try:
            self.helper.layout.append(Div(get_layout(self.Class_id,layout,'Layout'),css_class='modal-body'))
        except:
            print ("layout for the class "+ str(self.Class_id) + " didn't work")
            raise
            #raise
        #self.helper.layout.append(lo)
        a=""""""
            #self.helper.layout.append(layout_row)
        b=""""""
        if self.ReadOnly:
            Buttons = ButtonHolder(
                Button(value='Close',name='close',css_class='btn-secondary',data_dismiss='modal'),
                css_class='buttonHolder modal-footer'
            )
        else:
            Buttons = ButtonHolder(
                Button(value='Save',name='save',css_class='btn btn-primary savechanges',css_id='save'),
                Button(value='Save&Next',name='savenext',css_class='btn btn-primary savechanges',css_id='savenext') if self.Instance_id!=0
                else Button(value='Save&New',css_class='btn btn-primary savechanges',name='savenext',css_id='savenext'),
                Button(value='Send e-mail',name='sendemail',css_class='btn btn-primary send-instance-email',css_id='sendemail'),
                Button(value='Close',name='close',css_class='btn-secondary',data_dismiss='modal'),
                css_class='buttonHolder modal-footer'
            )
        self.helper.layout.append(Buttons)
        self.helper.layout.append(HTML('<div class="form-errors">{{ form_errors }}</div>'))
        print (datetime.now(),'form created')

from string import Template as strTemplate

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
                refattr=Attributes.objects.get(id=attr.Ref_Attribute_id).Attribute
                dt=attr.DataType.id
            except ObjectDoesNotExist:
                id=0
                dt=0
            if dt in [DT_Table]:
                a=strTemplate("""
                $attname
                {% with Class_id=$refclass Ref_Attribute="$refattr" %}
                    {% include "ut/datatable.html" %}
                {% endwith%}
                """)
                master.append(HTML(a.substitute(tb=attr.id,attname=attr.Attribute,refclass=attr.Ref_Class_id,refattr=refattr)))
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
        self.helper.attrs = {'class':'classtablefilter','data-class_id':Class_id, 'onsubmit':'return false'}
        self.helper.form_method = 'get'
        self.helper.layout=Layout()
        r=Row()
        for f in Filters.objects.filter(Q(Class_id=self.Class_id)|Q(Class_id=0)):
            att=get_attribute(f.Attribute1.id)
            if f.FilterType == FT_MinMax:
                self.fields['__min__'+f.Filter] = create_form_field(att,usedinfilter=True,fn=f.Filter)
                self.fields['__min__'+f.Filter].initial=filter.get('__min__'+f.Filter)
                self.fields['__min__'+f.Filter].label = False
                self.fields['__min__' + f.Filter].help_text = 'min'
                self.fields['__min__' + f.Filter].widget.attrs['data-filter-id']=f.id
                self.fields['__min__' + f.Filter].widget.attrs['data-filter-type'] = 'min'
                self.fields['__min__' + f.Filter].widget.attrs['class'] = 'filterfield'
                self.fields['__max__'+f.Filter] = create_form_field(att,usedinfilter=True,fn=f.Filter)
                self.fields['__max__'+f.Filter].initial = filter.get('__max__' + f.Filter)
                self.fields['__max__'+f.Filter].label = False
                self.fields['__max__' + f.Filter].help_text = 'max'
                self.fields['__max__' + f.Filter].widget.attrs['data-filter-id']=f.id
                self.fields['__max__' + f.Filter].widget.attrs['data-filter-type'] = 'max'
                self.fields['__max__' + f.Filter].widget.attrs['class'] = 'filterfield'
                r.append(Div(HTML('<label>{}</label>'.format(f.Filter)),
                             Row(Column('__min__'+f.Filter),
                                 Column('__max__'+f.Filter)
                                 )
                             ,css_class='form-group col-sm-{}'.format(f.Size)))
            else:
                self.fields[f.Filter]=create_form_field(att,usedinfilter=True,fn=f.Filter)
                self.fields[f.Filter].initial = filter.get(f.Filter)
                self.fields[f.Filter].widget.attrs['data-filter-id']=f.id
                self.fields[f.Filter].widget.attrs['data-filter-type'] = f.FilterType
                self.fields[f.Filter].widget.attrs['class'] = 'filterfield'
                r.append(Column(f.Filter,css_class='col-sm-{}'.format(f.Size)))

        self.helper.layout.append(r)
        #self.helper.layout.append(HTML('<input type="hidden" id="sortfield" name="sortfield" value="{{sortfield}}">'))
        #self.helper.add_input(Submit('submit','Filter'))
        #self.helper.add_input(Submit('reset', 'Reset'))
        #self.helper.add_input(Button('cancel', 'Cancel',css_class='btn-primary'))
        #self.helper.add_input(Button('save_to_xls', 'Save to xls',css_class='btn-primary',onclick="location.href='"+str(reverse_lazy('ut:instances',args=(self.Class_id,1)))+"'"))
        #self.helper.add_input(Button('load_from_xls', 'Load from xls',css_class='btn-primary',
        #                             onclick="location.href='"+str(reverse_lazy('ut:loadinstances',args=(self.Class_id,)))+"'"))


#from bootstrap_modal_forms.forms import BSModalModelForm

#class BookModelForm(BSModalModelForm):
#    Intfield=forms.IntegerField()
#    CharField=forms.CharField(max_length=50)


class SendInstanceEmailForm(forms.Form):
    to = forms.EmailField(required=True)
    cc = forms.EmailField(required=False)
    subject = forms.CharField(required=True,max_length=255)
    text_body = forms.CharField(widget=TinyMCE(),required=False)
    def __init__(self,*args,**kwargs):
        self.Class_id=kwargs.pop('Class_id')
        if 'instance' in kwargs.keys():
            self.instance=kwargs.pop('instance')


        self.ToTemplate=''
        self.CcTemplate=''
        self.SubjectTemplate=''
        self.BodyTemplate=''

        try:
            self.Template=Classes.objects.get(id=self.Class_id).DefaultEmailTemplate
            fieldmatch=re.compile(r'{{ *(".*?") *}}')
            self.ToTemplate=fieldmatch.sub(lambda x: '{{ '+x.group(1).replace(" ","_").replace('"','') + ' }}',value_if_null(self.Template.ToTemplate,''))
            self.CcTemplate=fieldmatch.sub(lambda x: '{{ '+x.group(1).replace(" ","_").replace('"','') + ' }}',value_if_null(self.Template.CcTemplate,''))
            self.SubjectTemplate=fieldmatch.sub(lambda x: '{{ '+x.group(1).replace(" ","_").replace('"','') + ' }}',value_if_null(self.Template.SubjectTemplate,''))
            self.BodyTemplate=fieldmatch.sub(lambda x: '{{ '+x.group(1).replace(" ","_").replace('"','') + ' }}',value_if_null(self.Template.Template,''))
        except:
            pass


        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.attrs = {'class':'sendemail','data-class-id':self.Class_id,'onsubmit':'return false',
                             'data-send-instance-email-link':reverse_lazy('ut:send_instance_email_modal',args=(self.Class_id,))}
        self.fields['to'].initial = Template(self.ToTemplate).render(context=Context(self.instance))
        self.fields['cc'].initial = Template(self.CcTemplate).render(context=Context(self.instance))
        self.fields['subject'].initial = Template(self.SubjectTemplate).render(context=Context(self.instance))
        self.fields['text_body'].initial = Template(self.BodyTemplate).render(context=Context(self.instance))
        #self.fields['text_body'].widget =

        self.helper.layout=Layout()
        self.helper.layout=Layout(HTML("""
        <div class="modal-header"><h5 class="modal-title" id="exampleModalLongTitle">  Send Instance Email </h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>
        """))

        self.helper.layout.append(Fieldset('','to','cc','subject','text_body',css_class='modal-body'))

        Buttons = ButtonHolder(
            Button(value='Send', name='send', css_class='btn btn-primary send-instance-email-btn', css_id='save'),
            Button(value='Cancel', name='cancel', css_class='btn-secondary', data_dismiss='modal'),
            css_class='buttonHolder modal-footer'
        )
        self.helper.layout.append(Buttons)

class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplates
        fields = '__all__'
        widgets = {'text_body': TinyMCE}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))

