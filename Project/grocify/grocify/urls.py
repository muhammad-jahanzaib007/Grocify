"""
URL configuration for grocify project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls', namespace='dashboard')),
    path('pos/', include('sales.urls', namespace='sales')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('expenses/', include('expenses.urls', namespace='expenses')),
    path('customers/', include('customers.urls', namespace='customers')),
    path('loyalty/', include('loyalty.urls', namespace='loyalty')),
    path('credit/', include('credit.urls', namespace='credit')),
    path('reports/', include('analytics.urls', namespace='reports')),
    path('api/', include('api.urls', namespace='api')),
    path('settings/', include('settings.urls', namespace='settings')),
    
]