from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name='ut'

urlpatterns = [
    path('', views.index, name='index'),
    path('Classes/',                        views.classes_view,                 name='classes_view'),
    path('Classes2/',                       views.classes_view2,                name='classes_view2'),
    path('Classestree/',                    views.classestree_view,             name='classestree_v iew'),
    path('Attributes/<int:Class_id>/',      views.attributes_view,              name='attributes_view'),
    path('Classes/edit/<slug:pk>/',         views.ClassesUpdateView.as_view(),  name='edit_class'),
    path('Classes/add/',                    views.ClassesCreateView.as_view(),  name='add_class'),
    path('Attributes/edit/<slug:pk>/',      views.AttributeUpdateView.as_view(),name='edit_attribute'),
    path('Attributes/<int:Class_id>/add/',  views.AttributeCreateView.as_view(),name='add_attribute'),
    path('Filters/<int:Class_id>/',         views.filters,                      name='filters'),
    path('ClassIns/<int:Class_id>/',        views.instances,                    name='instances'),
    path('ClassIns/<int:Class_id>/<int:SaveToExl>/',        views.instances,    name='instances'),
    path('Classes/edit/<int:Class_id>/<int:Instance_id>/', views.edit_instance, name='edit_instance'),
    path('Load/<int:Class_id>/', views.load_instances, name='loadinstances'),
    path('needlogin/',views.ProtectView.as_view(),name='needlogin'),
    path('Template/Form/<int:Class_id>/',views.FormTemplateView.as_view(),name='change_formtemplate'),
    path('Template/<str:Style>/<int:Class_id>/', views.TableTemplateView.as_view(), name='change_tabletemplate'),
    path('TestFormset/', views.TestFormsetFactory.as_view(), name='change_tabletemplate'),
]
