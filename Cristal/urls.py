# Cristal/urls.py
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.views.generic import RedirectView
from Cristal_app import views as cristal_app_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    path('login/', auth_views.LoginView.as_view(template_name='Cristal_app/autenticacion/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),
    path('app/', include('Cristal_app.urls')),

    # --- URLs para el reseteo de contraseña ---
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='Cristal_app/autenticacion/password_reset_form.html', # <--- TU PLANTILLA ADMINLTE
             email_template_name='registration/password_reset_email.html',
             success_url=reverse_lazy('password_reset_done')
         ),
         name='password_reset'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='Cristal_app/autenticacion/password_reset_done.html'), # <--- TU PLANTILLA ADMINLTE
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='Cristal_app/autenticacion/password_reset_confirm.html', # <--- TU PLANTILLA ADMINLTE
             success_url=reverse_lazy('password_reset_complete')
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='Cristal_app/autenticacion/password_reset_complete.html'), # <--- TU PLANTILLA ADMINLTE
         name='password_reset_complete'),

    # --- URL para el registro ---
    path('register/', cristal_app_views.register_view, name='register'), # <-- Tu vista que renderiza register.html
]