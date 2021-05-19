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
    path('Reports/edit/<slug:pk>/',          views.ReportEdit.as_view(),        name='edit_report'),
    path('Reports/add/',                    views.ReportCreateVeiw.as_view(),   name='add_report'),
    path('Reports/add/<int:Project_id>',    views.ReportCreateVeiw.as_view(),   name='add_report'),
    path('Reports/run/<int:Report_id>',     views.ReportRun.as_view(),          name='run_report'),
    path('Projects/',                       views.projects_view,                name='projects_view'),
    path('Projects/edit/<slug:pk>',         views.ProjectEdit.as_view(),        name='edit_project'),
    path('Projects/add/',                   views.ProjectCreateVeiw.as_view(),  name='add_project'),
    path('Filters/<int:Class_id>/',         views.filters_view.as_view(),       name='filters_view'),
    path('Filters/<int:Class_id>/add/',     views.FilterCreateView.as_view(),   name='add_filter'),
    path('Filters/edit/<slug:pk>',          views.FilterUpdateView.as_view(),   name='edit_filter'),
    path('Classes/edit/<slug:pk>/',         views.ClassesUpdateView.as_view(),  name='edit_class'),
    path('Classes/add/',                    views.ClassesCreateView.as_view(),  name='add_class'),
    path('Attributes/<int:Class_id>/',      views.attributes_view,              name='attributes_view'),
    path('Attributes/edit/<slug:pk>/',      views.AttributeUpdateView.as_view(),name='edit_attribute'),
    path('Attributes/<int:Class_id>/add/',  views.AttributeCreateView.as_view(),name='add_attribute'),
    path('Templates/',                      views.emailtemplates_view.as_view(),      name='templates_view'),
    path('Templates/edit/<slug:pk>/',       views.EmailTemplateUpdateView.as_view(), name='edit_template'),
    path('Templates/add/',                  views.EmailTemplateCreateView.as_view(), name='add_template'),
    path('update_instances_table/<int:Class_id>/', views.update_instances_table,name='update_instances_table'),
    path('ClassIns/<int:Class_id>/',        views.instances,                    name='instances'),
    path('ClassIns/<int:Class_id>/<int:SaveToExl>/',        views.instances,    name='instances'),
    path('ClassIns/<int:Class_id>/<int:SaveToExl>/<int:Project_id>',        views.instances,    name='instances'),
    path('Classes/view/<int:Class_id>/<int:Instance_id>/', views.view_instance.as_view(),               name='view_instance'),
    path('Classes/view/<str:Attribute>/<int:Ref_Instance_id>/', views.view_instance.as_view(),          name='view_instance'),
    path('Classes/edit/<int:Class_id>/<int:Instance_id>/', views.edit_instance.as_view(),               name='edit_instance'),
    path('Classes/delete/<int:Class_id>/<int:Instance_id>/', views.delete_instance.as_view(), name='delete_instance'),
    path('Load/<int:Class_id>/', views.load_instances, name='loadinstances'),
    path('needlogin/',views.ProtectView.as_view(),name='needlogin'),
    path('Template/Form/<int:Class_id>/',views.FormTemplateView.as_view(),name='change_formtemplate'),
    path('Template/<str:Style>/<int:Class_id>/', views.TableTemplateView.as_view(), name='change_tabletemplate'),
    path('ajax/change_master/<int:Attribute_id>/', views.ajax_change_master, name='ajax_change_master'),
    path('ajax/classdata/<int:Class_id>/', views.ajax_get_class_data, name='ajax_get_class_data'),
    path('ajax/classcolumns/<int:Class_id>/', views.ajax_get_class_columns, name='ajax_get_class_columns'),
    path('ajax/reportdata/<int:Report_id>/', views.ajax_get_report_data, name='ajax_get_report_data'),
    path('ajax/reportcolumns/<int:Report_id>/', views.ajax_get_report_columns, name='ajax_get_report_columns'),
    path('ajax/get_attribute_options/<int:Class_id>/<int:Attribute_id>/', views.ajax_get_attribute_options, name='ajax_get_attribute_options'),
    path('send_instance_email/<int:Class_id>/',views.send_instance_email.as_view(),name='send_instance_email'),
    path('modal/send_instance_email/<int:Class_id>/', views.send_instance_email.as_view(), name='send_instance_email_modal'),
    path('modal/send_instance_email/<int:Class_id>/<int:MassEmail>/', views.send_instance_email.as_view(), name='send_instance_email_modal'),
    path('send_instance_email/<int:Class_id>/<int:Instance_id>/', views.send_instance_email.as_view(), name='send_instance_email'),
    path('download_file/<slug:pk>/', views.download_file.as_view(),name='download_file'),
]

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()