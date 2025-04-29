from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import TimeEntrySerializer
from .models import *

def google_signin(request):

    if request.user.is_authenticated:
        return redirect('tracker')
    
    return render(request, 'google-signin.html')

@login_required(login_url='/signin-with-google/')
def tracker(request):
    if not request.user.is_authenticated:
        return redirect('google_signin')
    
    user = request.user
    required_hours = int(user.required_hours) if user.required_hours == int(user.required_hours) else user.required_hours
    rendered_hours = int(user.rendered_hours) if user.rendered_hours == int(user.rendered_hours) else user.rendered_hours

    context = {
        'id': user.id,
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'profile_picture': user.profile_picture or 'https://www.gravatar.com/avatar/default',
        'required_hours': required_hours,
        'rendered_hours': rendered_hours
    }
    return render(request, 'tracker.html', context)

@never_cache
@require_POST
def logout(request):
    """Logout view that clears session completely"""
    request.session.flush()  # Clears all session data
    auth_logout(request)  # Logs out the user
    return redirect('google_signin')

class TimeEntryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = TimeEntrySerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({
                'message': 'Time entry recorded successfully!',
                'rendered_hours': request.user.rendered_hours,
                'required_hours': request.user.required_hours
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UpdateRequiredHoursView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        required_hours = request.data.get('required_hours')
        if required_hours is not None:
            try:
                required_hours = float(required_hours)
                request.user.required_hours = required_hours
                request.user.save()
                return Response({'message': 'Required hours updated successfully.', 'rendered_hours': request.user.rendered_hours}, status=status.HTTP_200_OK)
            except ValueError:
                return Response({'error': 'Invalid required_hours value.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'required_hours is required.'}, status=status.HTTP_400_BAD_REQUEST)

class TimeEntryListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        time_entries = TimeEntry.objects.filter(user_id=id)
        serializer = TimeEntrySerializer(time_entries, many=True)
        return Response(serializer.data)

def test(request):
    return render(request, 'test.html')