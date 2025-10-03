from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

import pytest

from auth_app.api.views import PasswordResetConfirmView


@pytest.fixture
def active_user():
    """Create an active user for testing login and other authenticated operations."""
    return User.objects.create_user(
        username='activeuser',
        email='active@example.com',
        password='testpass123',
        is_active=True
    )


@pytest.mark.django_db
class TestIntegrationPasswordResetConfirmView:

    def test_get_user_method(self, active_user):
        """This test verifies that get_user correctly decodes the UID and returns the corresponding user."""
        view = PasswordResetConfirmView()
        uidb64 = urlsafe_base64_encode(force_bytes(active_user.pk))

        retrieved_user = view.get_user(uidb64)
        assert retrieved_user.pk == active_user.pk

    def test_get_user_invalid_uid(self):
        """This test checks that get_user raises Http404 for an invalid UID."""
        view = PasswordResetConfirmView()

        with pytest.raises(Http404):
            view.get_user('invalid-uid')

    def test_validate_token_method(self, active_user):
        """This test verifies that validate_token accepts a valid token without raising an exception."""
        view = PasswordResetConfirmView()
        valid_token = default_token_generator.make_token(active_user)

        # Should not raise exception
        view.validate_token(active_user, valid_token)

    def test_validate_token_invalid(self, active_user):
        """This test ensures that validate_token raises Http404 for an invalid token."""
        view = PasswordResetConfirmView()

        with pytest.raises(Http404):
            view.validate_token(active_user, 'invalid-token')
