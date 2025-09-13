from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from service_app.models import Profiles
from django.db.models.signals import post_save, post_delete
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.contrib.auth.models import User
import django_rq
import os

@receiver(post_save, sender=Profiles)
def send_verification_email(sender, instance, created, **kwargs):
    queue = django_rq.get_queue('default', autocommit=True)
    queue.enqueue(sendMail,created, instance)

def sendMail(created, instance):

    if created:
        subject = "Willkommen bei Videoflix"
        from_email = "noreply@videoflix.de"
        basis_url_backend =  os.environ.get("BASIS_URL_BACKEND", default="http://localhost:8000")
        context = {
            "username": instance.user.username,
            "verify_link": f"{basis_url_backend}/api/verify-email/?token={instance.email_token}"
        }
        html_content = render_to_string("emails/verification_email.html", context)
        email = EmailMultiAlternatives(subject, "", from_email, [instance.user.email])
        email.attach_alternative(html_content, "text/html")
        email.send()

@receiver(post_delete, sender=Profiles)
def delete_auth_token(sender, instance, **kwargs):
        User.objects.get(email=instance.user.email).delete()
        