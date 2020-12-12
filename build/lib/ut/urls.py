from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name='ut'

urlpatterns = [
    path('', views.index, name='index'),
    path('Classes/',                        views.classes_view,                 name='classes_view'),
    path('Classes/<int:Project_id>/',       views.classes_view,                 name='classes_view'),
    path('Reports/',                        views.reports_view,                 name='reports_view'),
    path('Reports/<int:Project_id>/',       views.reports_view,                 name='reports_view'),
    path('Reports/edit/<slug:pk>/',          views.ReportEdit.as_view(),         name='edit_report'),
    path('Reports/add/',                    views.ReportCreateVeiw.as_view(),   name='add_report'),
    path('Reports/add/<int:Project_id>',    views.ReportCreateVeiw.as_view(),   name='add_report'),
    path('Reports/run/<int:Report_id>',     views.ReportRun.as_view(),          name='run_report'),
    path('Projects/',                       views.projects_view,                name='projects_view'),
    path('Projects/edit/<slug:pk>',         views.ProjectEdit.as_view(),        name='edit_project'),
    path('Projects/add/',                   views.ProjectCreateVeiw.as_view(),  name='add_project'),
    path('Attributes/<int:Class_id>/',      views.attributes_view,              name='attributes_view'),
    path('Classes/edit/<slug:pk>/',         views.ClassesUpdateView.as_view(),  name='edit_class'),
    path('Classes/add/',                    views.ClassesCreateView.as_view(),  name='add_class'),
    path('Attributes/edit/<slug:pk>/',      views.AttributeUpdateView.as_view(),name='edit_attribute'),
    path('Attributes/<int:Class_id>/add/',  views.AttributeCreateView.as_view(),name='add_attribute'),
    path('Filters/<int:Class_id>/',         views.filters,                      name='filters'),
    path('ClassIns/<int:Class_id>/',        views.instances,                    name='instances'),
    path('ClassIns/<int:Class_id>/<int:SaveToExl>/',        views.instances,    name='instances'),
    path('Classes/view/<int:Class_id>/<int:Instance_id>/', views.view_instance.as_view(),               name='view_instance'),
    path('Classes/edit/<int:Class_id>/<int:Instance_id>/', views.edit_instance.as_view(),               name='edit_instance'),
    path('Classes/delete/<int:Class_id>/<slug:pk>/', views.delete_instance.as_view(), name='delete_instance'),
    path('Load/<int:Class_id>/', views.load_instances, name='loadinstances'),
    path('needlogin/',views.ProtectView.as_view(),name='needlogin'),
    path('Template/Form/<int:Class_id>/',views.FormTemplateView.as_view(),name='change_formtemplate'),
    path('Template/<str:Style>/<int:Class_id>/', views.TableTemplateView.as_view(), name='change_tabletemplate'),
    #path('TestModalForm/', views.TestModal.as_view(), name='testmodal'),
    path('TestFormset/', views.TestFormsetFactory.as_view(), name='change_tabletemplate'),
]

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()