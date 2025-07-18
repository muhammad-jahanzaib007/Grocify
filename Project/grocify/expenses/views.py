from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Expense

@login_required
def expenses_dashboard(request):
    return render(request, 'expenses/dashboard.html')

class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'expenses/expense_list.html'
    context_object_name = 'expenses'

class ExpenseDetailView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = 'expenses/expense_detail.html'
    context_object_name = 'expense'

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    fields = ['category', 'description', 'amount', 'vendor', 'location', 'date', 'receipt_number', 'notes', 'created_by']
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_list')

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    fields = ['category', 'description', 'amount', 'vendor', 'location', 'date', 'receipt_number', 'notes']
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_list')

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:expense_list')
