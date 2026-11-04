from django import template

register = template.Library()


@register.simple_tag
def simulated_balance(amount, hidden=False, currency="USD"):
    if hidden:
        return "••••••••"
    return f"${amount:,.2f} {currency}"


@register.filter
def money(amount):
    return f"${amount:,.2f}"
