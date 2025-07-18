from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def user_list(request):
    return render(request, 'users/user_list.html')

def login_view(request):
    return render(request, 'users/login.html')
