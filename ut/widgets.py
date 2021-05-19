from django.forms.widgets import Select
from django_select2.forms import HeavySelect2Widget
from django.forms.widgets import Media
from django.forms import RadioSelect
from django.utils.safestring import mark_safe

from django import forms

from string import Template
from django.utils.safestring import mark_safe

class PictureWidget(forms.widgets.FileInput):
    def render(self, name, value, attrs=None,**kwargs):
        html =  Template("""
        <div class="form-control custom-file">
            <input type="file" class="custom-file-input " name="$name" id="$id" accept="image/*" attr_id="$attr">        
            <label for="$id">Example file input</label>
            <img src="/media/$link" style="width:100%;hight:100%" />
        </div>
        """)
        return mark_safe(html.substitute(link=value,name=name,id=id,attr=self.attrs['attr_id']))

class ImagePreviewWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None, **kwargs):
        input_html = super().render(name, value, attrs=None)
        img_html = mark_safe(f'<br><br><img src="{value.url}"  />')
        return f'{input_html}{img_html}'

class HorizontalRadioSelect(RadioSelect):
    #template_name = 'ut:ut_inline_radio.html'
    option_template_name = 'ut:ut_inline_radio.html'
    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)
    #    css_style = 'style="display: inline-block; margin-right: 10px;"'
    #    self.renderer.inner_html = '<li ' + css_style + '>{choice_value}{sub_widgets}</li>'


class utHeavyWidget(HeavySelect2Widget):
    @property
    def media(self):
        m = Media()
        #m._css_lists.append({'screen':['https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.12/css/select2.min.css']})
        m._js_lists.append([#'https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.12/js/select2.min.js',
                            '/static/ut/js/django_select2.js'])
        return m

    def build_attrs(self, base_attrs, extra_attrs=None):
        #""" full copy form Select2.HeavyWidgetMixin"""
        default_attrs = {
            "data-ajax--url": self.get_url(),
            "data-ajax--cache": "true",
            "data-ajax--type": "GET",
            "data-minimum-input-length": 2,
        }

        if self.dependent_fields:
            default_attrs["data-select2-dependent-fields"] ="~" + "~".join(
                self.dependent_fields
            ) + "~"

        default_attrs.update(base_attrs)

        attrs = super().build_attrs(default_attrs, extra_attrs=extra_attrs)

        attrs["data-field_id"] = self.field_id

        attrs["class"] += " django-select2-heavy"
        return attrs

class DataAttributesSelect(Select):
    def __init__(self,attrs=None,choises=(),data={}):
        super(DataAttributesSelect,self).__init__(attrs=attrs,choices=choises)
        self.data = data

    def create_option(self,name, value, label, selected, index, subindex=None,attrs=None):
        option = super(DataAttributesSelect, self).create_option(name, value, label, selected, index, subindex=None,
                                                             attrs=None)  # noqa
        # adds the data-attributes to the attrs context var
        for data_attr, values in self.data.iteritems():
            option['attrs'][data_attr] = values[option['value']]
        return option