from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from simple_history.models import HistoricalRecords

class BaseModel(models.Model):
    id = models.AutoField(primary_key=True)

    class Meta:
        abstract = True

# Role model for user roles
class Role(BaseModel):
    name = models.CharField(max_length=50)
    history = HistoricalRecords()
    def __str__(self):
        return self.name

# Custom user manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

# Custom user model
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    department = models.CharField(max_length=100, default='unknown', blank=True, null=True)
    employee_code = models.CharField(max_length=10, unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    secondary_approver = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    STATUS_CHOICES = [
        ('A', 'Active'),
        ('D', 'Inactive'),
    ]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.name} ({self.employee_code})"

# UserRoleAssignment model to assign roles to users
class UserRoleAssignment(BaseModel):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    history = HistoricalRecords()
    def __str__(self):
        return f"{self.user} - {self.role}"

# Customer model
class Customer(BaseModel):
    STATUS_CHOICES = [
        ('A', 'Active'),
        ('D', 'Inactive'),
    ]

    name = models.CharField(max_length=100)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='A')
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='added_customers', blank=True, null=True)
    history = HistoricalRecords()
    def __str__(self):
        return self.name

# SolutionModule model
class SolutionModule(BaseModel):
    STATUS_CHOICES = [
        ('A', 'Active'),
        ('D', 'Inactive'),
    ]

    name = models.CharField(max_length=100, verbose_name='Solution Module Name')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    added_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='added_solution_modules', blank=True, null=True)
    history = HistoricalRecords()
    def __str__(self):
        return self.name

# Project model
CustomUser = get_user_model()

class Project(BaseModel):
    STATUS_CHOICES = [
        ('A', 'Active'),
        ('D', 'Inactive'),
    ]

    PROJECT_TYPE_CHOICES = [
        ('Change Request', 'Change Request'),
        ('New', 'New'),
        ('Rollout', 'Rollout'),
        ('Upgrade', 'Upgrade'),
        ('POC', 'POC'),
    ]

    PRODUCT_TYPE_CHOICES = [
        ('Legacy', 'Legacy'),
        ('New Generation', 'New Generation'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, verbose_name='Project Name')
    plant_code = models.CharField(max_length=10)
    plant_name = models.CharField(max_length=100)
    solution_module = models.ForeignKey(SolutionModule, on_delete=models.CASCADE, limit_choices_to={'status': 'A'})
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES)
    product_type = models.CharField(max_length=15, choices=PRODUCT_TYPE_CHOICES)
    
    program_manager = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='program_manager_projects', blank=True, null=True)
    project_manager = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='project_manager_projects', blank=True, null=True)
    solution_architect = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='solution_architect_projects', blank=True, null=True)
    solution_architect_1 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='solution_architect_1_projects', blank=True, null=True)
    solution_architect_2 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='solution_architect_2_projects', blank=True, null=True)
    functional_consultant = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='functional_consultant_projects', blank=True, null=True)
    functional_consultant_1 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='functional_consultant_1_projects', blank=True, null=True)
    functional_consultant_2 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='functional_consultant_2_projects', blank=True, null=True)
    functional_consultant_3 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='functional_consultant_3_projects', blank=True, null=True)
    technical_consultant = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='technical_consultant_projects', blank=True, null=True)
    technical_consultant_1 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='technical_consultant_1_projects', blank=True, null=True)
    technical_consultant_2 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='technical_consultant_2_projects', blank=True, null=True)
    technical_consultant_3 = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='technical_consultant_3_projects', blank=True, null=True)

    start_date = models.DateField()
    completion_date = models.DateField()
    Last_Modified = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='added_projects',
        blank=True,
        null=True,
    )
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.added_by:
            # Set the 'added_by' field to the currently logged-in user
            self.added_by = kwargs.pop('user', None)

        super(Project, self).save(*args, **kwargs)  
        
    COMMERCIAL_TYPE_CHOICES =[
        ('Non-billable','Non-billable'),
        ('Billable','Billable')
    ]
    
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    project_key = models.CharField(max_length=20, unique=True)
    secondary_approver = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='secondary_approver_projects',
        blank=True,
        null=True
    )

    def __str__(self):
        return self.name
# activity model
class Activity(BaseModel):
    STATUS_CHOICES = [
        ('A', 'Active'),
        ('D', 'Inactive'),
    ]

    name = models.CharField(max_length=100)
    solution_module = models.ForeignKey(SolutionModule, on_delete=models.CASCADE, limit_choices_to={'status': 'A'})
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    system_time = models.DateTimeField(auto_now=True)
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, related_name='added_activitiess', blank=True, null=True)
    history = HistoricalRecords()
    def __str__(self):
        return self.name
    activity_TYPE_CHOICES = [
        ('external', 'External'),
        ('internal', 'Internal'),
    ]

    activity_type = models.CharField(
        max_length=10,
        choices=activity_TYPE_CHOICES,
        default='external'  # Set the default type here
    )
    description = models.TextField(blank=True, null=True)

