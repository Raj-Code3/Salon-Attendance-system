from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Employee(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    STATUS_CHOICES = [('Active', 'Active'), ('Inactive', 'Inactive')]

    user          = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee', null=True, blank=True)
    employee_id   = models.CharField(max_length=20, unique=True)
    full_name     = models.CharField(max_length=200)
    email         = models.EmailField(unique=True)
    phone         = models.CharField(max_length=15)
    gender        = models.CharField(max_length=10, choices=GENDER_CHOICES)
    salary        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    address       = models.TextField(blank=True)
    status        = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    date_joined   = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"

    class Meta:
        ordering = ['employee_id']


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('Half Day', 'Half Day'),
        ('Leave', 'Leave'),
    ]

    employee    = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date        = models.DateField(default=timezone.now)
    check_in    = models.TimeField(null=True, blank=True)
    check_out   = models.TimeField(null=True, blank=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Absent')
    notes       = models.TextField(blank=True)

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.full_name} – {self.date} – {self.status}"

    def calculate_hours(self):
        if self.check_in and self.check_out:
            from datetime import datetime, date
            ci = datetime.combine(date.today(), self.check_in)
            co = datetime.combine(date.today(), self.check_out)
            diff = (co - ci).seconds / 3600
            return round(diff, 2)
        return 0

    def calculate_status(self):
        if not self.check_in:
            return 'Absent'
        from datetime import time
        if self.check_in <= time(10, 0):
            if self.total_hours and float(self.total_hours) < 4:
                return 'Half Day'
            return 'Present'
        else:
            if self.total_hours and float(self.total_hours) < 4:
                return 'Half Day'
            return 'Late'


class LeaveRequest(models.Model):
    LEAVE_TYPES = [
        ('Sick Leave', 'Sick Leave'),
        ('Casual Leave', 'Casual Leave'),
        ('Annual Leave', 'Annual Leave'),
        ('Emergency Leave', 'Emergency Leave'),
        ('Unpaid Leave', 'Unpaid Leave'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    employee   = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date   = models.DateField()
    reason     = models.TextField()
    status     = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.full_name} – {self.leave_type} ({self.status})"

    def total_days(self):
        return (self.end_date - self.start_date).days + 1

    class Meta:
        ordering = ['-created_at']


class Holiday(models.Model):
    holiday_name = models.CharField(max_length=200)
    date         = models.DateField(unique=True)
    description  = models.TextField(blank=True)

    def __str__(self):
        return f"{self.holiday_name} – {self.date}"

    class Meta:
        ordering = ['date']

class SundayException(models.Model):
    """Sundays removed from holiday list — attendance allowed on these days"""
    date        = models.DateField(unique=True)
    reason      = models.CharField(max_length=200, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Working Sunday – {self.date}"

    class Meta:
        ordering = ['date']
