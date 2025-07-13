# api/views.py
from django.http import JsonResponse
from django.db.models import Q
from inventory.models import Product

def product_search_api(request):
    query = request.GET.get('q', '')
    # Fetch full product objects to access the property
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query)
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