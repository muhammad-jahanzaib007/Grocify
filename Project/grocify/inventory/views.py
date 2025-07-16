from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
import csv
from .models import (
    InventoryItem, StockEntry, StockLedger,
    Product, Location, Category, AuditLog
)
from .forms import StockAdjustmentForm, ProductForm

# STOCK DASHBOARD
@login_required
def stock_dashboard(request):
    location_id = request.GET.get('location')
    category_id = request.GET.get('category')
    company = request.GET.get('company')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    sort_by = request.GET.get('sort_by', 'product__name')

    filters = Q()
    if location_id:
        filters &= Q(location_id=location_id)
    if category_id:
        filters &= Q(product__category_id=category_id)
    if company:
        filters &= Q(product__company__icontains=company)
    if price_min:
        filters &= Q(product__selling_price__gte=price_min)
    if price_max:
        filters &= Q(product__selling_price__lte=price_max)

    inventory_items = (
        InventoryItem.objects
        .select_related('product', 'location')
        .filter(filters)
        .order_by(sort_by)
    )

    context = {
        'inventory_items': inventory_items,
        'locations': Location.objects.all(),
        'categories': Category.objects.all(),
        'selected_location': int(location_id) if location_id else None,
        'selected_category': int(category_id) if category_id else None,
        'company': company or '',
        'price_min': price_min or '',
        'price_max': price_max or '',
        'sort_by': sort_by,
    }
    return render(request, 'inventory/stock_dashboard.html', context)

# ADD PRODUCT
@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('inventory:stock_dashboard')
    else:
        form = ProductForm()
    return render(request, 'inventory/add_product.html', {
        'form': form,
        'title': 'Add Product'
    })

# EDIT PRODUCT
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('inventory:stock_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'inventory/edit_product.html', {
        'form': form,
        'title': f'Edit {product.name}'
    })

# MANUAL ADJUSTMENT
@login_required
def manual_stock_adjustment(request):
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            location = form.cleaned_data['location']
            quantity_change = form.cleaned_data['quantity_change']
            reason = form.cleaned_data['reason'].lower()
            note = form.cleaned_data['note']

            inventory, _ = InventoryItem.objects.get_or_create(
                product=product,
                location=location
            )

            before = inventory.qty_on_hand
            inventory.qty_on_hand = max(0, before + quantity_change)
            inventory.save()

            entry = StockEntry.objects.create(
                product=product,
                location=location,
                quantity=quantity_change,
                entry_type=reason,
                note=note,
                created_by=request.user
            )

            StockLedger.objects.create(
                product=product,
                location=location,
                quantity_before=before,
                quantity_changed=quantity_change,
                quantity_after=inventory.qty_on_hand,
                related_entry=entry
            )

            AuditLog.objects.create(
                action_type='stock_adjustment',
                user=request.user,
                product=product,
                location=location,
                related_id=entry.id,
                note=f"Manual adjustment: {quantity_change} units. Reason: {reason}. Note: {note}"
            )

            return redirect('inventory:stock_dashboard')
    else:
        form = StockAdjustmentForm()

    return render(request, 'inventory/manual_adjustment.html', {
        'form': form,
        'title': 'Manual Stock Adjustment'
    })

# STOCK LEDGER
@login_required
def stock_ledger_view(request):
    product_q = request.GET.get('product')
    location_id = request.GET.get('location')
    entry_type = request.GET.get('entry_type')

    filters = Q()
    if product_q:
        filters &= Q(product__name__icontains=product_q)
    if location_id:
        filters &= Q(location_id=location_id)
    if entry_type:
        filters &= Q(related_entry__entry_type=entry_type)

    entries = (
        StockLedger.objects
        .select_related('product', 'location', 'related_entry')
        .filter(filters)
        .order_by('-timestamp')
    )

    return render(request, 'inventory/stock_ledger.html', {
        'ledger_entries': entries,
        'locations': Location.objects.all(),
        'entry_types': StockEntry._meta.get_field('entry_type').choices
    })

# EXPORT STOCK REPORT
@login_required
def export_stock_report(request):
    location_id = request.GET.get('location')
    category_id = request.GET.get('category')
    company = request.GET.get('company')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    sort_by = request.GET.get('sort_by', 'product__name')

    filters = Q()
    if location_id:
        filters &= Q(location_id=location_id)
    if category_id:
        filters &= Q(product__category_id=category_id)
    if company:
        filters &= Q(product__company__icontains=company)
    if price_min:
        filters &= Q(product__selling_price__gte=price_min)
    if price_max:
        filters &= Q(product__selling_price__lte=price_max)

    items = (
        InventoryItem.objects
        .select_related('product', 'location')
        .filter(filters)
        .order_by(sort_by)
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock_report.csv"'

    writer = csv.writer(response)
    headers = ['Product', 'SKU', 'Company', 'Category', 'Location', 'Qty On Hand', 'Reorder Level', 'Unit', 'Sale Price']
    writer.writerow(headers)

    for item in items:
        writer.writerow([
            item.product.name,
            item.product.sku,
            item.product.company,
            item.product.category.name if item.product.category else '',
            item.location.name,
            item.qty_on_hand,
            item.product.reorder_level,
            item.product.unit,
            item.product.selling_price,
        ])

    return response

# ✅ PRODUCT SEARCH API FOR POS
@require_GET
def product_search_api(request):
    query = request.GET.get("q", "").strip()
    results = []

    if query:
        products = Product.objects.filter(name__icontains=query)[:10]

        for product in products:
            total_stock = (
                InventoryItem.objects
                .filter(product=product)
                .aggregate(qty=Sum("qty_on_hand"))
                .get("qty") or 0
            )

            if total_stock > 0:
                results.append({
                    "id": product.id,
                    "name": product.name,
                    "price": float(product.price),
                    "sku": product.sku
                })

    return JsonResponse(results, safe=False)

@login_required
def admin_dashboard(request):
    return render(request, 'dashboard/admin_dashboard.html')
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()

            # ✅ Log the edit action
            AuditLog.objects.create(
                action_type='product_edit',
                user=request.user,
                product=product,
                location=product.default_location,
                note=f"Edited product '{product.name}' (ID: {product.id}) via admin interface."
            )

            return redirect('inventory:stock_dashboard')
    else:
        form = ProductForm(instance=product)

    return render(request, 'inventory/edit_product.html', {
        'form': form,
        'title': f'Edit {product.name}'
    })
