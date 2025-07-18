from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.expenses_dashboard, name='index'),
    path('list/', views.ExpenseListView.as_view(), name='expense_list'),
    path('create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('<int:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
    path('<int:pk>/update/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
]