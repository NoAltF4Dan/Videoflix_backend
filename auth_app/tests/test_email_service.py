from smtplib import SMTPException
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.template.exceptions import TemplateDoesNotExist
from django.test import override_settings

import pytest

from auth_app.services.email_service import EmailService


@pytest.fixture
def user():
    """Fixture for Test-User."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def mock_logger():
    """Fixture for Logger Mock."""
    with patch('auth_app.services.email_service.logger') as mock_log:
        yield mock_log


class TestEmailService:
    """Test Suite for EmailService."""

    @pytest.mark.django_db
    @patch('auth_app.services.email_service.send_mail')
    @patch('auth_app.services.email_service.render_to_string')
    @override_settings(
        SITE_URL='https://example.com',
        SITE_NAME='Test Site',
        DEFAULT_FROM_EMAIL='noreply@example.com'
    )
    def test_send_password_reset_email_success(self, mock_render, mock_send_mail, user, mock_logger):
        """Test successful sending of a password reset email."""
        # Mock template rendering
        mock_render.side_effect = [
            'Text message content',  # .txt template
            '<html>HTML content</html>'  # .html template
        ]

        # Mock token generation
        with patch('auth_app.services.email_service.default_token_generator.make_token') as mock_token:
            mock_token.return_value = 'test-token-123'

            # Call method
            EmailService.send_password_reset_email(user)

            # Assertions
            assert mock_render.call_count == 2

            # Check text template call
            mock_render.assert_any_call(
                'auth_app/emails/password_reset.txt',
                context={
                    'user': user,
                    'reset_url': f'https://example.com/pages/auth/confirm_password.html?uid={mock_render.call_args_list[0][1]["context"]["reset_url"].split("uid=")[1].split("&")[0]}&token=test-token-123',
                    'site_name': 'Test Site',
                }
            )

            # Check HTML template call
            mock_render.assert_any_call(
                'auth_app/emails/password_reset.html',
                context={
                    'user': user,
                    'reset_url': mock_render.call_args_list[1][1]["context"]["reset_url"],
                    'site_name': 'Test Site',
                }
            )

            # Check send_mail call
            mock_send_mail.assert_called_once_with(
                subject='Passwort zurücksetzen',
                message='Text message content',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],
                html_message='<html>HTML content</html>',
                fail_silently=False,
            )

            # Check success log
            mock_logger.info.assert_called_once_with(
                "Email successfully sent to test@example.com | Subject: 'Passwort zurücksetzen'"
            )

    @pytest.mark.django_db
    @patch('auth_app.services.email_service.send_mail')
    @patch('auth_app.services.email_service.render_to_string')
    @override_settings(
        SITE_URL='https://example.com',
        DEFAULT_FROM_EMAIL='noreply@example.com'
    )
    def test_send_registration_confirmation_email_success(self, mock_render, mock_send_mail, user, mock_logger):
        """Test successful sending of a registration confirmation email."""
        test_token = 'confirmation-token-456'

        # Mock template rendering
        mock_render.side_effect = [
            'Registration confirmation text',
            '<html>Registration confirmation HTML</html>'
        ]

        # Call method
        EmailService.send_registration_confirmation_email(user, test_token)

        # Assertions
        assert mock_render.call_count == 2

        # Check send_mail call
        mock_send_mail.assert_called_once_with(
            subject='Bestätige deine Registrierung',
            message='Registration confirmation text',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            html_message='<html>Registration confirmation HTML</html>',
            fail_silently=False,
        )

    @pytest.mark.django_db
    @patch('auth_app.services.email_service.send_mail')
    @patch('auth_app.services.email_service.render_to_string')
    def test_send_templated_email_html_template_not_found(self, mock_render, mock_send_mail, user, mock_logger):
        """Test email sending when the HTML template is not found (should use text only)."""
        # Mock: Text template exists, HTML template doesn't
        def render_side_effect(template_path, context):
            if template_path.endswith('.html'):
                raise TemplateDoesNotExist(template_path)
            return 'Text only content'

        mock_render.side_effect = render_side_effect

        # Call method
        EmailService._send_templated_email(
            template_name='test_template',
            subject='Test Subject',
            recipient='test@example.com',
            context={'user': user}
        )

        # Should send email with text only
        mock_send_mail.assert_called_once_with(
            subject='Test Subject',
            message='Text only content',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['test@example.com'],
            html_message=None,
            fail_silently=False,
        )

    @pytest.mark.django_db
    @patch('auth_app.services.email_service.send_mail')
    @patch('auth_app.services.email_service.render_to_string')
    def test_send_templated_email_text_template_not_found(self, mock_render, mock_send_mail, user, mock_logger):
        """Test email sending fails when the text template is not found."""
        # Mock: Text template doesn't exist
        mock_render.side_effect = TemplateDoesNotExist('test_template.txt')

        # Should raise exception
        with pytest.raises(TemplateDoesNotExist):
            EmailService._send_templated_email(
                template_name='test_template',
                subject='Test Subject',
                recipient='test@example.com',
                context={'user': user}
            )

        # Should log error
        mock_logger.error.assert_called_once_with(
            "Required text template 'test_template.txt' not found. Email not sent."
        )

        # Should not send email
        mock_send_mail.assert_not_called()

    @pytest.mark.django_db
    @patch('auth_app.services.email_service.send_mail')
    @patch('auth_app.services.email_service.render_to_string')
    def test_send_templated_email_smtp_exception(self, mock_render, mock_send_mail, user, mock_logger):
        """Test SMTP exception during email sending."""
        # Mock successful template rendering
        mock_render.side_effect = ['Text content', '<html>HTML content</html>']

        # Mock SMTP exception
        smtp_error = SMTPException("SMTP server error")
        mock_send_mail.side_effect = smtp_error

        # Should raise SMTP exception
        with pytest.raises(SMTPException):
            EmailService._send_templated_email(
                template_name='test_template',
                subject='Test Subject',
                recipient='test@example.com',
                context={'user': user}
            )

        # Should log SMTP error
        mock_logger.error.assert_called_once_with(
            "SMTP error while sending email to test@example.com: SMTP server error"
        )

    @pytest.mark.django_db
    @patch('auth_app.services.email_service.send_mail')
    @patch('auth_app.services.email_service.render_to_string')
    def test_send_templated_email_unexpected_exception(self, mock_render, mock_send_mail, user, mock_logger):
        """Test unexpected exception during email sending."""
        # Mock successful template rendering
        mock_render.side_effect = ['Text content', None]  # HTML template not found

        # Mock unexpected exception
        unexpected_error = ValueError("Unexpected error")
        mock_send_mail.side_effect = unexpected_error

        # Should raise the unexpected exception
        with pytest.raises(ValueError):
            EmailService._send_templated_email(
                template_name='test_template',
                subject='Test Subject',
                recipient='test@example.com',
                context={'user': user}
            )

        # Should log unexpected error
        mock_logger.exception.assert_called_once_with(
            "Unexpected error while sending email to test@example.com: Unexpected error"
        )

    @pytest.mark.django_db
    @patch('auth_app.services.email_service.send_mail')
    @patch('auth_app.services.email_service.render_to_string')
    @override_settings(SITE_NAME=None)  # Test fallback for SITE_NAME
    def test_send_password_reset_email_without_site_name(self, mock_render, mock_send_mail, user):
        """Test password reset email without SITE_NAME setting (should use fallback)."""
        mock_render.side_effect = ['Text content', '<html>HTML content</html>']

        with patch('auth_app.services.email_service.default_token_generator.make_token') as mock_token:
            mock_token.return_value = 'test-token'

            EmailService.send_password_reset_email(user)

            # render_to_string sollte zweimal aufgerufen werden: Text & HTML
            assert mock_render.call_count == 2

            # Erstes Call: Text-Template
            text_call_kwargs = mock_render.call_args_list[0][1]  # kwargs aus dem Call
            context_used = text_call_kwargs['context']
            assert context_used['site_name'] == 'Fallback Site Name'

            # Optional: prüfen, dass send_mail korrekt aufgerufen wurde
            mock_send_mail.assert_called_once()

    @pytest.mark.django_db
    @override_settings(SITE_URL='https://example.com')
    def test_password_reset_url_format(self, user):
        """Test correct URL format for password reset."""
        with patch('auth_app.services.email_service.default_token_generator.make_token') as mock_token, \
             patch('auth_app.services.email_service.render_to_string') as mock_render, \
             patch('auth_app.services.email_service.send_mail'):

            mock_token.return_value = 'test-token-123'
            mock_render.side_effect = ['Text', 'HTML']

            EmailService.send_password_reset_email(user)

            # Get the context from the render call
            text_call_kwargs = mock_render.call_args_list[0][1]  # kwargs
            context = text_call_kwargs['context']
            reset_url = context['reset_url']

            # Check URL format
            assert reset_url.startswith('https://example.com/pages/auth/confirm_password.html?uid=')
            assert '&token=test-token-123' in reset_url

    @pytest.mark.django_db
    @override_settings(SITE_URL='https://example.com')
    def test_registration_confirmation_url_format(self, user):
        """Test correct URL format for registration confirmation."""
        test_token = 'confirmation-token-456'

        with patch('auth_app.services.email_service.render_to_string') as mock_render, \
             patch('auth_app.services.email_service.send_mail'):

            mock_render.side_effect = ['Text', 'HTML']

            EmailService.send_registration_confirmation_email(user, test_token)

            # Get the context from the render call
            text_call_kwargs = mock_render.call_args_list[0][1]  # kwargs
            context = text_call_kwargs['context']
            confirmation_url = context['confirmation_url']

            # Check URL format
            assert confirmation_url.startswith('https://example.com/pages/auth/activate.html?uid=')
            assert f'&token={test_token}' in confirmation_url
