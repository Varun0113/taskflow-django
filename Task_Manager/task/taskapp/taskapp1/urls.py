from django.urls import path
from . import views

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing_page'),
    
    # Authentication
    path('task-admin/login/', views.admin_login1_view, name='admin_login'),
    path('employee/login/', views.employee_login_view, name='employee_login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # Dashboards
    path('task-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('employee/dashboard/', views.employee_dashboard, name='employee_dashboard'),
    
    # Task management (Admin)
    path('task-admin/assign-task/', views.assign_task, name='assign_task'),
    path('task-admin/tasks/', views.all_tasks, name='all_tasks'),
    path('task-admin/employees/', views.admin_employees, name='admin_employees'),
    path('task-admin/employees/add/', views.admin_add_employee, name='admin_add_employee'),
    path('task-admin/task/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('task-admin/task/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    
    # Employee task actions
    path('employee/task/<int:task_id>/update/', views.update_task_status, name='update_task_status'),
    
    # Task details (accessible by both admin and assigned employee)
    path('task/<int:task_id>/', views.task_details, name='task_details'),
]
