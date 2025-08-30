from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RegisterSerializer


class RegisterView(APIView):
    """
    Registers a new user.

    - Creates a user (initially inactive)
    - Generates activation UID & token
    - Sends activation email
    """
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False
            user.save()

            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"http://localhost:8000/api/activate/{uidb64}/{token}/"

            send_mail(
                "Activate Your Account",
                f"Click here to activate your account: {activation_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response({
                "user": {"id": user.id, "email": user.email},
                "activation_link": activation_link
            }, status=201)

        return Response(serializer.errors, status=400)


class ActivateView(APIView):
    """
    Activates a user account via UID and token.
    """
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)

            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return Response({"message": "Account successfully activated."}, status=200)
            else:
                return Response({"error": "Invalid token"}, status=400)

        except Exception:
            return Response({"error": "Invalid token"}, status=400)


class LoginView(APIView):
    """
    Authenticates user and sets JWT tokens in HttpOnly cookies.
    """
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            "detail": "Login successful",
            "user": {"id": user.id, "username": user.email}
        }, status=status.HTTP_200_OK)

        response.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="Lax")
        response.set_cookie("refresh_token", refresh_token, httponly=True, secure=False, samesite="Lax")

        return response


class LogoutView(APIView):
    """
    Logs out the user by blacklisting the refresh token and clearing cookies.
    """
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token is None:
                return Response({"detail": "Refresh token missing."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response(
                {"detail": "Logout successful! All tokens invalidated."},
                status=status.HTTP_200_OK
            )
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')

            return response
        except Exception:
            return Response({"detail": "Logout failed."}, status=status.HTTP_400_BAD_REQUEST)


class CookieTokenRefreshView(APIView):
    """
    Refreshes the access token using the refresh token from cookies.
    """
    def post(self, request, *args, **kwargs):
        ref
