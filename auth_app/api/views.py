from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    RegistrationSerializer,
)
from ..services.email_service import EmailService

User = get_user_model()


@ensure_csrf_cookie
def csrf(request):
    return JsonResponse({"detail": "CSRF cookie set"})


class RegistrationView(APIView):
    """API endpoint for registering a new user and sending a confirmation email with activation token."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Handle user registration, saves the account, generates an activation token, and triggers a confirmation email."""
        serializer = RegistrationSerializer(data=request.data)

        data = {}
        if serializer.is_valid():
            saved_account = serializer.save()

            token = default_token_generator.make_token(saved_account)

            EmailService.send_registration_confirmation_email(saved_account, token)

            data = {
                'user': {
                    'id': saved_account.pk,
                    'email': saved_account.email
                },
                'token': token
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'error': 'Email or Password is invalid'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def activate_account(request, uidb64, token):
    """Activate a user account via email verification token received in the activation link."""
    try:
        # decode user-ID from base64
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=uid)

        if not default_token_generator.check_token(user, token):
            return Response({'error': 'Token invalid or expired.'}, status=status.HTTP_400_BAD_REQUEST)

        # check if user is active
        if user.is_active:
            return Response({
                'message': 'Account is already activated.'
            }, status=status.HTTP_200_OK)

        # activate user
        user.is_active = True
        user.save()

        return Response({
            'message': 'Account successfully activated.'
        }, status=status.HTTP_200_OK)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({
            'error': 'Invalid activation link or token expired.'
        }, status=status.HTTP_400_BAD_REQUEST)


class CookieRefreshView(TokenRefreshView):
    """API endpoint to refresh access tokens using a refresh token stored in cookies."""
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Validate the refresh token from cookies, issues a new access token, and sets it in a secure cookie."""
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found!"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"detail": "Refresh token invalid!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        access_token = serializer.validated_data.get('access')
        response = Response({"message": "access Token refreshed"})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,   # always True in production
            samesite="None",
            path="/",
            domain=settings.COOKIE_DOMAIN
        )
        return response


class CookieEmailLoginView(TokenObtainPairView):
    """API endpoint for user login using email and password with JWT stored in cookies."""
    permission_classes = [AllowAny]
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """Authenticate user credentials and sets secure access and refresh tokens as cookies."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data["refresh"]
        access = serializer.validated_data["access"]

        response = Response({"message": "Login successful"})
        response.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=True,   # always True in production, better safe in .env
            samesite="None",
            path="/",
            domain=settings.COOKIE_DOMAIN
        )
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,   # always True in production, better safe in .env
            samesite="None",
            path="/",
            domain=settings.COOKIE_DOMAIN
        )
        return response


class LogoutView(APIView):
    """API endpoint for logging out and invalidating the user’s refresh token."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Blacklist the refresh token and removes authentication cookies to complete logout."""
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass

        response = Response(
            {"detail": "Logout successfully! All Tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK
        )
        response.delete_cookie("access_token", path="/", samesite="None", domain=settings.COOKIE_DOMAIN)
        response.delete_cookie("refresh_token", path="/", samesite="None", domain=settings.COOKIE_DOMAIN)
        return response


class PasswordResetView(APIView):
    """API endpoint for requesting a password reset via email."""
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate the email and, if active, sends a password reset email (without disclosing existence of accounts)."""
        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email, is_active=True)
                EmailService.send_password_reset_email(user)
            except User.DoesNotExist:
                # Return “successfully” anyway for security reasons
                # This prevents attackers from finding out which emails exist
                pass

            return Response(
                {"detail": "An email has been sent to reset your password."},
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class PasswordResetConfirmView(APIView):
    """API endpoint for confirming a password reset and setting a new password."""
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def get_user(self, uidb64):
        """Decode the uidb64 from the request and retrieves the corresponding user."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))

            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise Http404("Link invalid or expired.")
        return user

    def validate_token(self, user, token):
        """Ensure the provided token is valid and not expired for the given user."""
        if not default_token_generator.check_token(user, token):
            raise Http404("Token invalid or expired.")

    def post(self, request, uidb64, token):
        """Handle password reset confirmation by validating the token and updating the user's password."""
        try:
            user = self.get_user(uidb64)

            self.validate_token(user, token)

            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(user)

                return Response(
                    {
                        "detail": "Your Password has been successfully reset."
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Http404 as e:
            return Response(
                {
                    "detail": str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return Response(
                {
                    "detail": "An error has occurred. Please try again."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
