from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import HttpResponse
from datetime import date, datetime, timedelta
import json

from .models import Employee, Attendance, LeaveRequest, Holiday
from .forms import (LoginForm, EmployeeForm, ProfileForm,
                    LeaveRequestForm, HolidayForm, AttendanceFilterForm)


def is_admin(user):
    return user.is_staff or user.is_superuser


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'attendance/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out successfully.')
    return redirect('login')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today = date.today()

    if is_admin(request.user):
        employees      = Employee.objects.filter(status='Active')
        total_emp      = employees.count()
        present_today  = Attendance.objects.filter(date=today, status__in=['Present', 'Late']).count()
        late_today     = Attendance.objects.filter(date=today, status='Late').count()
        absent_today   = total_emp - Attendance.objects.filter(date=today).exclude(status='Absent').count()
        pending_leaves = LeaveRequest.objects.filter(status='Pending').count()
        recent_att     = Attendance.objects.select_related('employee').filter(date=today).order_by('-check_in')[:10]
        upcoming_holidays = Holiday.objects.filter(date__gte=today).order_by('date')[:5]

        chart_labels  = []
        chart_present = []
        chart_absent  = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            chart_labels.append(d.strftime('%d %b'))
            p = Attendance.objects.filter(date=d, status__in=['Present', 'Late']).count()
            chart_present.append(p)
            chart_absent.append(max(0, total_emp - p))

        context = {
            'is_admin':          True,
            'total_employees':   total_emp,
            'present_today':     present_today,
            'absent_today':      max(0, absent_today),
            'late_today':        late_today,
            'pending_leaves':    pending_leaves,
            'recent_attendance': recent_att,
            'upcoming_holidays': upcoming_holidays,
            'chart_labels':      json.dumps(chart_labels),
            'chart_present':     json.dumps(chart_present),
            'chart_absent':      json.dumps(chart_absent),
            'attendance_pct':    int(present_today / total_emp * 100) if total_emp else 0,
        }
    else:
        try:
            employee = request.user.employee
        except Employee.DoesNotExist:
            messages.error(request, 'Employee profile not found.')
            return redirect('login')

        today_att         = Attendance.objects.filter(employee=employee, date=today).first()
        my_leaves         = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')[:5]
        my_attendance     = Attendance.objects.filter(employee=employee).order_by('-date')[:7]
        month_att         = Attendance.objects.filter(employee=employee,
                                                       date__month=today.month, date__year=today.year)
        upcoming_holidays = Holiday.objects.filter(date__gte=today).order_by('date')[:3]

        context = {
            'is_admin':           False,
            'employee':           employee,
            'today_attendance':   today_att,
            'my_leaves':          my_leaves,
            'my_attendance':      my_attendance,
            'month_present':      month_att.filter(status__in=['Present', 'Late']).count(),
            'month_absent':       month_att.filter(status='Absent').count(),
            'month_late':         month_att.filter(status='Late').count(),
            'upcoming_holidays':  upcoming_holidays,
        }

    return render(request, 'attendance/dashboard.html', context)


# ── Attendance ────────────────────────────────────────────────────────────────

