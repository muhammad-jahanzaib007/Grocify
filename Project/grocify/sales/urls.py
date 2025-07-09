from django.urls import path
from .views import pos_checkout, product_search_api


urlpatterns = [
    path("", pos_checkout, name="pos_checkout"),
    path('products/', product_search_api, name='product_search_api'),
]