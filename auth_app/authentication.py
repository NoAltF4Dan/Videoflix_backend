from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework.exceptions import AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    """
    Reads the JWT access token from an HttpOnly cookie.
    Expects a cookie named access_token.
    """

    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return None  # No token -> try next authentication

        try:
            validated_token = self.get_validated_token(access_token)
        except InvalidToken:
            return None

        try:
            user = self.get_user(validated_token)
        except AuthenticationFailed:
            return None

        return (user, validated_token)
