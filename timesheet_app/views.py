from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import LoginView
from django.views.generic.edit import DeleteView, UpdateView
from django.urls import reverse_lazy
from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .models import WeeklyTimesheet, Customer, SolutionModule, Project, Activity, Timesheet, CustomUser
from .forms import ProjectForm, TimesheetForm, ActivityEntryForm
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
# from .models import CustomUser


@receiver(pre_save, sender=Customer)
@receiver(pre_save, sender=SolutionModule)
@receiver(pre_save, sender=Project)
@receiver(pre_save, sender=Activity)
def set_added_by(sender, instance, **kwargs):
    if not instance.added_by:
        instance.added_by = CustomUser.objects.get(username='admin')

@login_required
def dashboard(request):

    user = request.user
    # Fetch the number of submitted timesheets
    approved_timesheets = Timesheet.objects.filter(user=user, status='Approved').count()

    # Fetch the number of rejected timesheets
    rejected_timesheets = Timesheet.objects.filter(user=user, status='Rejected').count()

    # Fetch the number of timesheets with the status "Pending Approval"
    pending_approval_timesheets = Timesheet.objects.filter(user=user, status='Pending Approval').count()
    
    context = {
        'user': request.user,
        'approved_timesheets': approved_timesheets,
        'rejected_timesheets': rejected_timesheets,
        'pending_approval_timesheets': pending_approval_timesheets,
    }

    return render(request, 'dashboard.html', context)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            # Authenticate the user
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Redirect to your dashboard URL
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})

# Other views and routes can remain as they are.

def home(request):
    projects = Project.objects.all()
    return render(request, 'home.html', {'projects': projects})

def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'project_details.html', {'project': project})

def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            return redirect('project-detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'project_form.html', {'form': form})

def activity_list(request):
    activities = Activity.objects.all()
    return render(request, 'activity_list.html', {'activities': activities})

def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'customer_list.html', {'customers': customers})

