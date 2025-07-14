from django.urls import path, include
from . import views

app_name = 'loyalty'

urlpatterns = [
    path('', views.loyalty_dashboard, name='index'),
    path('history/', views.transaction_history, name='history'),
    path('redeem/', views.redeem_reward, name='redeem'),
]