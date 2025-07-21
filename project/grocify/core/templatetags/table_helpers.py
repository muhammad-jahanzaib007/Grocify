from django import template

register = template.Library()

@register.filter
def lookup(obj, key):
    """
    Template filter to safely access nested object attributes or dictionary keys.
    
    Usage:
    {{ object|lookup:"field_name" }}
    {{ object|lookup:"related_field__name" }}
    
    Returns the value if found, None otherwise.
    """
    if obj is None:
        return None
    
    # Handle nested field lookups (e.g., "supplier__name")
    keys = key.split('__')
    value = obj
    
    try:
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
                
        # If it's a callable (like a method), call it
        if callable(value):
            value = value()
            
        return value
    except (AttributeError, KeyError, TypeError):
        return None

@register.filter 
def slugify_status(value):
    """
    Convert status values to CSS-friendly slugs.
    
    Usage:
    {{ status|slugify_status }}
    """
    if not value:
        return ''
    
    return str(value).lower().replace(' ', '-').replace('_', '-')

@register.inclusion_tag('components/status_badge.html')
def status_badge(status, size='sm'):
    """
    Render a status badge with appropriate styling.
    
    Usage:
    {% status_badge order.status %}
    {% status_badge order.status size="lg" %}
    """
    status_classes = {
        'pending': 'warning',
        'confirmed': 'info', 
        'processing': 'primary',
        'shipped': 'secondary',
        'delivered': 'success',
        'cancelled': 'danger',
        'completed': 'success',
        'active': 'success',
        'inactive': 'secondary',
        'draft': 'secondary',
        'published': 'success',
        'archived': 'dark'
    }
    
    status_slug = slugify_status(status)
    badge_class = status_classes.get(status_slug, 'secondary')
    
    return {
        'status': status,
        'status_slug': status_slug,
        'badge_class': badge_class,
        'size': size
    }