def site_context(request):
    user = request.user
    groups = set(user.groups.values_list('name', flat=True)) if user.is_authenticated else set()
    return {
        'is_dispatcher': user.is_superuser or 'Диспетчер' in groups,
        'is_manager': user.is_superuser or 'Администратор' in groups,
        'is_crew': 'Сотрудник бригады' in groups,
    }
