# api/views.py
from django.http import JsonResponse
from django.db.models import Q
from inventory.models import Product, InventoryItem
from django.db.models import Sum

def product_search_api(request):
    query = request.GET.get('q', '')

    products = Product.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query)
    )

    results = []
    for p in products:
        # 🔎 Aggregate total quantity across all locations
        total_stock = (
            InventoryItem.objects
            .filter(product=p)
            .aggregate(qty=Sum("qty_on_hand"))
            .get("qty") or 0
        )

        results.append({
            'id': p.id,
            'name': p.name,
            'price': float(p.selling_price_with_tax) if p.selling_price_with_tax else 0.0,
            'stock': total_stock  # ✅ Pass stock to POS frontend
        })

    return JsonResponse(results, safe=False)

