from django.urls import path
from .views import pos_checkout

urlpatterns = [
    path("pos/", pos_checkout, name="pos_checkout"),
]