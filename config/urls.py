from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Клининговая служба: администрирование'
admin.site.site_title = 'Клининговая служба'
admin.site.enable_nav_sidebar = False

urlpatterns = [
    path('', include('catalog.urls')),
    path('admin/doc/', include('django.contrib.admindocs.urls')),
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
