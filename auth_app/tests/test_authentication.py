from unittest.mock import Mock, patch

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken

from ..authentication import CookieJWTAuthentication


def test_authenticate_no_cookie():
    """Returns None when no access_token cookie is present."""
    request = Mock(COOKIES={})
    auth = CookieJWTAuthentication()
    assert auth.authenticate(request) is None


def test_authenticate_invalid_token():
    """Returns None when the access_token cookie contains an invalid JWT."""
    request = Mock(COOKIES={'access_token': 'invalid'})
    auth = CookieJWTAuthentication()
    with patch.object(CookieJWTAuthentication, 'get_validated_token', side_effect=InvalidToken()):
        assert auth.authenticate(request) is None


def test_authenticate_user_not_found():
    """Returns None when the token is valid but the user cannot be retrieved."""
    request = Mock(COOKIES={'access_token': 'valid'})
    auth = CookieJWTAuthentication()
    with patch.object(CookieJWTAuthentication, 'get_validated_token', return_value='validated_token'), \
         patch.object(CookieJWTAuthentication, 'get_user', side_effect=AuthenticationFailed()):
        result = auth.authenticate(request)
        assert result is None


def test_authenticate_success():
    """Returns (user, validated_token) when the JWT is valid and user exists."""
    request = Mock(COOKIES={'access_token': 'valid'})
    auth = CookieJWTAuthentication()
    with patch.object(CookieJWTAuthentication, 'get_validated_token', return_value='validated_token'), \
         patch.object(CookieJWTAuthentication, 'get_user', return_value='user_object'):
        result = auth.authenticate(request)
        assert result == ('user_object', 'validated_token')

