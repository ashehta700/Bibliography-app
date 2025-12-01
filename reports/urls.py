from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('report/<str:pk>/', views.report_detail, name='report_detail'),
    path('secure_pdf/<str:token>/', views.secure_pdf_viewer, name='secure_pdf'),
    path('secure_pdf_file/<str:token>/', views.secure_pdf_file, name='secure_pdf_file'),
    # for download file 
    path('download/<str:token>/', views.secure_pdf_download, name='secure_pdf_download'),

    
    
    # for CRUD's operations for the reports
    path('admin/reports/', views.report_admin_list, name='report_admin_list'),
    path('admin/reports/add/', views.report_create, name='report_create'),
    path('admin/reports/<str:Library_Reference>/edit/', views.report_update, name='report_update'),

    # path('admin/reports/add/', views.report_create, name='report_create'),
    # path('admin/reports/<str:pk>/edit/', views.report_update, name='report_update'),
    path('admin/reports/<str:pk>/delete/', views.report_delete, name='report_delete'),


]