@login_required
def check_in(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    today    = date.today()
    existing = Attendance.objects.filter(employee=employee, date=today).first()

    if existing and existing.check_in:
        messages.warning(request, 'You have already checked in today.')
        return redirect('dashboard')

    now      = timezone.localtime(timezone.now()).time()
    att, _   = Attendance.objects.get_or_create(employee=employee, date=today)
    att.check_in = now
    att.status   = 'Present' if now.hour < 10 else 'Late'
    att.save()
    messages.success(request, f'✅ Checked in at {now.strftime("%I:%M %p")}. Status: {att.status}')
    return redirect('dashboard')


@login_required
def check_out(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')

    today = date.today()
    att   = Attendance.objects.filter(employee=employee, date=today).first()

    if not att or not att.check_in:
        messages.warning(request, 'Please check in first.')
        return redirect('dashboard')

    if att.check_out:
        messages.warning(request, 'You have already checked out today.')
        return redirect('dashboard')

    now             = timezone.localtime(timezone.now()).time()
    att.check_out   = now
    att.total_hours = att.calculate_hours()
    if float(att.total_hours) < 4:
        att.status = 'Half Day'
    att.save()
    messages.success(request, f'👋 Checked out at {now.strftime("%I:%M %p")}. Hours: {att.total_hours}')
    return redirect('dashboard')


@login_required
def attendance_list(request):
    if not is_admin(request.user):
        try:
            employee  = request.user.employee
            queryset  = Attendance.objects.filter(employee=employee).order_by('-date')
            paginator = Paginator(queryset, 15)
            records   = paginator.get_page(request.GET.get('page'))
            return render(request, 'attendance/my_attendance.html', {'records': records, 'employee': employee})
        except Employee.DoesNotExist:
            return redirect('dashboard')

    form     = AttendanceFilterForm(request.GET)
    queryset = Attendance.objects.select_related('employee').all()

    if form.is_valid():
        if form.cleaned_data.get('date'):
            queryset = queryset.filter(date=form.cleaned_data['date'])
        if form.cleaned_data.get('month'):
            queryset = queryset.filter(date__month=form.cleaned_data['month'])
        if form.cleaned_data.get('year'):
            queryset = queryset.filter(date__year=form.cleaned_data['year'])
        if form.cleaned_data.get('employee'):
            q = form.cleaned_data['employee']
            queryset = queryset.filter(
                Q(employee__full_name__icontains=q) | Q(employee__employee_id__icontains=q)
            )
        if form.cleaned_data.get('status'):
            queryset = queryset.filter(status=form.cleaned_data['status'])

    queryset  = queryset.order_by('-date')
    paginator = Paginator(queryset, 20)
    records   = paginator.get_page(request.GET.get('page'))
    return render(request, 'attendance/attendance_list.html', {'records': records, 'form': form})


# ── Employees ─────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def employee_list(request):
    q         = request.GET.get('q', '')
    employees = Employee.objects.all()
    if q:
        employees = employees.filter(
            Q(full_name__icontains=q) | Q(employee_id__icontains=q) | Q(email__icontains=q)
        )
    paginator = Paginator(employees, 10)
    employees = paginator.get_page(request.GET.get('page'))
    return render(request, 'attendance/employee_list.html', {'employees': employees, 'q': q})


@login_required
@user_passes_test(is_admin)
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            username = form.cleaned_data['username']
            password = form.cleaned_data.get('password') or 'salon@123'

            if User.objects.filter(username=username).exists():
                form.add_error('username', 'This username is already taken.')
                return render(request, 'attendance/employee_form.html', {'form': form, 'title': 'Add Employee'})

            user = User.objects.create_user(
                username=username,
                email=form.cleaned_data['email'],
                password=password,
                is_staff=False,
                is_superuser=False
            )
            employee.user = user
            employee.save()
            messages.success(request, f'✅ Employee added! Username: "{username}" | Password: "{password}"')
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'attendance/employee_form.html', {'form': form, 'title': 'Add Employee'})


@login_required
@user_passes_test(is_admin)
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            emp      = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password and employee.user:
                employee.user.set_password(password)
                employee.user.save()
            emp.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'attendance/employee_form.html', {'form': form, 'title': 'Edit Employee', 'employee': employee})


@login_required
@user_passes_test(is_admin)
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        if employee.user:
            employee.user.delete()
        employee.delete()
        messages.success(request, 'Employee deleted.')
        return redirect('employee_list')
    return render(request, 'attendance/confirm_delete.html', {'object': employee, 'type': 'Employee'})


@login_required
@user_passes_test(is_admin)
def employee_detail(request, pk):
    employee   = get_object_or_404(Employee, pk=pk)
    today      = date.today()
    attendance = Attendance.objects.filter(employee=employee).order_by('-date')[:30]
    leaves     = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')
    month_att  = Attendance.objects.filter(employee=employee, date__month=today.month)
    stats = {
    	'present': month_att.filter(status__in=['Present', 'Late']).count(),
    	'late':    month_att.filter(status='Late').count(),
    	'absent':  month_att.filter(status='Absent').count(),
    	'leave':   month_att.filter(status='Leave').count(),
    }
    return render(request, 'attendance/employee_detail.html', {
        'employee': employee, 'attendance': attendance, 'leaves': leaves, 'stats': stats
    })


# ── Profile ───────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        messages.error(request, 'No employee profile found.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=employee)
    return render(request, 'attendance/profile.html', {'form': form, 'employee': employee})


# ── Leave Management ──────────────────────────────────────────────────────────

