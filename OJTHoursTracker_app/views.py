from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.cache import never_cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import TimeEntrySerializer
from .models import *
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, time

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

def validate_time_sessions(data):
    def parse_time(t):
        if not t:
            return None
        if isinstance(t, time):
            return t  # Already a time object

        if isinstance(t, str):
            if t.count(":") == 2:
                try:
                    return datetime.strptime(t, '%H:%M:%S').time()
                except ValueError:
                    pass
            elif t.count(":") == 1:
                try:
                    return datetime.strptime(t, '%H:%M').time()
                except ValueError:
                    pass

        raise ValueError(f"Time format not recognized or invalid: {t}")


    print(data.get('morning_in'))
    morning_in = parse_time(data.get('morning_in'))
    print(morning_in)
    morning_out = parse_time(data.get('morning_out'))
    afternoon_in = parse_time(data.get('afternoon_in'))
    afternoon_out = parse_time(data.get('afternoon_out'))
    evening_in = parse_time(data.get('evening_in'))
    evening_out = parse_time(data.get('evening_out'))

    if morning_in and not time(1, 0) <= morning_in <= time(12, 0):
        return False, 'Morning In must be between 1:00 AM and 12:00 PM.'
    if morning_out and not time(1, 0) <= morning_out <= time(12, 0):
        return False, 'Morning Out must be between 1:00 AM and 12:00 PM.'
    if morning_in and morning_out and morning_in > morning_out:
        return False, 'Morning time out is earlier than time in'

    if afternoon_in and not time(12, 0) <= afternoon_in <= time(19, 0):
        return False, 'Afternoon In must be between 12:00 PM and 7:00 PM.'
    if afternoon_out and not time(12, 0) <= afternoon_out <= time(19, 0):
        return False, 'Afternoon Out must be between 12:00 PM and 7:00 PM.'
    if afternoon_in and afternoon_out and afternoon_in > afternoon_out:
        return False, 'Afternoon time out is earlier than time in'

    if evening_in and not (time(17, 0) <= evening_in <= time(23, 59) or time(0, 0) <= evening_in <= time(8, 0)):
        return False, 'Evening In must be between 5:00 PM and 12:00 AM.'
    if evening_out and not (time(17, 0) <= evening_out <= time(23, 59) or time(0, 0) <= evening_out <= time(8, 0)):
        return False, 'Evening Out must be between 5:00 PM and 12:00 AM.'
    if evening_in and evening_out and evening_in > evening_out:
        return False, 'Evening Out is earlier than In.'

    return True, ''


class TimeEntryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        data = request.data.copy()
        data['user'] = request.user.id

        if request.user.required_hours <= 0:
            return Response({'message': 'Required hours not set.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

        is_valid, message = validate_time_sessions(data)
        if not is_valid:
            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)

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

    def get(self, request, id, no=None):
        if no:
            try:
                time_entry = TimeEntry.objects.get(user_id=id, no=no)
                serializer = TimeEntrySerializer(time_entry)
                return Response(serializer.data)
            except TimeEntry.DoesNotExist:
                return Response({'detail': 'Time entry not found.'}, status=404)
        else:
            time_entries = TimeEntry.objects.filter(user_id=id)
            serializer = TimeEntrySerializer(time_entries, many=True)
            return Response(serializer.data)
        
    def put(self, request, id, no):
        try:
            time_entry = TimeEntry.objects.get(user_id=id, no=no)
        except TimeEntry.DoesNotExist:
            return Response({'detail': 'Time entry not found.'}, status=404)
        
        data = request.data.copy()

        is_valid, message = validate_time_sessions(data)
        if not is_valid:
            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)

        old_total_hours = time_entry.total_hours or 0
        serializer = TimeEntrySerializer(time_entry, data=request.data)

        if serializer.is_valid():
            serializer.save()
            new_total_hours = time_entry.total_hours

            time_entry.user.rendered_hours = (time_entry.user.rendered_hours or 0) - old_total_hours
            time_entry.user.save()

            response_data = serializer.data
            response_data.update({
                "rendered_hours": time_entry.user.rendered_hours,
                "required_hours": time_entry.user.required_hours
            })

            return Response(response_data)
        
        return Response(serializer.errors, status=400)

    
@csrf_protect
@require_http_methods(["DELETE"])
def delete_time_entry(request, no):
    try:
        time_entry = TimeEntry.objects.get(no=no)

        # Subtract the time entry's hours from the user's rendered_hours
        if time_entry.user and time_entry.total_hours:
            user = time_entry.user
            user.rendered_hours = (user.rendered_hours or 0) - time_entry.total_hours
            user.save()

        time_entry.delete()

        return JsonResponse({
            'message': 'Deleted successfully',
            'rendered_hours': user.rendered_hours,
            'required_hours': user.required_hours
        }, status=200)

    except TimeEntry.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

def test(request):
    return render(request, 'test.html')