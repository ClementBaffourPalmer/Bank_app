def ui_preferences(request):
    dark_mode = False
    hide_balance = False
    if getattr(request, "user", None) and request.user.is_authenticated:
        preferences = getattr(request.user, "preferences", None)
        if preferences is not None:
            dark_mode = preferences.dark_mode
            hide_balance = preferences.hide_balance
    return {
        "dark_mode": dark_mode,
        "hide_balance": hide_balance,
    }
