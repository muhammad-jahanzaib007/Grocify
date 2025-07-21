import json
import base64
import datetime
import treepoem  # Temporarily disabled - install with: pip install treepoem
from io import BytesIO

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required

from inventory.models import InventoryItem, StockEntry, StockLedger, Product, Location
from customers.models import Customer
from loyalty.models import LoyaltyProfile, PointTransaction
from loyalty.utils import TIER_MULTIPLIERS
from sales.models import SaleTransaction, SaleItem, Coupon
from credit.models import CreditSale


def get_selected_location(request):
    loc = request.session.get('selected_location', 'all')
    return None if loc == 'all' else int(loc)


def safe_float(value, default=0.0):
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default


@login_required
@transaction.atomic
def process_sale(request):
    if request.method != 'POST':
        return redirect('sales:index')

    # Parse cart JSON
    try:
        cart = json.loads(request.POST.get('cart') or '[]')
    except json.JSONDecodeError:
        messages.error(request, "Invalid cart data.")
        return redirect('sales:index')

    if not cart:
        messages.error(request, "🛒 Cart is empty.")
        return redirect('sales:index')

    # Payment & customer info
    payment_method  = request.POST.get('payment_method')
    amount_paid     = safe_float(request.POST.get('amount_paid'))
    discount_amount = safe_float(request.POST.get('discount_amount'))
    coupon_code     = request.POST.get('coupon_code', '').strip()
    customer_id     = request.POST.get('customer_id')
    points_used     = int(request.POST.get('points_used') or 0)

    walkin_customer = Customer.get_walkin_customer()
    customer = (
        Customer.objects.filter(id=customer_id).first()
        if customer_id else
        walkin_customer
    )

    if payment_method == 'Credit' and (not customer_id or customer_id == str(walkin_customer.id)):
        messages.error(request, "❌ Credit sales are not allowed for walk-in customers.")
        return redirect('sales:index')

    # Determine store location
    profile = request.user.userprofile
    sel = get_selected_location(request)
    if sel is not None:
        try:
            location = Location.objects.get(id=sel)
        except Location.DoesNotExist:
            messages.error(request, "Selected store not found.")
            return redirect('sales:index')
    else:
        location = profile.default_location or Location.objects.first()

    # Validate cart items
    subtotal = 0.0
    validated_cart = []
    for item in cart:
        price = safe_float(item.get('price'))
        qty = safe_float(item.get('qty'))
        if price <= 0 or qty <= 0:
            messages.error(request, f"🚫 Invalid price or quantity for '{item.get('name','Unknown')}'.")
            return redirect('sales:index')
        subtotal += price * qty
        validated_cart.append(item)

    if subtotal <= 0:
        messages.error(request, "🚫 Subtotal is zero.")
        return redirect('sales:index')

    # Apply coupon if valid
    valid_coupon = None
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            if coupon.is_valid() and subtotal >= float(coupon.minimum_amount):
                valid_coupon = coupon
                if coupon.discount_type == 'fixed':
                    discount_amount += float(coupon.discount_value)
                else:
                    discount_amount += subtotal * float(coupon.discount_value) / 100
                coupon.used_count += 1
                coupon.save()
        except Coupon.DoesNotExist:
            messages.warning(request, f"⚠️ Coupon '{coupon_code}' is invalid or expired.")

    # Calculate points usage
    max_usable_points = 0
    if customer.id != walkin_customer.id:
        max_usable_points = min(points_used, customer.points, subtotal - discount_amount)

    # Final totals
    total = max(subtotal - discount_amount - max_usable_points, 0)
    change_due = amount_paid - total if payment_method != 'Credit' else 0

    if payment_method != 'Credit' and amount_paid < total:
        messages.error(request, "🚫 Amount paid is less than total.")
        return redirect('sales:index')

    # Create SaleTransaction
    now = datetime.datetime.now()
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
        points_redeemed=max_usable_points,
        invoice_number=now.strftime("INV-%Y-%m-%d-%H-%M-%S")
    )
    tx._manual_points = True
    tx.points_earned = 0
    tx.save()

    # Calculate and record points
    tier_name = customer.tier.name if customer.tier else None
    multiplier = TIER_MULTIPLIERS.get(tier_name, 1.0)
    total_points_earned = 0

    # Batch fetch all products to avoid N+1 queries
    product_ids = [item['product_id'] for item in validated_cart]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    
    # Batch fetch all inventory items
    inventory_items = {}
    for inv in InventoryItem.objects.filter(product_id__in=product_ids, location=location):
        inventory_items[inv.product_id] = inv

    for item in validated_cart:
        product = products.get(item['product_id'])
        if not product:
            messages.error(request, f"❌ Product with ID {item['product_id']} not found.")
            return redirect('sales:index')
            
        quantity = safe_float(item['qty'])
        price = safe_float(item['price'])

        inventory = inventory_items.get(product.id)
        if not inventory:
            inventory = InventoryItem.objects.create(
                product=product,
                location=location,
                qty_on_hand=0
            )
            inventory_items[product.id] = inventory
        if inventory.qty_on_hand < quantity:
            messages.error(
                request,
                f"❌ Not enough stock for '{product.name}'. Only {inventory.qty_on_hand} left."
    )
            return redirect('sales:index')

        before_qty = inventory.qty_on_hand
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
            quantity_before=before_qty,
            quantity_changed=-quantity,
            quantity_after=inventory.qty_on_hand,
            related_entry=entry
        )

        points_earned = 0
        if customer.id != walkin_customer.id:
            base_points = product.points_per_unit * quantity
            points_earned = int(base_points * multiplier)
            total_points_earned += points_earned

        SaleItem.objects.create(
            transaction=tx,
            product=product,
            quantity=quantity,
            price_at_sale=price,
            points_earned=points_earned
        )

    tx.points_earned = total_points_earned
    tx.save(update_fields=['points_earned'])

    # Update loyalty profile
    if customer.id != walkin_customer.id:
        loyalty_profile, _ = LoyaltyProfile.objects.get_or_create(customer=customer)
        if max_usable_points > 0:
            loyalty_profile.points -= max_usable_points
            PointTransaction.objects.create(
                profile=loyalty_profile,
                points=-max_usable_points,
                transaction_type='redeemed',
                source=f"Sale #{tx.invoice_number}",
                note="Points redeemed on sale"
            )
        loyalty_profile.points += total_points_earned
        loyalty_profile.lifetime_points += total_points_earned
        loyalty_profile.save()
        PointTransaction.objects.create(
            profile=loyalty_profile,
            points=total_points_earned,
            transaction_type='earned',
            source=f"Sale #{tx.invoice_number}",
            note="Auto-awarded from completed sale"
        )

    # Handle credit sale
    if payment_method == 'Credit':
        CreditSale.objects.create(
            customer=customer,
            transaction=tx,
            credit_amount=total,
            due_date=timezone.now().date()
        )

    messages.success(request, f"✅ Sale completed. Invoice #{tx.invoice_number}")
    return redirect('sales:receipt', tx.id)


