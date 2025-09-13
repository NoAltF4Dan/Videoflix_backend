from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from service_app.models import Profiles
import os

def send_validation_email(profil_id):
    profil = Profiles.objects.get(id = profil_id)
    subject = "Willkommen bei Videoflix"
    from_email = "noreply@videoflix.de"
    basis_url_backend = os.environ.get("BASIS_URL_BACKEND", default="http://localhost:8000")
    context = {
        "username": profil.user.username,
        "verify_link": f"{basis_url_backend}/api/verify-email/?token={profil.email_token}"
    }
    html_content = render_to_string("emails/verification_email.html", context)
    email = EmailMultiAlternatives(subject, "", from_email, [profil.user.email])
    email.attach_alternative(html_content, "text/html")
    email.send()