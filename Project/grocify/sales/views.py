from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from inventory.models import InventoryItem, StockEntry, StockLedger, Product
from customers.models import Customer, CreditSale
from .models import SaleTransaction, SaleItem
from django.contrib import messages


@login_required
@transaction.atomic
def process_sale(request):
    if request.method == 'POST':
        cart = request.POST.getlist('cart')  # Expected format: list of dicts as JSON
        payment_method = request.POST.get('payment_method')
        amount_paid = float(request.POST.get('amount_paid', 0))
        customer_id = request.POST.get('customer_id') or None

        # Simplified example (you'd parse cart from JSON properly)
        from ast import literal_eval
        cart = literal_eval(cart[0])  # [{'product_id': 1, 'qty': 2, 'price': 150}, ...]

        if not cart:
            messages.error(request, "Cart is empty.")
            return redirect('sales:pos')

        # Get customer (or walk-in)
        if customer_id:
            customer = Customer.objects.get(id=customer_id)
        else:
            customer = Customer.get_walkin_customer()

        total = sum(float(item['price']) * float(item['qty']) for item in cart)
        change_due = amount_paid - total if payment_method != 'Credit' else 0

        # Create transaction
        tx = SaleTransaction.objects.create(
            cashier=request.user,
            customer=customer,
            location=request.user.profile.location,  # Assuming cashier has a location
            payment_method=payment_method,
            total_amount=total,
            amount_paid=amount_paid,
            change_due=change_due
        )

        for item in cart:
            product = Product.objects.get(id=item['product_id'])
            quantity = float(item['qty'])
            price = float(item['price'])

            # Create SaleItem
            SaleItem.objects.create(
                transaction=tx,
                product=product,
                quantity=quantity,
                price_at_sale=price
            )

            # Update inventory
            inventory = InventoryItem.objects.get(product=product, location=tx.location)
            before = inventory.qty_on_hand
            inventory.qty_on_hand -= int(quantity)
            inventory.save()

            # StockEntry + Ledger
            entry = StockEntry.objects.create(
                product=product,
                location=tx.location,
                quantity=-int(quantity),
                entry_type='sale',
                note=f"Sold on invoice {tx.invoice_number}",
                created_by=request.user
            )

            StockLedger.objects.create(
                product=product,
                location=tx.location,
                quantity_before=before,
                quantity_changed=-int(quantity),
                quantity_after=inventory.qty_on_hand,
                related_entry=entry
            )

        # Credit sale?
        if payment_method == 'Credit':
            CreditSale.objects.create(
                customer=customer,
                transaction=tx,
                credit_amount=total,
                balance_due=total,
                is_paid=False
            )

        messages.success(request, f"✅ Sale complete (Invoice #{tx.invoice_number})")
        return redirect('sales:receipt', tx.id)

    else:
        return redirect('sales:pos')


@login_required
def pos_checkout(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, 'sales/pos_checkout.html', {'customers': customers})