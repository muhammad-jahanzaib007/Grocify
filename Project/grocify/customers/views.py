from django.shortcuts import render
from .models import Customer

# Create your views here.
customers = Customer.objects.all().order_by('name')
def customers_dashboard(request):
    return render(request, 'customers/dashboard.html')