from django.contrib import admin
from django.urls import path, include
from OJTHoursTracker_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.tracker, name='tracker'),
    path('signin-with-google/', views.google_signin, name='google_signin'),
    path('auth/', include('social_django.urls', namespace='social')),
    path('logout/', views.logout, name='logout'),
    path('test/', views.test),
    path('api/time-entry/', views.TimeEntryView.as_view(), name='time-entry'),
    path('api/update-required-hours/', views.UpdateRequiredHoursView.as_view(), name='update-required-hours'),
    path('api/time-entries/<int:id>/', views.TimeEntryListView.as_view(), name='time-entry-list'),
]
