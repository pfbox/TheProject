from django.urls import path


from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('Classes/',                        views.classes_view,                 name='classes_view'),
    path('Classes2/',                       views.classes_view2,                name='classes_view2'),
    path('Classestree/',                    views.classestree_view,             name='classestree_view'),
    path('Attributes/<int:Class_id>/',      views.attributes_view,              name='attributes_view'),
    path('Classes/edit/<slug:pk>/',         views.ClassesUpdateView.as_view(),  name='edit_class'),
    path('Classes/add/',                    views.ClassesCreateView.as_view(),  name='add_class'),
    path('Attributes/edit/<slug:pk>/',      views.AttributeUpdateView.as_view(),name='edit_attribute'),
    path('Attributes/<int:Class_id>/add/',  views.AttributeCreateView.as_view(),name='add_attribute'),
#    path('<str:tablename>/',views.table,name='table'),
#    path('ClassAtt/<int:Class_id>/', views.showemptyform,name='showemptyform'),
    path('Filters/<int:Class_id>/',         views.filters,                      name='filters'),
    path('ClassIns/<int:Class_id>/',        views.instances,                    name='instances'),
    path('ClassIns/<int:Class_id>/<int:SaveToExl>/',        views.instances,                    name='instances'),
#    path('Classes/save/<int:Class_id>/<int:Instance_id>/', views.save_instance, name='save_instance'),
    path('Classes/edit/<int:Class_id>/<int:Instance_id>/', views.edit_instance, name='edit_instance'),
    path('Template/Form/<int:Class_id>/',                  views.change_formtemplate,name='change_formtemplate'),
    path('Template/Table/<int:Class_id>/',                 views.change_tabletemplate, name='change_tabletemplate'),
    path('Load/<int:Class_id>/', views.load_instances, name='loadinstances'),
]
