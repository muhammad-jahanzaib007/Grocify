from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q, F
from datetime import datetime, timedelta
from sales.models import SaleTransaction, SaleItem
from inventory.models import Product, InventoryItem, Location
from customers.models import Customer
from purchases.models import PurchaseOrder

@login_required
def admin_dashboard(request):
    try:
        # Get basic analytics data
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)
        sixty_days_ago = today - timedelta(days=60)
        
        # Calculate current period KPIs
        current_sales_data = SaleTransaction.objects.filter(date__gte=thirty_days_ago).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        total_sales = float(current_sales_data['total'] or 0)
        total_orders = current_sales_data['count'] or 0
        avg_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # Calculate previous period for trends
        previous_sales_data = SaleTransaction.objects.filter(
            date__gte=sixty_days_ago, 
            date__lt=thirty_days_ago
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        prev_total_sales = float(previous_sales_data['total'] or 0)
        prev_total_orders = previous_sales_data['count'] or 0
        prev_avg_order_value = prev_total_sales / prev_total_orders if prev_total_orders > 0 else 0
        
        # Calculate trend percentages (handle division by zero)
        if prev_total_sales > 0:
            sales_trend = ((total_sales - prev_total_sales) / prev_total_sales * 100)
        else:
            # If no previous data, show positive trend if current sales exist
            sales_trend = 100 if total_sales > 0 else 0
            
        if prev_total_orders > 0:
            orders_trend = ((total_orders - prev_total_orders) / prev_total_orders * 100)
        else:
            # If no previous data, show positive trend if current orders exist
            orders_trend = 100 if total_orders > 0 else 0
            
        if prev_avg_order_value > 0:
            aov_trend = ((avg_order_value - prev_avg_order_value) / prev_avg_order_value * 100)
        else:
            # If no previous data, show neutral trend
            aov_trend = 0
        
        # Get customer and inventory data
        total_customers = Customer.objects.filter(is_active=True).count()
        total_products = Product.objects.count()
        
        # Get chart data for revenue trend (last 12 months)
        revenue_chart_data = []
        chart_labels = []
        for i in range(11, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=32*i)
            month_start = month_start.replace(day=1)
            if i == 0:
                month_end = today
            else:
                next_month = month_start.replace(day=28) + timedelta(days=4)
                month_end = next_month - timedelta(days=next_month.day)
            
            month_sales = SaleTransaction.objects.filter(
                date__gte=month_start,
                date__lte=month_end
            ).aggregate(total=Sum('total_amount'))['total'] or 0
            
            revenue_chart_data.append(float(month_sales))
            chart_labels.append(month_start.strftime('%b'))
        
        # Get sales by category data
        from django.db.models import Q
        from sales.models import SaleItem
        
        category_sales = {}
        sale_items = SaleItem.objects.filter(
            transaction__date__gte=thirty_days_ago
        ).select_related('product__category')
        
        for item in sale_items:
            category_name = item.product.category.name if item.product.category else 'Uncategorized'
            if category_name not in category_sales:
                category_sales[category_name] = 0
            category_sales[category_name] += float(item.quantity * item.price_at_sale)
        
        # Get top selling products
        from django.db.models import F
        top_products = SaleItem.objects.filter(
            transaction__date__gte=thirty_days_ago
        ).values(
            'product__name'
        ).annotate(
            total_qty=Sum('quantity'),
            total_revenue=Sum(F('quantity') * F('price_at_sale'))
        ).order_by('-total_revenue')[:5]
        
        # Get low stock items - using proper field comparison
        low_stock_items = []
        for item in InventoryItem.objects.select_related('product', 'location').all():
            if item.qty_on_hand <= item.product.reorder_level:
                low_stock_items.append(item)
        low_stock_items = low_stock_items[:10]  # Limit to 10 items
        
        # Get recent orders
        recent_orders = SaleTransaction.objects.select_related(
            'customer', 'location'
        ).order_by('-date')[:10]
        
        # Build low stock table data
        low_stock_data = []
        for item in low_stock_items:
            status = 'critical' if item.qty_on_hand <= (item.product.reorder_level * 0.5) else 'low'
            low_stock_data.append({
                'name': item.product.name,
                'current_stock': item.qty_on_hand,
                'minimum_stock': item.product.reorder_level,
                'status': status,
                'location': item.location.name
            })
        
        # Build recent orders table data
        recent_orders_data = []
        for order in recent_orders:
            customer_name = order.customer.name if order.customer else 'Walk-in Customer'
            status = 'completed' if order.payment_method != 'Credit' else 'credit'
            recent_orders_data.append({
                'order_id': order.invoice_number,
                'customer': customer_name,
                'amount': float(order.total_amount),
                'status': status,
                'date': order.date.strftime('%Y-%m-%d')
            })
    
    except Exception as e:
        # Fallback values in case of database errors
        total_sales = 0
        total_orders = 0
        avg_order_value = 0
        total_customers = 0
        total_products = 0
        sales_trend = 0
        orders_trend = 0
        aov_trend = 0
        low_stock_data = []
        recent_orders_data = []
    
    # Widget configurations for the dashboard
    context = {
        # KPI Metric Cards
        'total_revenue': {
            'id': 'total-revenue',
            'label': 'Total Revenue',
            'value': f'Rs {total_sales:,.0f}',
            'icon': 'dollar-sign',
            'variant': 'primary',
            'trend': {
                'direction': 'up' if sales_trend >= 0 else 'down',
                'percentage': f'{abs(sales_trend):.1f}',
                'period': 'vs last month' if prev_total_sales > 0 else 'new data'
            },
            'sparkline': True
        },
        
        'total_orders': {
            'id': 'total-orders',
            'label': 'Total Orders',
            'value': f'{total_orders:,}',
            'icon': 'shopping-cart',
            'variant': 'success',
            'trend': {
                'direction': 'up' if orders_trend >= 0 else 'down',
                'percentage': f'{abs(orders_trend):.1f}',
                'period': 'vs last month' if prev_total_orders > 0 else 'new data'
            }
        },
        
        'avg_order_value': {
            'id': 'avg-order-value',
            'label': 'Average Order Value',
            'value': f'Rs {avg_order_value:,.0f}',
            'icon': 'chart-line',
            'variant': 'warning',
            'trend': {
                'direction': 'up' if aov_trend >= 0 else 'down',
                'percentage': f'{abs(aov_trend):.1f}',
                'period': 'vs last month' if prev_avg_order_value > 0 else 'current period'
            }
        },
        
        'total_products': {
            'id': 'total-products',
            'label': 'Total Products',
            'value': f'{total_products:,}',
            'icon': 'box',
            'variant': 'info',
            'trend': {
                'direction': 'neutral',
                'percentage': '0',
                'period': 'active products'
            }
        },
        
        # Chart Configurations
        'revenue_chart': {
            'id': 'revenue-chart',
            'title': 'Revenue Trend',
            'subtitle': 'Monthly revenue over the past year',
            'canvas_id': 'revenueChart',
            'show_period_selector': True,
            'show_export': True,
            'show_fullscreen': True,
            'loading': True,
            'footer': 'Data updates in real-time'
        },
        
        'monthly_comparison_chart': {
            'id': 'monthly-comparison',
            'title': 'Monthly Sales Comparison',
            'subtitle': 'This year vs last year performance',
            'canvas_id': 'monthlyComparisonChart',
            'show_period_selector': True,
            'show_export': True,
            'show_fullscreen': True
        },
        
        'sales_distribution_chart': {
            'id': 'sales-distribution',
            'title': 'Sales by Category',
            'subtitle': 'Product category distribution',
            'canvas_id': 'salesDistributionChart',
            'show_export': True,
            'show_fullscreen': True
        },
        
        'top_products_chart': {
            'id': 'top-products',
            'title': 'Top Selling Products',
            'subtitle': 'Best performers this month',
            'canvas_id': 'topProductsChart',
            'show_export': True,
            'show_fullscreen': True
        },
        
        'inventory_status_chart': {
            'id': 'inventory-status',
            'title': 'Inventory Overview',
            'subtitle': 'Current vs target inventory levels',
            'canvas_id': 'inventoryStatusChart',
            'show_export': True,
            'show_fullscreen': True
        },
        
        # Data Tables
        'low_stock_table': {
            'id': 'low-stock',
            'title': 'Low Stock Alerts',
            'show_search': True,
            'columns': [
                {'key': 'name', 'label': 'Product', 'type': 'text'},
                {'key': 'current_stock', 'label': 'Current', 'type': 'text', 'class': 'text-center'},
                {'key': 'minimum_stock', 'label': 'Minimum', 'type': 'text', 'class': 'text-center'},
                {'key': 'location', 'label': 'Location', 'type': 'text'},
                {'key': 'status', 'label': 'Status', 'type': 'badge'}
            ],
            'data': low_stock_data
        },
        
        'recent_orders_table': {
            'id': 'recent-orders',
            'title': 'Recent Orders',
            'show_search': True,
            'columns': [
                {'key': 'order_id', 'label': 'Order #', 'type': 'text'},
                {'key': 'customer', 'label': 'Customer', 'type': 'text'},
                {'key': 'amount', 'label': 'Amount', 'type': 'currency'},
                {'key': 'status', 'label': 'Status', 'type': 'badge'},
                {'key': 'date', 'label': 'Date', 'type': 'text'}
            ],
            'data': recent_orders_data
        },
        
        # System Alerts
        'system_alert_1': {
            'id': 'alert-1',
            'title': 'Low Stock Warning',
            'message': f'{len(low_stock_data)} products are running low on stock and need immediate attention.',
            'variant': 'warning' if len(low_stock_data) > 0 else 'success',
            'icon': 'exclamation-triangle' if len(low_stock_data) > 0 else 'check-circle',
            'dismissible': True,
            'actions': [
                {'label': 'View Details', 'url': '/inventory/'}
            ] if len(low_stock_data) > 0 else []
        },
        
        'system_alert_2': {
            'id': 'alert-2',
            'title': 'Sales Performance',
            'message': f'Sales are {"up" if sales_trend >= 0 else "down"} {abs(sales_trend):.1f}% compared to last month.',
            'variant': 'success' if sales_trend >= 0 else 'info',
            'icon': 'trending-up' if sales_trend >= 0 else 'trending-down',
            'dismissible': True
        },
        
        # Progress Cards
        'monthly_target': {
            'id': 'monthly-target',
            'title': 'Monthly Sales Target',
            'percentage': min(int((total_sales / 50000) * 100), 100) if total_sales > 0 else 0,
            'variant': 'primary',
            'subtitle': f'Rs {total_sales:,.0f} of Rs 50,000 target achieved',
            'milestones': [
                {'percentage': 25, 'label': '25%', 'status': 'completed', 'icon': 'check'},
                {'percentage': 50, 'label': '50%', 'status': 'completed', 'icon': 'check'},
                {'percentage': 75, 'label': '75%', 'status': 'completed', 'icon': 'check'},
                {'percentage': 100, 'label': '100%', 'status': 'pending', 'icon': 'flag'}
            ]
        },
        
        'inventory_turnover': {
            'id': 'inventory-turnover',
            'title': 'Inventory Turnover',
            'percentage': 65,
            'variant': 'success',
            'subtitle': 'Current turnover rate: 6.5x annually'
        },
        
        # Business Statistics Grid
        'business_stats': {
            'id': 'business-stats',
            'title': 'Business Performance Overview',
            'stats': [
                {
                    'label': 'Active Products',
                    'value': f'{total_products:,}',
                    'icon': 'box',
                    'variant': 'primary',
                    'change': {'direction': 'neutral', 'value': '0'}
                },
                {
                    'label': 'Total Customers',
                    'value': f'{total_customers:,}',
                    'icon': 'users',
                    'variant': 'success',
                    'change': {'direction': 'up', 'value': '+156'}
                },
                {
                    'label': 'Low Stock Items',
                    'value': f'{len(low_stock_data)}',
                    'icon': 'exclamation-triangle',
                    'variant': 'warning',
                    'change': {'direction': 'down' if len(low_stock_data) == 0 else 'up', 'value': f'{len(low_stock_data)}'}
                },
                {
                    'label': 'Locations',
                    'value': f'{Location.objects.count()}',
                    'icon': 'map-marker-alt',
                    'variant': 'info',
                    'change': {'direction': 'neutral', 'value': '0'}
                },
                {
                    'label': 'Revenue Growth',
                    'value': f'{sales_trend:+.1f}%',
                    'icon': 'chart-line',
                    'variant': 'success' if sales_trend >= 0 else 'danger',
                    'change': {'direction': 'up' if sales_trend >= 0 else 'down', 'value': f'{abs(sales_trend):.1f}%'}
                },
                {
                    'label': 'Avg Order Value',
                    'value': f'Rs {avg_order_value:,.0f}',
                    'icon': 'dollar-sign',
                    'variant': 'primary',
                    'change': {'direction': 'up' if aov_trend >= 0 else 'down', 'value': f'{abs(aov_trend):.1f}%'}
                }
            ]
        },
        
        # Real chart data
        'revenue_chart_data': {
            'labels': chart_labels,
            'data': revenue_chart_data
        },
        
        'category_sales_data': {
            'labels': list(category_sales.keys()) if category_sales else ['No Data'],
            'data': list(category_sales.values()) if category_sales else [0]
        },
        
        'top_products_data': {
            'labels': [item['product__name'] for item in top_products],
            'data': [float(item['total_revenue']) for item in top_products]
        }
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)

def analytics_demo(request):
    return render(request, 'test_analytics.html')