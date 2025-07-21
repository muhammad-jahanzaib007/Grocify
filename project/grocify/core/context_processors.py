from inventory.models import Location

def location_context(request):
    """Add current location to template context"""
    current_location = None
    # Check both session keys for compatibility
    current_location_id = request.session.get('current_location_id') or request.session.get('selected_location')
    
    if current_location_id:
        try:
            current_location = Location.objects.get(id=current_location_id, is_active=True)
        except Location.DoesNotExist:
            # Clear invalid location from session
            if 'current_location_id' in request.session:
                del request.session['current_location_id']
            if 'current_location_name' in request.session:
                del request.session['current_location_name']
            if 'selected_location' in request.session:
                del request.session['selected_location']
    
    return {
        'current_location': current_location,
        'current_location_id': current_location_id,
    }