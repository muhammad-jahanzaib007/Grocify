from django.urls import path
from .views import product_search_api, locations_api, switch_store

app_name = "api"

urlpatterns = [
    path('products/', product_search_api, name='product_search_api'),
    path('locations/', locations_api, name='locations_api'),
    path('switch-store/', switch_store, name='switch_store'),
]
