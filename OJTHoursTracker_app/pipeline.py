from OJTHoursTracker_app.models import User
from social_core.exceptions import AuthFailed
from social_core.pipeline.social_auth import associate_by_email as social_associate_by_email

def associate_by_email(backend, details, user=None, *args, **kwargs):
    """
    Associate current auth with a user with the same email in the DB.
    Prevents duplicate user creation.
    """
    if user:  # If user is already logged in
        return {'user': user}

    email = details.get('email')
    if not email:
        return None

    # Try to find a user with matching email
    try:
        user = User.objects.get(email=email)
        return {
            'user': user,
            'is_new': False  # Important to prevent new user creation
        }
    except User.DoesNotExist:
        return None

def save_profile(backend, user, response, *args, **kwargs):
    """Your existing profile saving function"""
    if backend.name == 'google-oauth2':
        user.profile_picture = response.get('picture')
        user.save()

def validate_email(backend, details, *args, **kwargs):
    """Ensure we have a valid email address."""
    email = details.get('email', '')
    if not email or '@' not in email:
        raise AuthFailed(backend, 'Valid email is required')