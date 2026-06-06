from .theme import get_request_theme


def ui_theme(request):
    return {
        "ui_theme": get_request_theme(request),
    }
