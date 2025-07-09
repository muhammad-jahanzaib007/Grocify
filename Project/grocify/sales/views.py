from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import ValidationError
from inventory.models import InventoryItem, StockEntry, StockLedger, Product, Location
from customers.models import Customer, CreditSale
from .models import SaleTransaction, SaleItem, Coupon
from django.http import JsonResponse
from django.db.models import Q
import json

def safe_float(value, default=0.0):
    try:
        return float(value.strip())
    except (ValueError, TypeError, AttributeError):
        return default

@login_required
@transaction.atomic
def process_sale(request):
    if request.method == 'POST':
        try:
            cart_data = request.POST.get('cart')
            cart = json.loads(cart_data) if cart_data else []
        except json.JSONDecodeError:
            messages.error(request, "Invalid cart data.")
            return redirect('sales:pos_checkout')

        if not cart:
            messages.error(request, "🛒 Cart is empty.")
            return redirect('sales:pos_checkout')

        payment_method = request.POST.get('payment_method')
        amount_paid = safe_float(request.POST.get('amount_paid'))
        discount_amount = safe_float(request.POST.get('discount_amount'))
        coupon_code = request.POST.get('coupon_code', '').strip()
        customer_id = request.POST.get('customer_id')
        points_used = int(request.POST.get('points_used') or 0)

        customer = Customer.objects.get(id=customer_id) if customer_id else Customer.get_walkin_customer()
        profile = getattr(request.user, 'userprofile', None)
        location = profile.default_location if profile and profile.default_location else Location.objects.first()

        subtotal = sum(float(item['price']) * float(item['qty']) for item in cart)

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

        # Apply points if customer has enough
        if customer != Customer.get_walkin_customer():
            if points_used > customer.points:
                messages.error(request, "🚫 Customer does not have enough loyalty points.")
                return redirect('sales:pos_checkout')
        else:
            points_used = 0  # Prevent point usage by walk-in

        total = max(subtotal - discount_amount - points_used, 0)
        change_due = amount_paid - total if payment_method != 'Credit' else 0

        if payment_method != 'Credit' and amount_paid < total:
            messages.error(request, "🚫 Amount paid is less than total. Please collect full payment.")
            return redirect('sales:pos_checkout')

        tx = SaleTransaction.objects.create(
            cashier=request.user,
            customer=customer,
            location=location,
            payment_method=payment_method,
            total_amount=total,
            amount_paid=amount_paid,
            change_due=change_due,
            discount_amount=discount_amount,
            coupon_code=valid_coupon.code if valid_coupon else '',
            points_redeemed=points_used  # Optional: add this field to SaleTransaction model
        )

        total_points_earned = 0
        for item in cart:
            product = Product.objects.get(id=item['product_id'])
            quantity = float(item['qty'])
            price = float(item['price'])

            inventory, _ = InventoryItem.objects.get_or_create(
                product=product,
                location=location,
                defaults={'qty_on_hand': 0}
            )

            if inventory.qty_on_hand < quantity:
                raise ValidationError(f"❌ Not enough stock for {product.name}.")

            points_earned = int(product.points_per_unit * quantity)
            total_points_earned += points_earned

            SaleItem.objects.create(
                transaction=tx,
                product=product,
                quantity=quantity,
                price_at_sale=price,
                points_earned=points_earned
            )

            before = inventory.qty_on_hand
            inventory.qty_on_hand -= int(quantity)
            inventory.save()

            entry = StockEntry.objects.create(
                product=product,
                location=location,
                quantity=-int(quantity),
                entry_type='sale',
                note=f"Sold on invoice {tx.invoice_number}",
                created_by=request.user
            )

            StockLedger.objects.create(
                product=product,
                location=location,
                quantity_before=before,
                quantity_changed=-int(quantity),
                quantity_after=inventory.qty_on_hand,
                related_entry=entry
            )

        # Loyalty: Burn and Earn
        customer.points = max(customer.points - points_used + total_points_earned, 0)
        customer.save()
        customer.update_tier()

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

    return redirect('sales:pos_checkout')

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

    results = [
        {
            'id': p['id'],
            'name': p['name'],
            'price': float(p['selling_price']) if p['selling_price'] else 0.0
        }
        for p in products
    ]

    return JsonResponse(results, safe=False)

@login_required
def receipt_view(request, id):
    transaction = SaleTransaction.objects.get(id=id)
    return render(request, 'sales/receipt.html', {'transaction': transaction})