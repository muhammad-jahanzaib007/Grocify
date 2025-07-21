from users.models import UserProfile
from inventory.models import Location

def location_context(request):
    # Always provide default values for template consistency
    context = {
        'available_locations': Location.objects.none(),
        'selected_location_id': 'all',
    }
    
    if not request.user.is_authenticated:
        return context

    try:
        profile = getattr(request.user, 'userprofile', None)
        
        # Get available locations
        if request.user.is_superuser:
            avail = Location.objects.all()
        else:
            avail = profile.locations.all() if profile else Location.objects.none()

        # Get selected location
        sel = request.session.get('selected_location')
        if not sel and profile and profile.default_location:
            sel = str(profile.default_location.id)
        if not sel:
            sel = 'all'
        
        context.update({
            'available_locations': avail,
            'selected_location_id': sel,
        })
        
    except Exception as e:
        # Silent error handling - use defaults
        pass
    
    return context
