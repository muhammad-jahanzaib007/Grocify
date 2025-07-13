from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Q

from inventory.models import InventoryItem, StockEntry, StockLedger, Product, Location
from customers.models import Customer, CreditSale
from loyalty.models import LoyaltyProfile, LoyaltyTier
from loyalty.utils import calculate_earned_points, get_loyalty_tier
from sales.models import SaleTransaction, SaleItem, Coupon

import json

def safe_float(value, default=0.0):
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return default
    elif value is None:
        return default
    else:
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

# ─── SALE PROCESSING ────────────────────────────────────────────────────────────
@login_required
@transaction.atomic
def process_sale(request):
    if request.method != 'POST':
        return redirect('sales:pos_checkout')

    try:
        cart = json.loads(request.POST.get('cart') or '[]')
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

    customer = Customer.objects.filter(id=customer_id).first() if customer_id else Customer.get_walkin_customer()
    profile = getattr(request.user, 'userprofile', None)
    location = profile.default_location if profile and profile.default_location else Location.objects.first()

    subtotal = 0.0
    validated_cart = []
    for item in cart:
        price = safe_float(item.get('price'))
        qty = safe_float(item.get('qty'))
        if price <= 0 or qty <= 0:
            messages.error(request, f"🚫 Invalid price or quantity detected in cart. Check '{item.get('name', 'Unknown Product')}'.")
            return redirect('sales:pos_checkout')
        subtotal += price * qty
        validated_cart.append(item)

    if subtotal <= 0:
        messages.error(request, "🚫 Subtotal is zero. Please check product prices and quantities.")
        return redirect('sales:pos_checkout')

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

    max_usable_points = min(points_used, customer.points, subtotal - discount_amount) if customer != Customer.get_walkin_customer() else 0
    total = max(subtotal - discount_amount - max_usable_points, 0)
    change_due = amount_paid - total if payment_method != 'Credit' else 0

    if payment_method != 'Credit' and amount_paid < total:
        messages.error(request, "🚫 Amount paid is less than total. Please collect full payment.")
        return redirect('sales:pos_checkout')

    tx = SaleTransaction(
        cashier=request.user,
        customer=customer,
        location=location,
        payment_method=payment_method,
        total_amount=total,
        amount_paid=amount_paid,
        change_due=change_due,
        discount_amount=discount_amount,
        coupon_code=valid_coupon.code if valid_coupon else '',
        points_redeemed=max_usable_points
    )
    tx._manual_points = True
    tx.points_earned = 0
    tx.save()

    tier_name = customer.tier.name if customer.tier else None
    total_points_earned = 0

    for item in validated_cart:
        product = get_object_or_404(Product, id=item['product_id'])
        quantity = safe_float(item['qty'])
        price = safe_float(item['price'])

        inventory, _ = InventoryItem.objects.get_or_create(
            product=product,
            location=location,
            defaults={'qty_on_hand': 0}
        )

        if inventory.qty_on_hand < quantity:
            raise ValidationError(f"❌ Not enough stock for {product.name}.")

        if hasattr(product, 'loyalty_points') and product.loyalty_points > 0:
            points_earned = product.loyalty_points * quantity
        else:
            points_earned = 0
        total_points_earned += points_earned

        SaleItem.objects.create(
            transaction=tx,
            product=product,
            quantity=quantity,
            price_at_sale=price,
            points_earned=points_earned
        )

        before = inventory.qty_on_hand
        inventory.qty_on_hand -= quantity
        inventory.save()

        entry = StockEntry.objects.create(
            product=product,
            location=location,
            quantity=-quantity,
            entry_type='sale',
            note=f"Sold on invoice {tx.invoice_number}",
            created_by=request.user
        )

        StockLedger.objects.create(
            product=product,
            location=location,
            quantity_before=before,
            quantity_changed=-quantity,
            quantity_after=inventory.qty_on_hand,
            related_entry=entry
        )

    tx.points_earned = total_points_earned
    tx._manual_points = True
    tx.save(update_fields=['points_earned'])
    customer.points = max(customer.points - max_usable_points + total_points_earned, 0)
    customer.save()
    tx._manual_points = True
    tx.points_earned = total_points_earned
    tx.save(update_fields=['points_earned'])
    
    loyalty_profile, _ = LoyaltyProfile.objects.get_or_create(customer=customer)
    tier_name = get_loyalty_tier(loyalty_profile.lifetime_points)
    tier_instance, _ = LoyaltyTier.objects.get_or_create(
        name=tier_name,
        defaults={
            'min_points': 0,
            'discount_percent': 0,
            'badge_color': '#999999'
        }
    )

    loyalty_profile.tier = tier_instance
    loyalty_profile.save()

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

# ─── POS CHECKOUT ───────────────────────────────────────────────────────────────
@login_required
def pos_checkout(request):
    customers = Customer.objects.filter(is_active=True).order_by('name')
    customer_points = {str(c.id): c.points for c in customers}
    return render(request, 'sales/pos_checkout.html', {
        'customers': customers,
        'customer_points': json.dumps(customer_points)
    })

# ─── PRODUCT SEARCH API ─────────────────────────────────────────────────────────
def product_search_api(request):
    query = request.GET.get('q', '')
    # Fetch full product objects to access the property
    products = Product.objects.filter(
        Q(name__icontains=query) |
        Q(sku__icontains=query)
    )

    results = [
        {
            'id': p.id,
            'name': p.name,
            # Use the selling_price_with_tax property to ensure consistency
            'price': float(p.selling_price_with_tax) if p.selling_price_with_tax else 0.0
        } for p in products
    ]

    return JsonResponse(results, safe=False)

# ─── RECEIPT VIEW ───────────────────────────────────────────────────────────────
@login_required
def receipt_view(request, id):
    transaction = get_object_or_404(SaleTransaction, id=id)
    items = transaction.items.all()

    for item in items:
        item.total_amount = float(item.quantity) * float(item.price_at_sale) - float(item.discount_amount)

    total_points_earned = sum(item.points_earned for item in items)
    points_redeemed = transaction.points_redeemed or 0
    remaining_points = transaction.customer.points

    return render(request, 'sales/receipt.html', {
        'transaction': transaction,
        'items': items,
        'total_points_earned': total_points_earned,
        'points_redeemed': points_redeemed,
        'remaining_points': remaining_points
    })