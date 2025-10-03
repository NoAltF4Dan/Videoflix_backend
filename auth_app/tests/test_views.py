from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.test import RequestFactory
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.exceptions import TokenError

from ..api.views import PasswordResetConfirmView


@pytest.fixture
def api_client():
    """Create an API client for making HTTP requests in tests."""
    return APIClient()


@pytest.fixture
def user():
    """Create an inactive user for testing account activation."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        is_active=False
    )


@pytest.fixture
def active_user():
    """Create an active user for testing login and other authenticated operations."""
    return User.objects.create_user(
        username='activeuser',
        email='active@example.com',
        password='testpass123',
        is_active=True
    )


@pytest.fixture
def request_factory():
    """Django's RequestFactory for creating request objects."""
    return RequestFactory()


class TestRegistrationView:
    """Test cases for user registration endpoint."""

    @pytest.mark.django_db
    @patch('auth_app.api.views.EmailService.send_registration_confirmation_email')
    @patch('auth_app.api.views.RegistrationSerializer')
    def test_registration_success(self, mock_serializer_class, mock_email_service, api_client, user):
        """Test successful user registration."""
        # Setup mocks
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = user
        mock_serializer_class.return_value = mock_serializer

        data = {'email': 'test@example.com', 'password': 'testpass123'}

        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'token' in response.data
        assert response.data['user']['email'] == user.email
        mock_email_service.assert_called_once()

    @pytest.mark.django_db
    @patch('auth_app.api.views.RegistrationSerializer')
    def test_registration_invalid_data(self, mock_serializer_class, api_client):
        """Test registration with invalid data."""
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = False
        mock_serializer_class.return_value = mock_serializer

        data = {'email': 'invalid-email', 'password': '123'}

        response = api_client.post('/api/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data


class TestActivateAccountView:
    """Test cases for account activation endpoint."""

    @pytest.mark.django_db
    def test_activate_account_success(self, api_client, user):
        """Test successful account activation."""
        # Generate valid token and uidb64
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        response = api_client.get(f'/api/activate/{uidb64}/{token}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Account successfully activated.'

        # Verify user is now active
        user.refresh_from_db()
        assert user.is_active is True

    @pytest.mark.django_db
    def test_activate_already_active_account(self, api_client, active_user):
        """Test activation of already active account."""
        token = default_token_generator.make_token(active_user)
        uidb64 = urlsafe_base64_encode(force_bytes(active_user.pk))

        response = api_client.get(f'/api/activate/{uidb64}/{token}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Account is already activated.'

    @pytest.mark.django_db
    def test_activate_invalid_token(self, api_client, user):
        """Test activation with invalid token."""
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        invalid_token = 'invalid-token'

        response = api_client.get(f'/api/activate/{uidb64}/{invalid_token}/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Token invalid or expired' in response.data['error']

    @pytest.mark.django_db
    def test_activate_invalid_uidb64(self, api_client):
        """Test activation with invalid uidb64 parameter."""
        invalid_uidb64 = 'invalid-uid'
        token = 'some-token'

        response = api_client.get(f'/api/activate/{invalid_uidb64}/{token}/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid activation link or token expired' in response.data['error']


class TestCookieLoginView:
    """Test cases for cookie-based JWT login."""

    @pytest.mark.django_db
    @patch('auth_app.api.views.TokenObtainPairView.post')
    def test_cookie_login_success(self, mock_super_post, api_client, active_user):
        """Test successful login with cookie token storage."""
        # Mock the parent's post method
        mock_response = Mock()
        mock_response.data = {
            'access': 'test-access-token',
            'refresh': 'test-refresh-token'
        }
        mock_super_post.return_value = mock_response

        data = {'email': 'active@example.com', 'password': 'testpass123'}
        response = api_client.post('/api/login/', data)
        print(response.status_code)
        print(response.data)

        assert response.data['message'] == 'Login successful'
        assert 'access_token' in response.cookies
        assert 'refresh_token' in response.cookies
        assert response.cookies['access_token']['httponly'] is True


class TestCookieRefreshView:
    """Test cases for JWT token refresh endpoint."""

    @pytest.mark.django_db
    @patch('auth_app.api.views.TokenRefreshView.get_serializer')
    def test_refresh_token_success(self, mock_get_serializer, api_client, active_user):
        """Test successful token refresh."""

        # Setup mock serializer
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'access': 'new-access-token'}
        mock_get_serializer.return_value = mock_serializer

        api_client.cookies['refresh_token'] = 'valid-refresh-token'

        response = api_client.post('/api/token/refresh/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'access Token refreshed'
        assert 'access_token' in response.cookies

    @pytest.mark.django_db
    def test_refresh_token_missing(self, api_client):
        """Test refresh attempt without refresh token."""
        response = api_client.post('/api/token/refresh/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Refresh token not found' in response.data['detail']

    @pytest.mark.django_db
    @patch('auth_app.api.views.TokenRefreshView.get_serializer')
    def test_refresh_token_invalid(self, mock_get_serializer, api_client):
        """Test refresh with invalid token."""
        mock_serializer = Mock()
        mock_serializer.is_valid.side_effect = Exception('Invalid token')
        mock_get_serializer.return_value = mock_serializer

        api_client.cookies['refresh_token'] = 'invalid-refresh-token'

        response = api_client.post('/api/token/refresh/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'Refresh token invalid' in response.data['detail']


class TestCookieEmailLoginView:
    """Test cases for email-based login with cookie storage."""

    @pytest.mark.django_db
    @patch('auth_app.api.views.CustomTokenObtainPairSerializer')
    def test_email_login_success(self, mock_serializer_class, api_client, active_user):
        """Test successful email-based login."""
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {
            'access': 'test-access-token',
            'refresh': 'test-refresh-token'
        }
        mock_serializer_class.return_value = mock_serializer

        data = {'email': 'active@example.com', 'password': 'testpass123'}
        response = api_client.post('/api/login/', data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['message'] == 'Login successful'
        assert 'access_token' in response.cookies
        assert 'refresh_token' in response.cookies


class TestLogoutView:
    """Test cases for user logout endpoint."""

    @pytest.mark.django_db
    @patch('auth_app.api.views.RefreshToken')
    def test_logout_success(self, mock_refresh_token_class, api_client):
        """Test successful user logout."""
        mock_token = Mock()
        mock_refresh_token_class.return_value = mock_token

        api_client.cookies['refresh_token'] = 'valid-refresh-token'

        response = api_client.post('/api/logout/')

        assert response.status_code == status.HTTP_200_OK
        assert 'Logout successfully' in response.data['detail']
        mock_token.blacklist.assert_called_once()

        # Check cookies are deleted
        assert response.cookies['access_token']['expires'] is not None
        assert response.cookies['refresh_token']['expires'] is not None

    @pytest.mark.django_db
    def test_logout_missing_token(self, api_client):
        """Test logout attempt without refresh token."""
        response = api_client.post('/api/logout/')

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    @patch('auth_app.api.views.RefreshToken')
    def test_logout_invalid_token(self, mock_refresh_token_class, api_client):
        """
        Test logout with invalid refresh token.
        """
        mock_refresh_token_class.side_effect = TokenError('Invalid token')

        api_client.cookies['refresh_token'] = 'invalid-refresh-token'

        response = api_client.post('/api/logout/')

        assert response.status_code == status.HTTP_200_OK


class TestPasswordResetView:
    """Test cases for password reset request endpoint."""

    @pytest.mark.django_db
    @patch('auth_app.api.views.EmailService.send_password_reset_email')
    @patch('auth_app.api.views.PasswordResetSerializer')
    def test_password_reset_success(self, mock_serializer_class, mock_email_service, api_client, active_user):
        """Test successful password reset request."""
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'email': 'active@example.com'}
        mock_serializer_class.return_value = mock_serializer

        data = {'email': 'active@example.com'}
        response = api_client.post('/api/password_reset/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'An email has been sent' in response.data['detail']
        mock_email_service.assert_called_once_with(active_user)

    @pytest.mark.django_db
    @patch('auth_app.api.views.PasswordResetSerializer')
    def test_password_reset_user_not_exists(self, mock_serializer_class, api_client):
        """This test ensures a password reset request for a non-existent email returns success."""
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'email': 'nonexistent@example.com'}
        mock_serializer_class.return_value = mock_serializer

        data = {'email': 'nonexistent@example.com'}
        response = api_client.post('/api/password_reset/', data)

        # Should still return success for security reasons
        assert response.status_code == status.HTTP_200_OK
        assert 'An email has been sent' in response.data['detail']

    @pytest.mark.django_db
    @patch('auth_app.api.views.PasswordResetSerializer')
    def test_password_reset_invalid_data(self, mock_serializer_class, api_client):
        """This test checks that invalid password reset data returns a 400 error."""
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {'email': ['This field is required.']}
        mock_serializer_class.return_value = mock_serializer

        response = api_client.post('/api/password_reset/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data


class TestPasswordResetConfirmView:

    @patch('auth_app.api.views.PasswordResetConfirmSerializer')
    @pytest.mark.django_db
    def test_password_reset_confirm_success(self, mock_serializer_class, api_client, active_user):
        """This test verifies that a valid password reset confirmation succeeds."""
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer

        token = default_token_generator.make_token(active_user)
        uidb64 = urlsafe_base64_encode(force_bytes(active_user.pk))

        data = {'new_password': 'newpass123', 'confirm_password': 'newpass123'}
        response = api_client.post(f'/api/password_confirm/{uidb64}/{token}/', data)

        print(response.status_code, response.data)  # Debug
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_password_reset_confirm_invalid_token(self, api_client, active_user):
        """This test ensures that a password reset confirmation with an invalid token fails."""
        uidb64 = urlsafe_base64_encode(force_bytes(active_user.pk))
        invalid_token = 'invalid-token'

        data = {'new_password1': 'newpass123', 'new_password2': 'newpass123'}
        response = api_client.post(f'/api/password_confirm/{uidb64}/{invalid_token}/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Token invalid or expired' in response.data['detail']

    @pytest.mark.django_db
    def test_password_reset_confirm_invalid_uid(self, api_client):
        """This test ensures that a password reset confirmation with an invalid UID fails."""
        invalid_uidb64 = 'invalid-uid'
        token = 'some-token'

        data = {'new_password1': 'newpass123', 'new_password2': 'newpass123'}
        response = api_client.post(f'/api/password_confirm/{invalid_uidb64}/{token}/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Link invalid or expired' in response.data['detail']

    @pytest.mark.django_db
    @patch('auth_app.api.views.PasswordResetConfirmSerializer')
    def test_password_reset_confirm_invalid_serializer(self, mock_serializer_class, api_client, active_user):
        """This test checks that a password reset confirmation with invalid serializer data fails."""
        mock_serializer = Mock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {'new_password2': ['Passwords do not match.']}
        mock_serializer_class.return_value = mock_serializer

        token = default_token_generator.make_token(active_user)
        uidb64 = urlsafe_base64_encode(force_bytes(active_user.pk))

        data = {'new_password': 'newpass123', 'confirm_password': 'different123'}
        response = api_client.post(f'/api/password_confirm/{uidb64}/{token}/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'confirm_password' in response.data

    @pytest.mark.django_db
    @patch.object(PasswordResetConfirmView, 'serializer_class')
    def test_password_reset_confirm_general_exception(self, mock_serializer_class, api_client, active_user):
        """This test ensures that a general exception during password reset confirmation returns a 500 error."""
        mock_serializer_class.side_effect = Exception('Database error')

        token = default_token_generator.make_token(active_user)
        uidb64 = urlsafe_base64_encode(force_bytes(active_user.pk))

        data = {'new_password': 'newpass123', 'confirm_password': 'newpass123'}
        response = api_client.post(f'/api/password_confirm/{uidb64}/{token}/', data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'An error has occurred' in response.data['detail']