@login_required
def leave_apply(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave          = form.save(commit=False)
            leave.employee = employee
            leave.save()
            messages.success(request, 'Leave request submitted successfully.')
            return redirect('my_leaves')
    else:
        form = LeaveRequestForm()
    return render(request, 'attendance/leave_apply.html', {'form': form})


@login_required
def my_leaves(request):
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return redirect('dashboard')
    leaves = LeaveRequest.objects.filter(employee=employee).order_by('-created_at')
    return render(request, 'attendance/my_leaves.html', {'leaves': leaves, 'employee': employee})


@login_required
@user_passes_test(is_admin)
def leave_list(request):
    status   = request.GET.get('status', '')
    queryset = LeaveRequest.objects.select_related('employee').all()
    if status:
        queryset = queryset.filter(status=status)
    paginator = Paginator(queryset, 15)
    leaves    = paginator.get_page(request.GET.get('page'))
    return render(request, 'attendance/leave_list.html', {'leaves': leaves, 'status_filter': status})


@login_required
@user_passes_test(is_admin)
def leave_action(request, pk, action):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    if action == 'approve':
        leave.status = 'Approved'
        delta = leave.end_date - leave.start_date
        for i in range(delta.days + 1):
            d = leave.start_date + timedelta(days=i)
            Attendance.objects.update_or_create(
                employee=leave.employee, date=d,
                defaults={'status': 'Leave'}
            )
        messages.success(request, f'Leave approved for {leave.employee.full_name}.')
    elif action == 'reject':
        leave.status = 'Rejected'
        messages.warning(request, f'Leave rejected for {leave.employee.full_name}.')
    leave.save()
    return redirect('leave_list')


# ── Reports ───────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def reports(request):
    today       = date.today()
    month       = int(request.GET.get('month', today.month))
    year        = int(request.GET.get('year', today.year))
    emp_id      = request.GET.get('employee', '')
    report_type = request.GET.get('type', 'monthly')

    employees  = Employee.objects.filter(status='Active')
    attendance = Attendance.objects.filter(date__month=month, date__year=year)

    if emp_id:
        attendance = attendance.filter(employee__id=emp_id)

    monthly_data = []
    for emp in employees:
        emp_att = attendance.filter(employee=emp)
        monthly_data.append({
    		'employee': emp,
    		'present':  emp_att.filter(status__in=['Present', 'Late']).count(),
    		'late':     emp_att.filter(status='Late').count(),
    		'absent':   emp_att.filter(status='Absent').count(),
    		'leave':    emp_att.filter(status='Leave').count(),
    		'half_day': emp_att.filter(status='Half Day').count(),
	})

    daily_att = Attendance.objects.filter(date=today).select_related('employee')

    return render(request, 'attendance/reports.html', {
    	'monthly_data': monthly_data,
    	'daily_att':    daily_att,
    	'employees':    employees,
    	'month':        month,
    	'year':         year,
    	'emp_id':       emp_id,
    	'report_type':  report_type,
    	'today':        today,
    	'month_list':   list(range(1, 13)),
   })


# ── Holidays ──────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def holiday_list(request):
    from .models import SundayException
    
    holidays = Holiday.objects.all()
    
    today = date.today()
    year  = today.year
    sundays = []
    d = date(year, 1, 1)
    while d.year == year:
        if d.weekday() == 6:
            sundays.append(d)
        d = d + timedelta(days=1)
    
    # Store as strings for reliable template comparison
    working_sundays = list(
        SundayException.objects.values_list('date', flat=True)
    )
    working_sundays_str = [str(d) for d in working_sundays]
    
    return render(request, 'attendance/holiday_list.html', {
        'holidays':            holidays,
        'sundays':             sundays,
        'working_sundays_str': working_sundays_str,
    })


@login_required
@user_passes_test(is_admin)
def holiday_delete(request, pk):
    holiday = get_object_or_404(Holiday, pk=pk)
    if request.method == 'POST':
        holiday.delete()
        messages.success(request, 'Holiday deleted.')
        return redirect('holiday_list')
    return render(request, 'attendance/confirm_delete.html', {'object': holiday, 'type': 'Holiday'})

@login_required
@user_passes_test(is_admin)
def toggle_sunday(request, date_str):
    from .models import SundayException
    from datetime import date as date_type
    d = date_type.fromisoformat(date_str)
    obj = SundayException.objects.filter(date=d).first()
    if obj:
        obj.delete()
        messages.success(request, f'Sunday {d} is now a holiday again.')
    else:
        SundayException.objects.create(date=d)
        messages.success(request, f'Sunday {d} is now a working day.')
    return redirect('holiday_list')


@login_required
@user_passes_test(is_admin)
def holiday_add(request):
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Holiday added.')
            return redirect('holiday_list')
    else:
        form = HolidayForm()
    return render(request, 'attendance/holiday_form.html', {'form': form})@login_required
@user_passes_test(is_admin)
def toggle_sunday(request, date_str):
    from .models import SundayException
    from datetime import date as date_type
    d = date_type.fromisoformat(date_str)
    obj = SundayException.objects.filter(date=d).first()
    if obj:
        obj.delete()
        messages.success(request, f'Sunday {d} is now a holiday again.')
    else:
        SundayException.objects.create(date=d)
        messages.success(request, f'Sunday {d} is now a working day.')
    return redirect('holiday_list')


@login_required
@user_passes_test(is_admin)
def holiday_add(request):
    if request.method == 'POST':
        form = HolidayForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Holiday added.')
            return redirect('holiday_list')
    else:
        form = HolidayForm()
    return render(request, 'attendance/holiday_form.html', {'form': form})


@login_required
def employee_status_list(request):
    status = request.GET.get('status', 'all')
    today  = date.today()

    if status == 'present':
        attended  = Attendance.objects.filter(date=today, status='Present').values_list('employee_id', flat=True)
        employees = Employee.objects.filter(id__in=attended)
        title     = '✅ Present Today'
    elif status == 'late':
        attended  = Attendance.objects.filter(date=today, status='Late').values_list('employee_id', flat=True)
        employees = Employee.objects.filter(id__in=attended)
        title     = '⏰ Late Arrivals Today'
    elif status == 'absent':
        attended  = Attendance.objects.filter(date=today).exclude(status='Absent').values_list('employee_id', flat=True)
        employees = Employee.objects.filter(status='Active').exclude(id__in=attended)
        title     = '❌ Absent Today'
    else:
        employees = Employee.objects.filter(status='Active')
        title     = '👥 All Employees'

    return render(request, 'attendance/employee_status_list.html', {
        'employees': employees,
        'title':     title,
        'status':    status,
        'today':     today,
    })


@login_required
def my_calendar(request):
    from .models import SundayException
    try:
        employee = request.user.employee
    except Employee.DoesNotExist:
        return redirect('dashboard')

    today = date.today()
    month = int(request.GET.get('month', today.month))
    year  = int(request.GET.get('year', today.year))

    import calendar
    cal        = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    # Get attendance as simple dict with string keys
    attendance_records = Attendance.objects.filter(
        employee=employee,
        date__month=month,
        date__year=year
    )
    att_dict = {}
    for att in attendance_records:
        att_dict[att.date.strftime('%Y-%m-%d')] = {
            'status':    att.status,
            'check_in':  att.check_in.strftime('%I:%M %p') if att.check_in else '',
            'check_out': att.check_out.strftime('%I:%M %p') if att.check_out else '',
            'hours':     str(att.total_hours) if att.total_hours else '',
        }

    # Holidays as string list
    holidays = list(
        Holiday.objects.filter(date__month=month, date__year=year)
        .values_list('date', flat=True)
    )
    holiday_list = [h.strftime('%Y-%m-%d') for h in holidays]

    # Working sundays as string list
    working_sundays = list(
        SundayException.objects.filter(date__month=month, date__year=year)
        .values_list('date', flat=True)
    )
    working_sundays_list = [ws.strftime('%Y-%m-%d') for ws in working_sundays]

    # Prev/next month
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    # Monthly stats
    present = sum(1 for v in att_dict.values() if v['status'] in ['Present', 'Late'])
    absent  = sum(1 for v in att_dict.values() if v['status'] == 'Absent')
    late    = sum(1 for v in att_dict.values() if v['status'] == 'Late')
    leave   = sum(1 for v in att_dict.values() if v['status'] == 'Leave')

    import json
    return render(request, 'attendance/my_calendar.html', {
        'employee':           employee,
        'calendar':           cal,
        'month':              month,
        'year':               year,
        'month_name':         month_name,
        'att_dict_json':      json.dumps(att_dict),
        'holiday_list_json':  json.dumps(holiday_list),
        'working_sundays_json': json.dumps(working_sundays_list),
        'today':              today,
        'today_str':          today.strftime('%Y-%m-%d'),
        'prev_month':         prev_month,
        'prev_year':          prev_year,
        'next_month':         next_month,
        'next_year':          next_year,
        'stats': {
            'present': present,
            'absent':  absent,
            'late':    late,
            'leave':   leave,
        }
    })