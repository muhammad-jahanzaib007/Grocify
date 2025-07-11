from django.urls import path
from . import views

app_name = 'credit'

urlpatterns = [
    path('', views.credit_dashboard, name='index'),
    path('customers/<int:customer_id>/', views.customer_credit_detail, name='customer_detail'),
    path('payments/add/', views.add_credit_payment, name='add_payment'),
    path('insights/', views.credit_insights, name='insights'),

]