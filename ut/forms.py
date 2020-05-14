from django import forms
from django import forms
from .utclasses import *
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column,Field,Fieldset,MultiField,HTML
from bootstrap_datepicker_plus import DatePickerInput

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

def create_form_field(Attribute_id,usedinfilter=False,filter={}):
    att=Attributes.objects.get(pk=Attribute_id)
    FieldName=att.Attribute
    dt=att.DataType.id
    if usedinfilter:
        req=False
    else:
        req=att.NotNullAtt
    valueslist=att.ValuesList
    if pd.isnull(valueslist) or (valueslist == ''):
        vl = ''
    else:
        try:
            vl=json.loads(valueslist)
        except:
            print ('Could not load list of values for field',FieldName,'Class',att.Class.Class)
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
    elif dt == 10: #list Do not use
        return False
    elif dt == 11: #EmailField
        field=forms.EmailField(required=req)
    elif dt == 12: #Currency
        field=forms.FloatField(required=req)
    else:
        raise Exception('Datatype {} does not exists.'.format(dt))
    return field

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
        super().__init__(*args, **kwargs)
        cl=Classes.objects.get(pk=self.Class_id)
        for i,att in cl.editlist.iterrows():
            if create_form_field(att.id):
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
        try:
            rawlayout=json.loads(Layouts.objects.get(Class_id=self.Class_id).FormLayout)
            NinRow = rawlayout['settings']['NinRow']
            master = container(mel={'top': 0, 'left': 0, 'width': NinRow, 'height': 1200}, rawlayout=rawlayout['layout'])
            master.split_by_con()
            layout=master.print_elements()
        except:
            print ("layout for the class "+ str(self.Class_id) + " was not found")

        try:
            self.helper.layout= get_layout(cl,layout,'Layout')
        except:
            raise
            print ("layout for the class "+ str(self.Class_id) + " didn't work")
            #raise
        #self.helper.layout.append(lo)
        a=""""""
            #self.helper.layout.append(layout_row)
        b=""""""
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

bootstrap_textarea_100="""
<div id="content" class="margin-from-nav">
    <div class="container">
        <form>
            <div class="row">
                <div class="col-12 col-sm-12 col-md-12 col-lg-6 col-xl-6">
                    <div class="form-group">
                        <label for="inputName1">Imię</label>
                        <input type="text" class="form-control" id="inputName1" placeholder="Imie">
                    </div>
                    <div class="form-group">
                        <label for="inputName2">Nazwisko</label>
                        <input type="text" class="form-control" id="inputName2" placeholder="Nazwisko">
                    </div>                  
                    <div class="form-group">
                        <label for="inputEmail4">Adres e-mail</label>
                        <input type="email" class="form-control" id="inputEmail4" placeholder="Email">
                    </div>
                    <div class="form-group">
                        <label class="mr-sm-2" for="inlineFormCustomSelect">Temat zapytania</label>
                        <select class="custom-select mr-sm-2" id="inlineFormCustomSelect">
                            <option selected>Wybierz temat...</option>
                            <option value="1">One</option>
                            <option value="2">Two</option>
                            <option value="3">Three</option>
                        </select>
                    </div>
                </div>
                <div class="col-12 col-sm-12 col-md-12 col-lg-6 col-xl-6 d-flex flex-column">
                    <div class="form-group flex-grow-1 d-flex flex-column">
                        <label for="exampleFormControlTextarea1">Treść wiadomości</label>
                        <textarea class="form-control flex-grow-1" id="exampleFormControlTextarea1" rows="8"></textarea>
                    </div>
                </div>          
            </div>
        </form>     
    </div>
</div>
"""
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
        cl=Classes.objects.get(pk=self.Class_id)
        for i,att in cl.editlist.iterrows():
            dt=DataTypes.objects.get(pk=att.DataType_id)
            if dt.id in [10]:
                pass
            elif dt.FieldFilter > 1:
                min=dt.Filter1stName
                max=dt.Filter2ndName
                self.fields['__min__'+att.Attribute] = create_form_field(att.id,usedinfilter=True)
                self.fields['__min__'+att.Attribute].initial=filter.get('__min__'+att.Attribute)
                self.fields['__min__'+att.Attribute].label = att.Attribute+' '+min
                self.fields['__max__'+att.Attribute] = create_form_field(att.id,usedinfilter=True)
                self.fields['__max__' + att.Attribute].initial = filter.get('__max__' + att.Attribute)
                self.fields['__max__'+att.Attribute].label = att.Attribute+' '+max
                r.append(Fieldset('',Row(Column('__min__'+att.Attribute),Column('__max__'+att.Attribute)),css_class='formgroup col-sm-2'))
            else:
                self.fields[att.Attribute]=create_form_field(att.id,usedinfilter=True)
                self.fields[att.Attribute].initial = filter.get(att.Attribute)
                r.append(Column(att.Attribute,css_class='form-group col-sm-1'))
        self.helper.layout.append(r)
        self.helper.layout.append(HTML('<input type="hidden" id="sortfield" name="sortfield" value="{{sortfield}}">'))
        self.helper.add_input(Submit('submit','Filter'))
        self.helper.add_input(Submit('reset', 'Reset'))
        self.helper.add_input(Submit('cancel', 'Cancel'))
        self.helper.add_input(Submit('save_to_xls', 'Save to xls'))
        self.helper.add_input(Submit('load_from_xls', 'Load from xls'))


