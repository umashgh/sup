class ContentSecurityPolicyMiddleware:
    """
    Adds a Content-Security-Policy header to every response.

    Sources allowed:
    - Scripts: self + JSDelivr + cdnjs (Bootstrap, Alpine, htmx, Chart.js)
    - Styles: self + unsafe-inline (Bootstrap generates inline styles)
    - Fonts: Google Fonts
    - Images: self + data URIs (Chart.js inline images)
    - Connect: self (AJAX / htmx)
    """

    CSP = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdn.jsdelivr.net; "
        "font-src 'self' fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none';"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = self.CSP
        return response
