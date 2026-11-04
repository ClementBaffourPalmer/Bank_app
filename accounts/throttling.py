from django.core.cache import cache
from django.http import HttpResponse
from django.template.response import TemplateResponse


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def rate_limit(key_prefix, limit=8, window=300):
    def decorator(view):
        def wrapped(request, *args, **kwargs):
            key = f"rl:{key_prefix}:{client_ip(request)}"
            count = cache.get(key, 0)
            if count >= limit:
                if request.headers.get("Accept", "").startswith("application/json"):
                    return HttpResponse("Too many attempts. Try again later.", status=429)
                return TemplateResponse(
                    request,
                    "registration/throttled.html",
                    {"message": "Too many attempts from this network. Wait a few minutes and try again."},
                    status=429,
                )
            cache.set(key, count + 1, window)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
