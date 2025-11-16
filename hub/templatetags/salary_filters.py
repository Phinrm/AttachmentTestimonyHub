from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.filter
def money(value):
    """
    Format a numeric value with thousands separators without decimals if .00
    """
    if value is None:
        return ''
    try:
        val = float(value)
    except (TypeError, ValueError):
        return str(value)
    # Show decimals only if needed
    if val.is_integer():
        return intcomma(int(val))
    # keep two decimals
    s = f"{val:,.2f}"
    return s

@register.filter
def salary_display(job):
    """
    Render a concise salary range display using job.currency, salary_min, salary_max.
    Usage: {{ job|salary_display }}
    """
    cur = getattr(job, 'currency', '')
    smin = getattr(job, 'salary_min', None)
    smax = getattr(job, 'salary_max', None)

    if smin and smax:
        return f"{cur} {money(smin)} – {money(smax)}"
    if smin and not smax:
        return f"{cur} {money(smin)}+"
    if not smin and smax:
        return f"Up to {cur} {money(smax)}"
    return "Salary undisclosed"
