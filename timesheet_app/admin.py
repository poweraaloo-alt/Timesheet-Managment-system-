from django.contrib import admin
from django import forms
from .models import TimesheetHistory, Timesheet, CustomUser, Customer, Project, Activity, SolutionModule, Role, UserRoleAssignment
from django.contrib.auth.admin import UserAdmin as UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .forms import UserRoleAssignmentForm
from datetime import datetime, timedelta
from django.apps import apps

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'get_projects')

    def get_projects(self, obj):
        return ", ".join([str(project) for project in obj.project_set.all()])
    get_projects.short_description = 'Projects'

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('department',)

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm):
        model = CustomUser
        fields = '__all__'

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'name', 'department', 'employee_code', 'role', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('name', 'employee_code', 'mobile', 'role', 'secondary_approver', 'department')}),  # Include 'department' here
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'name', 'employee_code', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser', 'department'),  # Include 'department' here
        }),
    )
    search_fields = ('username', 'email', 'name', 'employee_code')
    ordering = ('username', 'email')
    add_form = CustomUserCreationForm  # Use the custom form for user creation

admin.site.register(CustomUser, CustomUserAdmin)

class ProjectAdminForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Roles to retrieve users for
        role_names = [
            'Program Manager', 'Project Manager', 'Solution Architect',
            'Functional Consultant', 'Functional Consultant 1', 'Functional Consultant 2', 'Functional Consultant 3',
            'Solution Architect 1', 'Solution Architect 2',
            'Technical Consultant', 'Technical Consultant 1', 'Technical Consultant 2', 'Technical Consultant 3',
        ]

        # Create a dictionary to map numbered roles to their base roles
        role_mapping = {
            'Functional Consultant 1': 'Functional Consultant',
            'Functional Consultant 2': 'Functional Consultant',
            'Functional Consultant 3': 'Functional Consultant',
            'Solution Architect 1': 'Solution Architect',
            'Solution Architect 2': 'Solution Architect',
            'Technical Consultant 1': 'Technical Consultant',
            'Technical Consultant 2': 'Technical Consultant',
            'Technical Consultant 3': 'Technical Consultant',
        }

        for field_name in role_names:
            field = self.fields.get(field_name.lower().replace(' ', '_'))
            if field:
                # Check if the field name is a numbered role
                if field_name in role_mapping:
                    base_role_name = role_mapping[field_name]
                    base_field = self.fields.get(base_role_name.lower().replace(' ', '_'))
                    if base_field:
                        # Set the queryset for the numbered role field to be the same as the base role field
                        field.queryset = base_field.queryset
                        # Override the label to display username and employee_code
                        field.label_from_instance = lambda obj: f"{obj.name} ({obj.employee_code})"
                else:
                    # Retrieve the users associated with the role and set the queryset
                    users = CustomUser.objects.filter(userroleassignment__role__name=field_name)
                    field.queryset = users
                    # Override the label to display username and employee_code
                    field.label_from_instance = lambda obj: f"{obj.name} ({obj.employee_code})"

        # Add the secondary_approver field and set the queryset to all users
        secondary_approver_field = self.fields.get('secondary_approver')
        if secondary_approver_field:
            all_users = CustomUser.objects.all()
            secondary_approver_field.queryset = all_users
            secondary_approver_field.label_from_instance = lambda obj: f"{obj.username} ({obj.employee_code})"
                
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 'name', 'project_manager', 'program_manager',
        'functional_consultant', 'functional_consultant_1', 'functional_consultant_2', 'functional_consultant_3', 
        'solution_architect_1', 'solution_architect_2', 'technical_consultant_1', 
        'technical_consultant_2', 'technical_consultant_3', 'start_date', 'completion_date', 'status', 'added_by', 'Last_Modified', 'id'
    )
    list_filter = ('customer', 'program_manager', 'project_manager', 'status')
    search_fields = ('name', 'customer__name', 'plant_code')
    form = ProjectAdminForm  # Use the custom form for this admin class

    def save_model(self, request, obj, form, change):
        # Set the 'added_by' field to the currently logged-in user
        obj.added_by = request.user
        obj.save()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # List of fields for which you want to customize the queryset
        role_fields = [
            'program_manager', 'project_manager', 'solution_architect_1', 'solution_architect_2',
            'functional_consultant', 'functional_consultant_1', 'functional_consultant_2', 'functional_consultant_3',
            'technical_consultant_1', 'technical_consultant_2', 'technical_consultant_3',
            'secondary_approver',  # Include secondary_approver in customization
        ]

        if db_field.name in role_fields:
            # Customize the queryset to include only active users with the respective role
            role_name = db_field.name.replace('_', ' ').title()
            role_users = CustomUser.objects.filter(role__name=role_name, status='A')
            kwargs["queryset"] = role_users

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'solution_module', 'status', 'system_time', 'added_by_name')
    list_filter = ('status', 'system_time')
    search_fields = ('name', 'solution_module')

    def added_by_name(self, obj):
        return obj.added_by.username if obj.added_by else None
    
    added_by_name.short_description = 'Added By'

@admin.register(SolutionModule)
class SolutionModuleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status', 'added_by_name')

    def added_by_name(self, obj):
        return obj.added_by.username if obj.added_by else None
    
    added_by_name.short_description = 'Added By'

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')

@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    form = UserRoleAssignmentForm
    list_display = ('user', 'role')
    
    # Override the widget for the user field to display usernames
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "user":
            kwargs["queryset"] = CustomUser.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
class TimesheetAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_user', 'date', 'project', 'activity', 'start_time', 'end_time', 'display_total_time', 'remarks')
    list_filter = ('date', 'project', 'activity')
    search_fields = ('user__username', 'date', 'project', 'solution_module', 'activity')
    list_per_page = 20

    def get_user(self, obj):
        user = obj.user
        if user:
            return f"{user.name} ({user.employee_code})"
        return "N/A"

    get_user.short_description = 'User'

    # Define a method to display the calculated 'total_time' as a string
    def display_total_time(self, obj):
        total_time = obj.calculate_total_time()
        return str(total_time) if total_time else "N/A"

    display_total_time.short_description = 'Total Time'

# Register the TimesheetEntry model with the admin site
admin.site.register(Timesheet, TimesheetAdmin)

class TimesheetHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'timesheet', 'project_key', 'project_manager', 'program_manager', 'secondary_approver', 'employee_code', 'email_id', 'department', 'activity_type', 'activity_description', 'user_role', 'history_date']
    list_filter = ['timesheet', 'history_date']
    search_fields = ['timesheet__user__username', 'timesheet__project__project_key']

    def activity_type(self, obj):
        return obj.activity_type if obj.activity_type else "N/A"
    activity_type.short_description = 'activity Type'

    def activity_description(self, obj):
        return obj.activity_description if obj.activity_description else "N/A"
    activity_description.short_description = 'Activity Description'

    def user_role(self, obj):
        if obj.timesheet.user and obj.timesheet.project:
            user = obj.timesheet.user
            project_key = obj.timesheet.project.project_key
            try:
                user_role_assignment = UserRoleAssignment.objects.get(user=user, project__project_key=project_key)
                return user_role_assignment.role.name
            except UserRoleAssignment.DoesNotExist:
                return "N/A"
        else:
            return "N/A"
    user_role.short_description = 'User Role'

# Register the updated TimesheetHistoryAdmin
admin.site.register(TimesheetHistory, TimesheetHistoryAdmin)

