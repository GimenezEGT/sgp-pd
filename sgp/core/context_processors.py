from sgp.accounts.profiles import INTEGRITY_PROFILES, Profile, active_profiles
from sgp.core.navigation import nav_for


def sgp(request):
    context = {
        "sgp_profiles": frozenset(),
        "sgp_profile_labels": [],
        "sgp_nav": [],
        "sgp_integrity_alert": False,
    }
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return context
    profiles = active_profiles(user)
    match = getattr(request, "resolver_match", None)
    context["sgp_profiles"] = profiles
    context["sgp_profile_labels"] = [Profile(code).label for code in sorted(profiles)]
    context["sgp_nav"] = nav_for(profiles, match.view_name if match else None)
    if profiles & INTEGRITY_PROFILES:
        from sgp.audit.services import integrity_alert_active

        context["sgp_integrity_alert"] = integrity_alert_active()
    return context
