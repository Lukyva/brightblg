from django import template
register = template.Library()

@register.filter
def humanize_number(value):
    try:
        value = int(value) # ADD THIS LINE
    except (ValueError, TypeError):
        return value
    
    if value >= 1000000: 
        return f'{value/1000000:.1f}M'
    if value >= 1000: 
        return f'{value/1000:.1f}K'
    return value