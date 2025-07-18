from django.urls import path
from . import views



path('', views.purchase_orders_dashboard, name='index'),
