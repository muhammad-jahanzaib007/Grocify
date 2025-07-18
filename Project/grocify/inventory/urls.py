from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.admin_dashboard, name='index'),  # ✅ Inventory dashboard as root
    path('stock/', views.stock_dashboard, name='stock_dashboard'),  # ✅ Now safely routable
    path('adjust-stock/<int:item_id>/', views.manual_stock_adjustment, name='adjust_stock'),
    path('ledger/', views.stock_ledger_view, name='stock_ledger'),
    path('add-product/', views.add_product, name='add_product'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('export-stock/', views.export_stock_report, name='export_stock'),
    path('api/products/', views.product_search_api, name='product_search_api'),
]