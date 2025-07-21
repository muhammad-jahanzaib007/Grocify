from django.utils       import timezone
from django.db.models  import Sum, Count, F
from purchases.models  import PurchaseOrder
from .models           import PurchaseReportSnapshot
from inventory.models  import Location

def generate_daily_purchase_snapshot(for_date=None):
    if not for_date:
        for_date = timezone.now().date()

    # Single query with grouping to avoid N+1 problem
    location_stats = (
        PurchaseOrder.objects
        .filter(date_ordered=for_date)
        .values('location')
        .annotate(
            total_orders=Count('id'),
            total_qty_ordered=Sum('items__quantity'),
            total_cost=Sum(F('items__quantity') * F('items__cost_price'))
        )
    )
    
    # Create a mapping of location stats
    stats_by_location = {stat['location']: stat for stat in location_stats}
    
    # Update snapshots for all locations
    for location in Location.objects.all():
        stats = stats_by_location.get(location.id, {
            'total_orders': 0,
            'total_qty_ordered': 0,
            'total_cost': 0
        })
        
        PurchaseReportSnapshot.objects.update_or_create(
            date=for_date,
            location=location,
            defaults={
                'total_orders': stats['total_orders'],
                'total_qty_ordered': stats['total_qty_ordered'] or 0,
                'total_cost': stats['total_cost'] or 0,
            }
        )
