from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('analytics-demo/', views.analytics_demo, name='analytics_demo'),
    path('test-theme/', views.analytics_demo, name='test_theme'),
]
