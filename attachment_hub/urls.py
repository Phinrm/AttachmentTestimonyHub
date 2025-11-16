from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),

    # point LoginView at your existing template
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='hub/login.html'
    ), name='login'),

    # logout can stay default
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # keep the rest of the auth routes (password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    # your app (namespaced)
    path('', include(('hub.urls', 'hub'), namespace='hub')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
