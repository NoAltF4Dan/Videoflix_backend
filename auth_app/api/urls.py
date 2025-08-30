urlpatterns = [
    # Register new user → POST email, password
    path('register/', RegisterView.as_view(), name='register'),

    # Activate user account via email link
    path('activate/<str:uidb64>/<str:token>/', ActivateView.as_view(), name='activate'),

    # Login → returns JWT cookies
    path('login/', LoginView.as_view(), name='login'),

    # Logout → clears cookies & blacklists refresh token
    path('logout/', LogoutView.as_view(), name='logout'),

    # Refresh access token using refresh token cookie
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),

    # Request password reset email
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),

    # Confirm password reset with token
    path('password_confirm/<str:uidb64>/<str:token>/', PasswordConfirmView.as_view(), name='password_reset_confirm'),
]
