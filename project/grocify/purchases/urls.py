from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.PurchaseOrderListView.as_view(), name='index'),
    path('orders/', views.PurchaseOrderListView.as_view(), name='order_list'),
    path('orders/create/', views.PurchaseOrderCreateView.as_view(), name='order_create'),
    path('orders/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/update/', views.PurchaseOrderUpdateView.as_view(), name='order_update'),
    path('orders/<int:pk>/delete/', views.PurchaseOrderDeleteView.as_view(), name='order_delete'),
    path('items/create/', views.PurchaseItemCreateView.as_view(), name='item_create'),
    path('receipts/create/', views.PurchaseReceiptCreateView.as_view(), name='receipt_create'),
    path('receipts/<int:pk>/', views.PurchaseReceiptDetailView.as_view(), name='receipt_detail'),
]
