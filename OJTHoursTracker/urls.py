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
]
