from functools import wraps
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def roles(*names):
    def decorate(view):
        @wraps(view)
        def guarded(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.is_superuser or request.user.groups.filter(name__in=names).exists():
                return view(request, *args, **kwargs)
            raise PermissionDenied('Эта страница доступна другой роли.')
        return guarded
    return decorate
