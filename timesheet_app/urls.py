from django.urls import path, include
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.auth import views as auth_views
from django.contrib import admin
from timesheet_app import views  # Replace 'your_app_name' with your actual app name

# Add this line to prevent circular import
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='login/'), name='root'),  # Redirect root URL to the login page
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),     path('logout/', LogoutView.as_view(), name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('projects/', views.project_list, name='project-list'),
    path('projects/create/', views.project_create, name='project-create'),
    path('projects/<int:pk>/', views.project_detail, name='project-detail'),
    path('projects/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project-update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project-delete'),
    path('add_activity_entry/', views.add_activity_entry, name='add_activity_entry'),
    path('activities/', views.activity_list, name='activity-list'),
    path('customers/', views.customer_list, name='customer-list'),
    path('admin/', admin.site.urls),
    path('timesheets/', views.timesheets, name='timesheets'),
    path('add-timesheet-entry/', views.add_timesheet_entry, name='add-timesheet-entry'),
    path('add_timesheet_entry/', views.add_timesheet_entry, name='add_timesheet_entry'),
    path('projects/', views.project_list, name='project_list'),
    path('approvals/', views.approvals, name='approvals'),
    path('update_status/', views.update_status, name='update_status'),
]

# Add this if you're using Django's built-in development server to serve media files in DEBUG mode
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
