class SimulatedDisclosureMiddleware:
    """Attach a shared request notice used by context processors."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.simulated_disclosure = ""
        return self.get_response(request)
