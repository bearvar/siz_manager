from django.conf import settings

THEME_LIGHT = "light"
THEME_DARK = "dark"
THEME_CHOICES = (
    (THEME_LIGHT, "Светлая"),
    (THEME_DARK, "Темная"),
)
THEME_COOKIE_NAME = "siz_theme"
THEME_COOKIE_MAX_AGE = 60 * 60 * 24 * 365
SUPPORTED_THEMES = {THEME_LIGHT, THEME_DARK}


def normalize_theme(value):
    if value in SUPPORTED_THEMES:
        return value
    return None


def get_request_theme(request):
    if request.user.is_authenticated:
        user_theme = normalize_theme(getattr(request.user, "theme", None))
        if user_theme:
            return user_theme

    cookie_theme = normalize_theme(request.COOKIES.get(THEME_COOKIE_NAME))
    if cookie_theme:
        return cookie_theme

    return THEME_LIGHT


def set_theme_cookie(response, theme):
    response.set_cookie(
        THEME_COOKIE_NAME,
        theme,
        max_age=THEME_COOKIE_MAX_AGE,
        secure=getattr(settings, "SESSION_COOKIE_SECURE", False),
        httponly=True,
        samesite="Lax",
    )
