from django.urls import path
from .views import pos_checkout, product_search_api, process_sale, receipt_view
from dashboard import views as dashboard_views

app_name = 'sales'

urlpatterns = [
    path("checkout/", pos_checkout, name="pos_checkout"),
    path("products/", product_search_api, name="product_search_api"),
    path("submit/", process_sale, name="process_sale"),
    path("receipt/<int:id>/", receipt_view, name="receipt"),
    path('', dashboard_views.admin_dashboard, name='index')

]