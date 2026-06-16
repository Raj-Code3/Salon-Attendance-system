from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import Employee, Attendance, LeaveRequest, Holiday


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Password'
        })


class EmployeeForm(forms.ModelForm):
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login username for employee'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Set Password'}),
        required=False,
        help_text='Leave blank to use default: salon@123'
    )

    class Meta:
        model = Employee
        fields = ['employee_id', 'full_name', 'email', 'phone', 'gender',
                  'salary', 'address', 'status', 'profile_photo']
        widgets = {
            'employee_id':   forms.TextInput(attrs={'class': 'form-control'}),
            'full_name':     forms.TextInput(attrs={'class': 'form-control'}),
            'email':         forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':         forms.TextInput(attrs={'class': 'form-control'}),
            'gender':        forms.Select(attrs={'class': 'form-select'}),
            'salary':        forms.NumberInput(attrs={'class': 'form-control'}),
            'address':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status':        forms.Select(attrs={'class': 'form-select'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['full_name', 'phone', 'address', 'profile_photo']
        widgets = {
            'full_name':     forms.TextInput(attrs={'class': 'form-control'}),
            'phone':         forms.TextInput(attrs={'class': 'form-control'}),
            'address':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason':     forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end   = cleaned.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError('End date cannot be before start date.')
        return cleaned


class HolidayForm(forms.ModelForm):
    class Meta:
        model = Holiday
        fields = ['holiday_name', 'date', 'description']
        widgets = {
            'holiday_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date':         forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description':  forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AttendanceFilterForm(forms.Form):
    date     = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    month    = forms.IntegerField(required=False, min_value=1, max_value=12,
                                  widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Month (1-12)'}))
    year     = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    employee = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee name/ID'}))
    status   = forms.ChoiceField(required=False, choices=[('', 'All Status')] + Attendance.STATUS_CHOICES,
                                  widget=forms.Select(attrs={'class': 'form-select'}))