from django.urls import path
from .views import product_search_api

app_name = "api"

urlpatterns = [
    path('products/', product_search_api, name='product_search_api'),
]
