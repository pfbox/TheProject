from ut.models import Attributes,Values,Instances
import pandas as pd

class Control:
    DataType=0
    def __init__(self,Instance_id,Attribute_id,read_only=False):
        at=Attributes.objects.get(pk=self.Attribute_id)
        self.Ref_Class_id=at.Ref_Class.id
        self.Attribute=at.Attribute
        self.Instance_id=Instance_id
        self.Attribute_id = Attribute_id
        self.read_only=read_only
        self.DataType_id=at.DataType.id
        self.ValueList=at.ValueList
        self.set_value()
    def print_control(self):
        print ('Attribute',self.Attribute,'datatype=',self.DataType)

    def create_control(self):
        ro = ''
        at_id=self.Attribute_id
        value=self.Value
        if self.ReadOnly:
            ro = 'readonly'
        dt = self.DataType_id
        if dt == 1:  # int
            if self.ValuesList == '':
                return '<input class="form-control" type="number" name="{name}" {ro} value="{val}" >' \
                    .format(name=at_id, ro=ro, val=value)
            else:
                options= '<option value=0></option>'
                for v in self.ValueList.split(','):
                    options = options + '<option value="{v}">{v}</option>'.forma(v)
                return '<select class="form-control" name="{name}" {ro}> {op} </select>'.format(name=at_id, ro=ro,op=options)

        elif dt == 2:  # float
            return '<input class="form-control" type="number" step="0.01" {ro} name="{name}" value="{val}" >' \
                .format(name=at_id, ro=ro, val=value)
        elif dt == 3:  # char
            return '<input class="form-control" type="text" name="{name}" value="{val}" {ro}>' \
                .format(name=at_id, ro=ro, val=value)
        elif dt == 4:  # text
            return '<textarea class="form-control" rows="4" cols="50" name="{name}" {ro}>{val}</textarea>' \
                .format(name=at_id, ro=ro, val=value)
        elif dt == 5:  # date
            if (type(value) != str) & (not pd.isnull(value)):
                value = value.strftime("%Y-%m-%d")
            return '<input class="form-control" type="date" rows="4" cols="50" {ro} name="{name}" value="{val}">' \
                .format(name=at_id, ro=ro, val=value)
        elif dt == 6:  # instance
            ins = Instances.objects.filter(Class_id=self.Ref_Class_id).values_list('id', 'Code')
            options = '<option value=0></option>' + ' '.join(['<option value={} {}>{}</option>'.format(list(o)[0],
                 'selected' if value ==list(o)[0] else '',list(o)[1]) for o in ins])  # (value.id==list(o)[0])
            return '<select class="form-control" name="{name}" {ro}> {op} </select>'.format(name=at_id, ro=ro, op=options)
        elif dt == 9:  # instance
            pass
        else:
            raise ('DataType does not exists --create_control')

    def set_value(self):
        DataType = Attributes.objects.get(pk=self.Attribute_id).DataType.id
        if self.Instance_id == 0:
            self.value = ''
        else:
            if not Values.objects.filter(Instance_id=self.Instance_id, Attribute_id=self.Attribute_id).exists():
                self.value = ''
            else:
                v = Values.objects.get(Instance_id=self.Instance_id, Attribute_id=self.Attribute_id)
                if DataType == 1:
                    self.value = v.int_value
                elif DataType == 2:
                    self.value = v.float_value
                elif DataType == 3:
                    self.value = v.char_value
                elif DataType == 4:
                    self.value = v.text_value
                elif DataType == 5:
                    self.value = v.datetime_value
                elif DataType == 6:
                    if pd.isnull(v.instance_value):
                        self.value = 0
                    else:
                        self.value = v.instance_value.id
                elif DataType == 9:
                    self.value = v.int_value
                else:
                    raise ('Wrong DataType')
    def get_value(self):
        return self.value



class IntControl(Control):
    def __init__(self,Instance_id,Attribute_id,read_only=False):
        self.__init__(*args)