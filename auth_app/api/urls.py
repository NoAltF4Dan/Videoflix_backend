from django.urls import path

from .views import RegistrationView, CookieRefreshView, CookieEmailLoginView, activate_account, \
    LogoutView, PasswordResetView, PasswordResetConfirmView, csrf


urlpatterns = [
    path('csrf/', csrf, name='csrf'),
    path('register/', RegistrationView.as_view(), name='register'),
    path('login/', CookieEmailLoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CookieRefreshView.as_view(), name='token_refresh'),
    path('activate/<str:uidb64>/<str:token>/', activate_account, name='activate_account'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
