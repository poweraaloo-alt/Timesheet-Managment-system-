from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import UserRoleAssignment, Timesheet, Customer, Activity, Project, SolutionModule, CustomUser
# from django.contrib.auth.models import AbstractUser

User = get_user_model()  # Get the user model

class CustomerForm(forms.ModelForm):
    class Meta:   
        model = Customer
        fields = '__all__'

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = '__all__'

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        labels = {
            'name': 'Project Name',
        }

class SolutionModuleForm(forms.ModelForm):
    class Meta:
        model = SolutionModule
        fields = ['name', 'status']

class TimesheetForm(forms.ModelForm):
    class Meta:
        model = Timesheet
        fields = ['user', 'date', 'project', 'activity', 'start_time', 'end_time', 'remarks']  # Exclude 'status' field

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TimesheetForm, self).__init__(*args, **kwargs)

        # Set the 'user' field to the logged-in user's name and employee code
        if user is not None:
            user_label = f"{user.name} ({user.employee_code})"
            self.fields['user'].label_from_instance = lambda obj: user_label
            self.fields['user'].initial = user.id

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time.")

class ActivityEntryForm(forms.Form):
    activity_name = forms.CharField(max_length=100)
    description = forms.CharField(max_length=400, required=False)
    solution_module = forms.ModelChoiceField(queryset=SolutionModule.objects.all(), empty_label="Select Solution Module")

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser  # Use the User model obtained from get_user_model()
        fields = ('email', 'username','name', 'employee_code', 'password1', 'password2', 'department')

class UserRoleAssignmentForm(forms.ModelForm):
    class Meta:
        model = UserRoleAssignment
        # Remove 'employee_code' from the fields
        fields = ['user', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the choices for the user field
        self.fields['user'].widget = forms.Select(choices=self.get_user_choices())

    def get_user_choices(self):
        # Fetch usernames and ids to populate the dropdown
        users = CustomUser.objects.all()
        user_choices = [(user.id, user.username) for user in users]
        return user_choices