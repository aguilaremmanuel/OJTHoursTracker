from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

def google_signin(request):

    if request.user.is_authenticated:
        return redirect('tracker')
    
    return render(request, 'google-signin.html')

@login_required(login_url='/signin-with-google/')
def tracker(request):
    if not request.user.is_authenticated:
        return redirect('google_signin')
    
    user = request.user
    context = {
        'name': user.get_full_name() or user.username,
        'email': user.email,
        'profile_picture': user.profile_picture or 'https://www.gravatar.com/avatar/default',
    }
    return render(request, 'tracker.html', context)

@never_cache
@require_POST
def logout(request):
    """Logout view that clears session completely"""
    request.session.flush()  # Clears all session data
    auth_logout(request)  # Logs out the user
    return redirect('google_signin')


def test(request):
    return render(request, 'test.html')