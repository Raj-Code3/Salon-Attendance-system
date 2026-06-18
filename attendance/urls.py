from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/',    views.login_view,   name='login'),
    path('logout/',   views.logout_view,  name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Attendance
    path('attendance/',          views.attendance_list, name='attendance_list'),
    path('attendance/check-in/', views.check_in,        name='check_in'),
    path('attendance/check-out/',views.check_out,       name='check_out'),

    # Employees (admin)
    path('employees/',                views.employee_list,   name='employee_list'),
    path('employees/status/', views.employee_status_list, name='employee_status_list'),
    path('employees/add/',            views.employee_add,    name='employee_add'),
    path('employees/<int:pk>/',       views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/edit/',  views.employee_edit,   name='employee_edit'),
    path('employees/<int:pk>/delete/',views.employee_delete, name='employee_delete'),
    path('holidays/<str:date_str>/toggle/', views.toggle_sunday, name='toggle_sunday'),

    # Profile
    path('profile/', views.profile_view, name='profile'),

    # Leave
    path('leave/apply/',                     views.leave_apply,  name='leave_apply'),
    path('leave/my/',                        views.my_leaves,    name='my_leaves'),
    path('calendar/', views.my_calendar, name='my_calendar'),
    path('leave/all/',                       views.leave_list,   name='leave_list'),
    path('leave/<int:pk>/<str:action>/',     views.leave_action, name='leave_action'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # Holidays
    path('holidays/',              views.holiday_list,   name='holiday_list'),
    path('holidays/add/',          views.holiday_add,    name='holiday_add'),
    path('holidays/<int:pk>/delete/', views.holiday_delete, name='holiday_delete'),
]
