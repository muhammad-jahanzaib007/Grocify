from users.models import UserProfile
from inventory.models import Location

def location_context(request):
    if not request.user.is_authenticated:
        return {}

    profile = getattr(request.user, 'userprofile', None)
    if request.user.is_superuser:
        avail = Location.objects.all()
    else:
        avail = profile.locations.all() if profile else Location.objects.none()

    sel = request.session.get('selected_location')
    if not sel and profile and profile.default_location:
        sel = str(profile.default_location.id)
    if not sel:
        sel = 'all'
    return {
         'available_locations': avail,
         'selected_location_id': sel,
    }
