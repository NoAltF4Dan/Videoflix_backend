from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get('access_key')
        if token is None:
            return None
        validated_token = self.get_validated_token(token)
        return self.get_user(validated_token), validated_token