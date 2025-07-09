from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import ValidationError
from inventory.models import InventoryItem, StockEntry, StockLedger, Product
from customers.models import Customer, CreditSale
from .models import SaleTransaction, SaleItem, Coupon
from django.http import JsonResponse
from django.db.models import Q
import json


@login_required
@transaction.atomic
def process_sale(request):
    if request.method == 'POST':
        # Parse cart
        try:
            cart_data = request.POST.get('cart')
            cart = json.loads(cart_data) if cart_data else []
        except json.JSONDecodeError:
            messages.error(request, "Invalid cart data.")
            return redirect('sales:pos')

        if not cart:
            messages.error(request, "🛒 Cart is empty.")
            return redirect('sales:pos')

        # Extract transaction details
        payment_method = request.POST.get('payment_method')
        amount_paid = float(request.POST.get('amount_paid', 0))
        discount_amount = float(request.POST.get('discount_amount', 0))
        coupon_code = request.POST.get('coupon_code', '').strip()
        customer_id = request.POST.get('customer_id')

        # Get customer or walk-in fallback
        customer = (
            Customer.objects.get(id=customer_id)
            if customer_id else Customer.get_walkin_customer()
        )

        # Calculate subtotal
        subtotal = sum(float(item['price']) * float(item['qty']) for item in cart)

        # Handle coupon logic
        valid_coupon = None
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                if coupon.is_valid() and subtotal >= float(coupon.minimum_amount):
                    valid_coupon = coupon
                    if coupon.discount_type == 'fixed':
                        discount_amount += float(coupon.discount_value)
                    elif coupon.discount_type == 'percentage':
                        discount_amount += subtotal * float(coupon.discount_value) / 100
                    coupon.used_count += 1
                    coupon.save()
            except Coupon.DoesNotExist:
                messages.warning(request, f"⚠️ Coupon '{coupon_code}' is invalid or expired.")

        total = max(subtotal - discount_amount, 0)
        change_due = amount_paid - total if payment_method != 'Credit' else 0

        # Create SaleTransaction
        tx = SaleTransaction.objects.create(
            cashier=request.user,
            customer=customer,
            location=request.user.profile.location,  # Assumes user profile has location
            payment_method=payment_method,
            total_amount=total,
            amount_paid=amount_paid,
            change_due=change_due,
            discount_amount=discount_amount,
            coupon_code=valid_coupon.code if valid_coupon else ''
        )

        # Create SaleItems and update inventory
        total_points_earned = 0
        for item in cart:
            product = Product.objects.get(id=item['product_id'])
            quantity = float(item['qty'])
            price = float(item['price'])

            # Prevent stock underflow
            inventory = InventoryItem.objects.get(product=product, location=tx.location)
            if inventory.qty_on_hand < quantity:
                raise ValidationError(f"❌ Insufficient stock for {product.name}.")

            # Loyalty points
            points_earned = int(product.points_per_unit * quantity)
            total_points_earned += points_earned

            SaleItem.objects.create(
                transaction=tx,
                product=product,
                quantity=quantity,
                price_at_sale=price,
                points_earned=points_earned
            )

            # Deduct inventory and record ledger
            before = inventory.qty_on_hand
            inventory.qty_on_hand -= int(quantity)
            inventory.save()

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

        # Reward loyalty points
        if customer:
            customer.points += total_points_earned
            customer.save()
            customer.update_tier()

        # Log credit sale
        if payment_method == 'Credit':
            CreditSale.objects.create(
                customer=customer,
                transaction=tx,
                credit_amount=total,
                balance_due=total,
                is_paid=False
            )

        messages.success(request, f"✅ Sale completed. Invoice #{tx.invoice_number}")
        return redirect('sales:receipt', tx.id)

    return redirect('sales:pos')
@login_required
def pos_checkout(request):
    customers = Customer.objects.all().order_by('name')
    return render(request, 'sales/pos_checkout.html', {'customers': customers})
def product_search_api(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(sku__icontains=query)
    ).values('id', 'name', 'selling_price')

    return JsonResponse(list(products), safe=False)
