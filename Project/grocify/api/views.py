# api/views.py
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from inventory.models import Product, InventoryItem, Location
from django.db.models import Sum
import json
import logging

logger = logging.getLogger(__name__)

@login_required
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

@login_required
def locations_api(request):
    """API endpoint to fetch all active locations"""
    locations = Location.objects.filter(is_active=True).order_by('name')
    
    results = []
    for location in locations:
        results.append({
            'id': location.id,
            'name': location.name,
            'address': location.address
        })
    
    return JsonResponse(results, safe=False)

@login_required
@require_http_methods(["POST"])
@ensure_csrf_cookie
def switch_store(request):
    """API endpoint to switch current store location"""
    logger.info(f"Store switch requested by user {request.user.id}")
    
    try:
        data = json.loads(request.body)
        store_id = data.get('store_id')
        
        if not store_id:
            logger.warning("Store switch request missing store_id")
            return JsonResponse({
                'success': False,
                'message': 'Store ID is required'
            }, status=400)
        
        try:
            location = Location.objects.get(id=store_id, is_active=True)
            
            # Store the selected location in session
            request.session['selected_location'] = location.id
            request.session['current_location_id'] = location.id
            request.session['current_location_name'] = location.name
            
            logger.info(f"User {request.user.id} switched to location {location.name}")
            
            return JsonResponse({
                'success': True,
                'message': f'Switched to {location.name}',
                'location': {
                    'id': location.id,
                    'name': location.name,
                    'address': location.address
                }
            })
        except Location.DoesNotExist:
            logger.warning(f"Location {store_id} not found during store switch")
            return JsonResponse({
                'success': False,
                'message': 'Location not found'
            }, status=404)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in store switch request")
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Unexpected error during store switch: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Internal server error'
        }, status=500)
