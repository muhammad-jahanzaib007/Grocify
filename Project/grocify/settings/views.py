from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

def is_manager(user):
    return user.is_superuser or user.groups.filter(name='Managers').exists()

@login_required
@user_passes_test(is_manager)
def settings_dashboard(request):
    return render(request, 'settings/dashboard.html')