@login_required
def pos_checkout(request):
    customers = Customer.objects.filter(is_active=True).order_by('name')
    customer_points = {str(c.id): c.points for c in customers}
    loc = get_selected_location(request)

    products = Product.objects.all()
    if loc:
        products = products.filter(
            inventoryitem__location_id=loc,
            inventoryitem__qty_on_hand__gt=0
        )

    try:
        current_location = Location.objects.get(id=loc) if loc else None
    except Location.DoesNotExist:
        current_location = None

    return render(request, 'sales/pos_checkout.html', {
        'customers': customers,
        'customer_points': json.dumps(customer_points),
        'current_location': current_location,
    })


@login_required
def product_search_api(request):
    query = request.GET.get('q', '')
    qs = Product.objects.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    loc = get_selected_location(request)
    if loc:
        qs = qs.filter(
            inventoryitem__location_id=loc,
            inventoryitem__qty_on_hand__gt=0
        )

    results = [
        {'id': p.id, 'name': p.name, 'price': float(p.selling_price_with_tax or 0.0)}
        for p in qs
    ]
    return JsonResponse(results, safe=False)


@login_required
def receipt_view(request, id):
    walkin_customer = Customer.get_walkin_customer()
    transaction = get_object_or_404(SaleTransaction, id=id)
    items = transaction.items.all()

    for item in items:
        item.total_amount = (
            float(item.quantity) * float(item.price_at_sale)
            - float(item.discount_amount)
        )

    total_points_earned = sum(item.points_earned for item in items)
    points_redeemed = transaction.points_redeemed or 0
    remaining_points = transaction.customer.points
    before_points_total = transaction.total_amount + transaction.points_redeemed

    coupon_description = ''
    if transaction.coupon_code:
        try:
            coupon = Coupon.objects.get(code=transaction.coupon_code)
            coupon_description = coupon.name or coupon.code
        except Coupon.DoesNotExist:
            coupon_description = transaction.coupon_code

    # Temporarily disabled barcode generation - install treepoem to enable
    barcode_image = treepoem.generate_barcode(
        barcode_type='code128',
        data=transaction.invoice_number
    )
    buffer = BytesIO()
    barcode_image.convert('1').save(buffer, format='PNG')
    barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    barcode_uri = f"data:image/png;base64,{barcode_base64}"

    return render(request, 'sales/receipt.html', {
        'transaction': transaction,
        'items': items,
        'total_points_earned': total_points_earned,
        'points_redeemed': points_redeemed,
        'remaining_points': remaining_points,
        'before_points_total': before_points_total,
        'coupon_description': coupon_description,
        'walkin_customer_id': walkin_customer.id,
        'barcode_uri': barcode_uri,
    })


@login_required
def set_location(request):
    """
    Store the chosen location in session (or 'all').
    """
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = JsonResponse({'ok': True})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, X-Requested-With'
        return response
    
    # Only allow POST requests for actual functionality
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Parse JSON data
        if request.content_type == 'application/json':
            data = json.loads(request.body or '{}')
            loc_id = data.get('location_id')
        else:
            # Handle form data as fallback
            loc_id = request.POST.get('location_id')
        
        if not loc_id:
            return JsonResponse({'error': 'No location_id provided'}, status=400)
        
        # Check user permissions
        try:
            profile = request.user.userprofile
        except:
            profile = None
        
        # Validate location access
        if loc_id != 'all':
            if not request.user.is_superuser:
                if not profile or not profile.locations.filter(id=loc_id).exists():
                    return JsonResponse({'error': 'Access denied to this location'}, status=403)
        
        # Store in session
        request.session['selected_location'] = loc_id
        request.session.save()  # Force session save
        
        return JsonResponse({
            'ok': True, 
            'selected_location': loc_id,
            'message': f'Location switched to {loc_id}'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


@staff_member_required
def chain_dashboard(request):
    """
    Chain-wide overview of sales per location.
    """
    totals = SaleTransaction.objects.aggregate(
        total_sales=Sum('total_amount'),
        tx_count=Count('id')
    )
    by_store = (
        SaleTransaction.objects
        .values('location__name')
        .annotate(store_total=Sum('total_amount'), tx_count=Count('id'))
    )
    return render(request, 'sales/chain_dashboard.html', {
        'total': totals,
        'by_store': by_store,
    })