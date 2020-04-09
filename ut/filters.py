from .models import Classes
import django_filters

class ClassesFilter(django_filters.FilterSet):
    class Meta:
        model = Classes
        fields = '__all__'