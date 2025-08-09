from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    path('login/', auth_views.LoginView.as_view(template_name='Cristal_app/autenticacion/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page=reverse_lazy('login')), name='logout'),
    path('app/', include('Cristal_app.urls')),

    # URLs para el reseteo de contraseña
    path('password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='Cristal_app/autenticacion/password_reset_form.html',
             email_template_name='Cristal_app/autenticacion/password_reset_email.html',
             success_url=reverse_lazy('password_reset_done')
         ),
         name='password_reset'),

    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='Cristal_app/autenticacion/password_reset_done.html'),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='Cristal_app/autenticacion/password_reset_confirm.html',
             success_url=reverse_lazy('password_reset_complete')
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='Cristal_app/autenticacion/password_reset_complete.html'),
         name='password_reset_complete'),
]