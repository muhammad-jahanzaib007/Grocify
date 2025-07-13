from django.shortcuts import render, get_object_or_404, redirect
from customers.models import Customer
from .models import CreditSale, CreditPayment
from django.contrib.auth.decorators import login_required
from .forms import CreditPaymentForm  # You’ll build this next

@login_required
def credit_dashboard(request):
    customers = Customer.objects.filter(outstanding_balance__gt=0)
    return render(request, 'credit/dashboard.html', {'customers': customers})


@login_required
def customer_credit_detail(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    credit_sales = customer.creditsale_set.all()
    payments = customer.creditpayment_set.all()
    return render(request, 'credit/detail.html', {
        'customer': customer,
        'credit_sales': credit_sales,
        'payments': payments,
    })

@login_required
def add_credit_payment(request):
    if request.method == 'POST':
        form = CreditPaymentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('credit:index')
    else:
        form = CreditPaymentForm()
    return render(request, 'credit/add_payment.html', {'form': form})
@login_required
def credit_insights(request):
    from django.db.models import Sum

    total_pending = Customer.objects.aggregate(Sum('pending_balance'))['pending_balance__sum'] or 0
    top_customers = Customer.objects.order_by('-pending_balance')[:5]

    return render(request, 'credit/insights.html', {
        'total_pending': total_pending,
        'top_customers': top_customers,
    })
