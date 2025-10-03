from unittest.mock import patch

from django.contrib.auth import get_user_model

import pytest
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from auth_app.api.serializers import (
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegistrationSerializer,
)

User = get_user_model()


@pytest.fixture
def user():
    """Fixture for Test-User."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpassword123',
        is_active=True
    )


@pytest.fixture
def inactive_user():
    """Fixture for inactive Test-User."""
    return User.objects.create_user(
        username='inactiveuser',
        email='inactive@example.com',
        password='testpassword123',
        is_active=False
    )


class TestRegistrationSerializer:
    """Test Suite for RegistrationSerializer."""

    @pytest.mark.django_db
    def test_registration_serializer_valid_data(self):
        """Test successful registration with valid data."""
        data = {
            'email': 'newuser@example.com',
            'password': 'validpassword123',
            'confirmed_password': 'validpassword123',
            'privacy_policy': 'on'
        }

        serializer = RegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()

        assert user.email == 'newuser@example.com'
        assert user.username == 'newuser'
        assert user.check_password('validpassword123')
        assert not user.is_active  # Should be inactive by default
        assert User.objects.filter(email='newuser@example.com').exists()

    @pytest.mark.django_db
    def test_registration_serializer_password_mismatch(self):
        """Test registration with non-matching passwords."""
        data = {
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirmed_password': 'differentpassword',
            'privacy_policy': 'on'
        }

        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'confirmed_password' in serializer.errors
        assert 'Passwords do not match' in str(serializer.errors['confirmed_password'])

    @pytest.mark.django_db
    def test_registration_serializer_duplicate_email(self, user):
        """Test registration with an already existing email."""
        data = {
            'email': user.email,  # Bereits existierende E-Mail
            'password': 'validpassword123',
            'confirmed_password': 'validpassword123',
            'privacy_policy': 'on'
        }

        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        assert 'Email or Password is invalid' in str(serializer.errors['email'])

    @pytest.mark.django_db
    def test_registration_serializer_privacy_policy_not_accepted(self):
        """Test registration without accepting the privacy policy."""
        data = {
            'email': 'newuser@example.com',
            'password': 'validpassword123',
            'confirmed_password': 'validpassword123',
            'privacy_policy': 'off'
        }

        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'privacy_policy' in serializer.errors
        assert 'Privacy policy must be accepted' in str(serializer.errors['privacy_policy'])

    @pytest.mark.django_db
    def test_registration_serializer_username_fallback(self):
        """Test username fallback for an already existing username."""
        User.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='password123'
        )

        data = {
            'email': 'testuser@newdomain.com',
            'password': 'validpassword123',
            'confirmed_password': 'validpassword123',
            'privacy_policy': 'on'
        }

        serializer = RegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()

        assert user.username.startswith('testuser_')
        assert len(user.username) == len('testuser_') + 8
        assert user.email == 'testuser@newdomain.com'

    @pytest.mark.django_db
    def test_registration_serializer_missing_required_fields(self):
        """Test registration with missing required fields."""
        data = {
            'password': 'validpassword123',
            'confirmed_password': 'validpassword123',
            # email und privacy_policy missing
        }

        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        assert 'privacy_policy' in serializer.errors

    @pytest.mark.django_db
    def test_registration_serializer_invalid_email_format(self):
        """Test registration with an invalid email format."""
        data = {
            'email': 'invalid-email-format',
            'password': 'validpassword123',
            'confirmed_password': 'validpassword123',
            'privacy_policy': 'on'
        }

        serializer = RegistrationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors


class TestCustomTokenObtainPairSerializer:
    """Test Suite for CustomTokenObtainPairSerializer."""

    @pytest.mark.django_db
    def test_token_serializer_valid_credentials(self, user):
        """Test token generation with valid credentials."""
        data = {
            'email': user.email,
            'password': 'testpassword123'
        }

        serializer = CustomTokenObtainPairSerializer(data=data)
        assert serializer.is_valid()

        validated_data = serializer.validated_data
        assert 'access' in validated_data
        assert 'refresh' in validated_data

    @pytest.mark.django_db
    def test_token_serializer_invalid_email(self):
        """Test token generation with a non-existent email."""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword'
        }

        serializer = CustomTokenObtainPairSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'Invalid email or password' in str(serializer.errors['non_field_errors'])

    @pytest.mark.django_db
    def test_token_serializer_invalid_password(self, user):
        """Test token generation with incorrect password."""
        data = {
            'email': user.email,
            'password': 'wrongpassword'
        }

        serializer = CustomTokenObtainPairSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors
        assert 'Invalid email or password' in str(serializer.errors['non_field_errors'])

    @pytest.mark.django_db
    def test_token_serializer_removes_username_field(self):
        """Test that the username field is removed from the serializer."""
        serializer = CustomTokenObtainPairSerializer()
        assert 'username' not in serializer.fields
        assert 'email' in serializer.fields
        assert 'password' in serializer.fields

    @pytest.mark.django_db
    def test_token_serializer_inactive_user(self, inactive_user):
        """Test token generation with an inactive user."""
        data = {
            'email': inactive_user.email,
            'password': 'testpassword123'
        }

        serializer = CustomTokenObtainPairSerializer(data=data)
        with pytest.raises(AuthenticationFailed) as exc_info:
            serializer.is_valid(raise_exception=True)

        assert str(exc_info.value) == 'No active account found with the given credentials'

    @pytest.mark.django_db
    def test_token_serializer_case_insensitive_email(self, user):
        """Test token generation with email case insensitivity."""
        data = {
            'email': user.email.upper(),
            'password': 'testpassword123'
        }

        serializer = CustomTokenObtainPairSerializer(data=data)
        assert serializer.is_valid()


class TestPasswordResetSerializer:
    """Test Suite for PasswordResetSerializer."""

    def test_password_reset_serializer_valid_email(self):
        """Test password reset serializer with a valid email."""
        data = {'email': 'test@example.com'}

        serializer = PasswordResetSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['email'] == 'test@example.com'

    def test_password_reset_serializer_email_normalization(self):
        """Test email normalization (lowercase, strip)."""
        data = {'email': '  TEST@EXAMPLE.COM  '}

        serializer = PasswordResetSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data['email'] == 'test@example.com'

    def test_password_reset_serializer_invalid_email(self):
        """Test password reset serializer with an invalid email."""
        data = {'email': 'invalid-email'}

        serializer = PasswordResetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors

    def test_password_reset_serializer_missing_email(self):
        """Test Password Reset Serializer without email."""
        data = {}

        serializer = PasswordResetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors


class TestPasswordResetConfirmSerializer:
    """Test Suite for PasswordResetConfirmSerializer."""

    @pytest.mark.django_db
    def test_password_reset_confirm_valid_data(self, user):
        """Test Password Reset Confirm with valid data."""
        data = {
            'new_password': 'newvalidpassword123',
            'confirm_password': 'newvalidpassword123'
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert serializer.is_valid()

        # Test save method
        updated_user = serializer.save(user)
        assert updated_user.check_password('newvalidpassword123')

    def test_password_reset_confirm_password_mismatch(self):
        """Test password reset confirm with non-matching passwords."""
        data = {
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword123'
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert 'confirm_password' in serializer.errors
        assert 'Die Passwörter stimmen nicht überein.' in str(serializer.errors['confirm_password'])

    def test_password_reset_confirm_short_password(self):
        """Test password reset confirm with a too short password."""
        data = {
            'new_password': 'short',
            'confirm_password': 'short'
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert 'new_password' in serializer.errors

    @patch('auth_app.api.serializers.validate_password')
    def test_password_reset_confirm_django_validation_error(self, mock_validate_password):
        """Test password reset confirm with Django password validation errors."""
        # Mock Django's validate_password to raise ValidationError
        mock_validate_password.side_effect = ValidationError([
            'This password is too common.',
            'This password is entirely numeric.'
        ])

        data = {
            'new_password': '12345678',
            'confirm_password': '12345678'
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert 'new_password' in serializer.errors
        assert 'This password is too common.' in serializer.errors['new_password']
        assert 'This password is entirely numeric.' in serializer.errors['new_password']

    def test_password_reset_confirm_missing_fields(self):
        """Test password reset confirm with missing fields."""
        data = {'new_password': 'onlyonepassword'}

        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert 'confirm_password' in serializer.errors

    @pytest.mark.django_db
    def test_password_reset_confirm_save_method(self, user):
        """Test save method of the password reset confirm serializer."""
        original_password = user.password

        data = {
            'new_password': 'brandnewpassword123',
            'confirm_password': 'brandnewpassword123'
        }

        serializer = PasswordResetConfirmSerializer(data=data)
        assert serializer.is_valid()

        updated_user = serializer.save(user)

        # Password should be changed
        assert updated_user.password != original_password
        assert updated_user.check_password('brandnewpassword123')

        # User should be updated in the database.
        user.refresh_from_db()
        assert user.check_password('brandnewpassword123')


class TestSerializersEdgeCases:
    """Edge Cases for all serializers."""

    @pytest.mark.django_db
    def test_registration_with_email_containing_plus(self):
        """Test registration with an email containing a '+'."""
        data = {
            'email': 'user+tag@example.com',
            'password': 'validpassword123',
            'confirmed_password': 'validpassword123',
            'privacy_policy': 'on'
        }

        serializer = RegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.email == 'user+tag@example.com'
        assert user.username == 'user+tag'  # Generates the username from the email prefix (before @).

    @pytest.mark.django_db
    def test_registration_with_unicode_email(self):
        """Test registration with Unicode characters in the email."""
        data = {
            'email': 'üser@exämple.com',
            'password': 'validpassword123',
            'confirmed_password': 'validpassword123',
            'privacy_policy': 'on'
        }

        serializer = RegistrationSerializer(data=data)

        # The serializer is expected to be invalid.
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        assert any('valid email address' in str(e) for e in serializer.errors['email'])

    @pytest.mark.django_db
    def test_token_serializer_with_empty_strings(self):
        """Test token serializer with empty strings."""
        data = {
            'email': '',
            'password': ''
        }

        serializer = CustomTokenObtainPairSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors or 'non_field_errors' in serializer.errors

    def test_password_reset_serializer_with_whitespace_only_email(self):
        """Test password reset with an email containing only whitespace."""
        data = {'email': '   '}

        serializer = PasswordResetSerializer(data=data)
        # If the email is empty after strip(), a validation error should be raised.
        assert not serializer.is_valid()

    @pytest.mark.django_db
    @patch('uuid.uuid4')
    def test_registration_username_collision_with_uuid(self, mock_uuid):
        """Test username collision with a mocked UUID."""
        mock_uuid.return_value.hex = 'abcd1234' * 4

        # Create an existing user.
        User.objects.create_user(
            username='collision',
            email='existing@example.com',
            password='password123'
        )

        data = {
            'email': 'collision@newdomain.com',
            'password': 'validpassword123',
            'confirmed_password': 'validpassword123',
            'privacy_policy': 'on'
        }

        serializer = RegistrationSerializer(data=data)
        assert serializer.is_valid()

        user = serializer.save()
        assert user.username == 'collision_abcd1234'