class ProjectUpdateView(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'project_form.html'
    success_url = reverse_lazy('project-list')

class ProjectDeleteView(DeleteView):
    model = Project
    success_url = reverse_lazy('project-list')

    def delete(self, request, *args, **kwargs):
        project = self.get_object()
        project.delete()
        return super().delete(request, *args, **kwargs)

@login_required
def edit_timesheet_entry(request, entry_id):
    entry = get_object_or_404(Timesheet, pk=entry_id)
    if entry.employee != request.user:
        # Add logic to handle unauthorized access here
        pass
    if request.method == 'POST':
        form = TimesheetForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('timesheet-list')
    else:
        form = TimesheetForm(instance=entry)
    return render(request, 'edit_timesheet_entry.html', {'form': form, 'entry': entry})

def timesheet_list(request):
    # Fetch Timesheet objects, you can filter or order them as needed
    timesheets = Timesheet.objects.all()

    # Pass the Timesheet objects to the template
    return render(request, 'timesheets.html', {'timesheets': timesheets})
@login_required
def submit_timesheet(request, week_id):
    week = get_object_or_404(WeeklyTimesheet, pk=week_id)
    if request.user != week.timesheet_entries.first().employee:
        # Handle unauthorized access here
        pass
    week.submitted = True
    week.save()
    return redirect('timesheet-list')

@login_required

def timesheets(request):
    # Fetch all timesheets initially
    timesheets = Timesheet.objects.all()
    
    # Get filter parameters from the request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    project = request.GET.get('project')
    customer = request.GET.get('customer')
    plant = request.GET.get('plant')
    activity = request.GET.get('activity')
    status = request.GET.get('status')

    # Apply filters if parameters exist
    if start_date:
        timesheets = timesheets.filter(date__gte=start_date)
    if end_date:
        timesheets = timesheets.filter(date__lte=end_date)
    if project:
        timesheets = timesheets.filter(project__name=project)
    if customer:
        timesheets = timesheets.filter(project__customer=customer)
    if plant:
        timesheets = timesheets.filter(project__plant_name=plant)
    if activity:
        timesheets = timesheets.filter(activity__name=activity)
    if status:
        timesheets = timesheets.filter(status=status)

    # Modify the timesheets objects (assuming related fields are present)
    for timesheet in timesheets:
        if timesheet.project:
            timesheet.plant = timesheet.project.plant_name
            timesheet.customer = timesheet.project.customer
        if timesheet.activity:
            timesheet.solution_module = timesheet.activity.solution_module

    # Fetch data for dropdowns
    projects = Project.objects.all()
    customers = Customer.objects.all()
    plants = Project.objects.values_list('plant_name', flat=True).distinct()    
    activities = Activity.objects.all()

    user = request.user if request.user.is_authenticated else None
    timesheet_form = TimesheetForm(user=user)

    context = {
        'timesheets': timesheets,
        'timesheet_form': timesheet_form,
        'projects': projects,
        'customers': customers,
        'plants': plants,
        'activities': activities,
    }

    return render(request, 'timesheets.html', context)

def end_activity(request, activity_id):
    try:
        activity = Activity.objects.get(id=activity_id)
        if activity.status == 'A':  # Check if the activity is active
            activity.status = 'D'  # Mark the activity as inactive
            activity.save()
    except Activity.DoesNotExist:
        pass  # Handle the case where the activity doesn't exist or has already ended

    return redirect('timesheets') 

def timesheets_view(request):
    # Assuming you have the necessary logic to fetch timesheet data
    timesheet_data = ...  # Replace this with your actual data retrieval logic

    context = {
        'timesheet_data': timesheet_data,
    }

    return render(request, 'timesheets.html', context)

def add_activity_entry(request):
    if request.method == 'POST':
        form = ActivityEntryForm(request.POST)
        if form.is_valid():
            # Save the activity entry
            activity_entry = form.save()
            return redirect('timesheets')  # Redirect to the timesheets page after submission
    else:
        form = ActivityEntryForm()
    
    return render(request, 'add_activity_entry.html', {'form': form})

def submit_timesheet(request):
    if request.method == 'POST':
        form = TimesheetForm(request.POST)
        if form.is_valid():
            # Process and save the form data here
            # Redirect to a success page or do something else
            return redirect('timesheets')
    else:
        form = TimesheetForm()

    return render(request, 'timesheets.html', {'timesheet_form': form})
    
@login_required
def add_timesheet_entry(request):
    if request.method == 'POST':
        form = TimesheetForm(request.POST, user=request.user)
        if form.is_valid():
            timesheet_entry = form.save(commit=False)
            timesheet_entry.user = request.user
            timesheet_entry.save()
            
            # Redirect to timesheets.html after successful submission
            return redirect('timesheets')  # 'timesheets' should be the name of your timesheets view

    else:
        form = TimesheetForm(user=request.user)

    return render(request, 'timesheet_entry_form.html', {'form': form})

def project_list(request):
    # Fetch projects where the user is assigned as a program manager, project manager, solution architect,
    # or secondary approver
    user_projects = Project.objects.filter(
        Q(program_manager=request.user) |
        Q(project_manager=request.user) |
        Q(solution_architect=request.user) |
        Q(solution_architect_1=request.user) |
        Q(solution_architect_2=request.user) |
        Q(functional_consultant=request.user) |
        Q(functional_consultant_1=request.user) |
        Q(functional_consultant_2=request.user) |
        Q(functional_consultant_3=request.user) |
        Q(technical_consultant=request.user) |
        Q(technical_consultant_1=request.user) |
        Q(technical_consultant_2=request.user) |
        Q(technical_consultant_3=request.user) |
        Q(secondary_approver=request.user)
    ).distinct()

    # Create a dictionary to map user IDs to roles
    user_roles = {}
    for project in user_projects:
        if project.program_manager == request.user:
            user_roles[project.id] = 'Program Manager'
        elif project.project_manager == request.user:
            user_roles[project.id] = 'Project Manager'
        elif project.solution_architect == request.user:
            user_roles[project.id] = 'Solution Architect'
        elif project.solution_architect_1 == request.user:
            user_roles[project.id] = 'Solution Architect 1'
        elif project.solution_architect_2 == request.user:
            user_roles[project.id] = 'Solution Architect 2'
        elif project.functional_consultant == request.user:
            user_roles[project.id] = 'Functional Consultant'
        elif project.functional_consultant_1 == request.user:
            user_roles[project.id] = 'Functional Consultant'
        elif project.functional_consultant_2 == request.user:
            user_roles[project.id] = 'Functional Consultant'
        elif project.functional_consultant_3 == request.user:
            user_roles[project.id] = 'Funnctional Consultant'
        elif project.technical_consultant == request.user:
            user_roles[project.id] = 'Technical Consultant'
        elif project.technical_consultant_1 == request.user:
            user_roles[project.id] = 'Technical Consultant'
        elif project.technical_consultant_2 == request.user:
            user_roles[project.id] = 'Technical Consultant'
        elif project.technical_consultant_3 == request.user:
            user_roles[project.id] = 'Technical Consultant'
        elif project.secondary_approver == request.user:
            user_roles[project.id] = 'Secondary Approver'

    context = {
        'user': request.user,
        'projects': user_projects,
        'user_roles': user_roles,
    }

    return render(request, 'projects.html', context)

def approvals(request):
    user = request.user
    user_projects = Project.objects.filter(
        Q(program_manager=user) | Q(project_manager=user) | Q(secondary_approver=user)
    ).distinct()

    timesheets_by_project = {}
    for project in user_projects:
        timesheets = Timesheet.objects.filter(project=project)
        timesheets_by_project[project] = timesheets

    context = {
        'user_projects': user_projects,
        'timesheets_by_project': timesheets_by_project,
    }
    return render(request, 'approvals.html', context)

@csrf_exempt
def update_status(request):
    if request.method == 'POST':
        timesheet_id = request.POST.get('timesheet_id')
        new_status = request.POST.get('new_status')

        try:
            timesheet = Timesheet.objects.get(pk=timesheet_id)
            timesheet.status = new_status
            timesheet.save()
            return JsonResponse({'message': 'Status updated successfully'})
        except Timesheet.DoesNotExist:
            return JsonResponse({'message': 'Timesheet not found'}, status=404)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)
    else:
        return JsonResponse({'message': 'Invalid request method'}, status=405)