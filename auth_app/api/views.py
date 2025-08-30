from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.http import urlsafe_base64_encode
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import RegisterSerializer
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False  # Benutzer erstmal deaktiviert
            user.save()

            # UID und Token für Aktivierung generieren
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"http://localhost:8000/api/activate/{uidb64}/{token}/"

            # E-Mail verschicken
            send_mail(
                "Konto Aktivieren",
                f"Klicke hier, um dein Konto zu aktivieren: {activation_link}",
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
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = get_object_or_404(User, pk=uid)

            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return Response({"message": "Account erfolgreich aktiviert."}, status=200)
            else:
                return Response({"error": "Ungültiger Token"}, status=400)

        except Exception as e:
            return Response({"error": "Ungültiger Token"}, status=400)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email und Passwort erforderlich"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Ungültige Anmeldedaten"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"error": "Ungültige Anmeldedaten"}, status=status.HTTP_401_UNAUTHORIZED)

        # JWT erstellen
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response({
            "detail": "Login successful",
            "user": {
                "id": user.id,
                "username": user.email
            }
        }, status=status.HTTP_200_OK)

        # HttpOnly-Cookies setzen
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # auf Produktion auf True setzen
            samesite="Lax"
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="Lax"
        )

        return response
    
    
class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token is None:
                return Response({"detail": "Refresh-Token fehlt."}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response(
                {"detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."},
                status=status.HTTP_200_OK
            )

            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')

            return response
        except Exception:
            return Response({"detail": "Logout fehlgeschlagen."}, status=status.HTTP_400_BAD_REQUEST)

class CookieTokenRefreshView(APIView):
    def post(self, request, *args, **kwargs):
        # Refresh-Token aus Cookies holen
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({"detail": "Refresh-Token fehlt."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Gültigkeit prüfen und neuen Access-Token erzeugen
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
        except Exception:
            return Response({"detail": "Ungültiger Refresh-Token."}, status=status.HTTP_401_UNAUTHORIZED)

        # Response mit neuem Access-Token + Cookie
        response = Response({
            "detail": "Token refreshed",
            "access": access_token
        }, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Für Prod auf True setzen
            samesite="Lax"
        )
        return response
    
class PasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email ist erforderlich."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Kein Hinweis auf Existenz eines Benutzers für Security
            return Response({"detail": "An email has been sent to reset your password."}, status=status.HTTP_200_OK)
        
        # UID und Token generieren
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"http://localhost:8000/api/password_reset_confirm/{uidb64}/{token}/"
        
        # E-Mail verschicken
        send_mail(
            "Passwort zurücksetzen",
            f"Klicke hier, um dein Passwort zurückzusetzen: {reset_link}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        
        return Response({"detail": "An email has been sent to reset your password."}, status=status.HTTP_200_OK)
    
class PasswordConfirmView(APIView):
    def post(self, request, uidb64, token):
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not new_password or not confirm_password:
            return Response({"error": "Beide Passwortfelder sind erforderlich."}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({"error": "Passwörter stimmen nicht überein."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({"error": "Ungültiger Benutzer."}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Ungültiger oder abgelaufener Token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)