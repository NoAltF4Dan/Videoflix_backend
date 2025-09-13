from django.urls import path
from .views import RegestrationView, VerifyEmailView, SendEmailForResetPasswordView, SetNewPasswordView, ResendEmailView, CookieTokenObtainView, CookieTokenRefreshView, CookieTokenLogoutView, CookieIsAuthenticatedAndVerifiedView
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)

urlpatterns = [
    path("login/", CookieTokenObtainView.as_view(), name='token_obtain_pair'),
    path("registration/", RegestrationView.as_view(), name="registration"),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('find-user/', SendEmailForResetPasswordView.as_view(), name='find_user_reset'),
    path('password_reset/', SetNewPasswordView.as_view(), name='password_reset'),
    path('resend-email/', ResendEmailView.as_view(), name='resend-email'),
    path('logout/', CookieTokenLogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('is-authenticated/', CookieIsAuthenticatedAndVerifiedView.as_view(), name='token_is_auth' )
]


