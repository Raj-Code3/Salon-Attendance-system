from django.contrib import admin
from .models import Employee, Attendance, LeaveRequest, Holiday

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ('employee_id', 'full_name', 'email', 'phone', 'gender', 'status')
    list_filter   = ('status', 'gender')
    search_fields = ('employee_id', 'full_name', 'email')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'date', 'check_in', 'check_out', 'total_hours', 'status')
    list_filter   = ('status', 'date')
    search_fields = ('employee__full_name', 'employee__employee_id')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter   = ('status', 'leave_type')
    search_fields = ('employee__full_name',)

@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('holiday_name', 'date', 'description')