class TimesheetManager(models.Manager):
    def create_entry(self, user, date, project, activity, start_time, end_time, remarks):
        return self.create(user=user, date=date, project=project, activity=activity, start_time=start_time, end_time=end_time, remarks=remarks)
    history = HistoricalRecords()

class TimesheetHistory(BaseModel):
    timesheet = models.ForeignKey('Timesheet', on_delete=models.CASCADE)
    project_key = models.CharField(max_length=255)
    project_manager = models.CharField(max_length=255)
    program_manager = models.CharField(max_length=255)
    secondary_approver = models.CharField(max_length=255)
    employee_code = models.CharField(max_length=255)
    email_id = models.EmailField()
    department = models.CharField(max_length=255)
    history_date = models.DateTimeField()
    activity_type = models.CharField(max_length=10, blank=True, null=True)  # Added activity_type field
    activity_description = models.TextField(blank=True, null=True)  # Added activity_description field
    user_role = models.CharField(max_length=50, blank=True, null=True)  # Added user_role field

    class Meta:
        verbose_name_plural = 'Timesheet Histories'

    def save(self, *args, **kwargs):
        if not self.activity_type and self.timesheet.activity:
            self.activity_type = self.timesheet.activity.activity_type
        if not self.activity_description and self.timesheet.activity:
            self.activity_description = self.timesheet.activity.description
        if not self.user_role and self.timesheet.user:
            self.user_role = self.timesheet.user.role.name if self.timesheet.user.role else None

        super(TimesheetHistory, self).save(*args, **kwargs)

    def __str__(self):
        return f"TimesheetHistory for {self.timesheet.user} on {self.timesheet.date}"

class Timesheet(BaseModel):
    STATUS_CHOICES = (
        ('Pending Approval', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    date = models.DateField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    remarks = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending Approval')

    # Historical records for Timesheet
    history = HistoricalRecords()

    def clean(self):
        # Check if there are any timesheets with conflicting start and end times
        conflicting_timesheets = Timesheet.objects.filter(
            user=self.user,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)  # Exclude the current timesheet if updating

        if conflicting_timesheets.exists():
            raise ValidationError("There is a conflicting timesheet with the same time range.")

    def calculate_total_time(self):
        if self.start_time and self.end_time:
            start_time = datetime.combine(datetime.today(), self.start_time)
            end_time = datetime.combine(datetime.today(), self.end_time)
            total_time = end_time - start_time
            return total_time
        else:
            return None

    def save(self, *args, **kwargs):
        if not self.user_id:
            # Set the user to the logged-in user
            self.user = kwargs.pop('user', None)

        super(Timesheet, self).save(*args, **kwargs)

        # Get the department from the user or set a default value
        department = self.user.department if self.user and self.user.department else 'Unknown'

        # Combine name and employee code for project manager
        project_manager = f"{self.project.project_manager.name} ({self.project.project_manager.employee_code})" if self.project.project_manager else None

        # Combine name and employee code for program manager
        program_manager = f"{self.project.program_manager.name} ({self.project.program_manager.employee_code})" if self.project.program_manager else None

        # Combine name and employee code for secondary approver
        secondary_approver = f"{self.project.secondary_approver.name} ({self.project.secondary_approver.employee_code})" if self.project.secondary_approver else None

        # Check if project_manager_info is None and provide a default value
        project_manager = project_manager or 'No Project Manager'
        program_manager = program_manager or 'No Program Manager'
        secondary_approver = secondary_approver or 'No Secondary Approver'
        # Create a history record after saving the Timesheet
        TimesheetHistory.objects.create(
            timesheet=self,
            project_key=self.project.project_key,
            project_manager=project_manager,
            program_manager=program_manager,
            secondary_approver=secondary_approver,
            employee_code=self.user.employee_code,
            email_id=self.user.email,
            department=department,
            history_date=timezone.now(),  # Use the current timestamp
        )

    def __str__(self):
        return f"TimesheetEntry for {self.user} on {self.date}"
# WeeklyTimesheet model
class WeeklyTimesheet(BaseModel):
    start_date = models.DateField()
    end_date = models.DateField()
    submitted = models.BooleanField(default=False)
    history = HistoricalRecords()
    def __str__(self):
        return f"Weekly Timesheet for {self.start_date} - {self.end_date}"
