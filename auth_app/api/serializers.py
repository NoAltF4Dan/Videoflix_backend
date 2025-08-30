from django.contrib.auth.models import User
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    - Validates that password and confirmed_password match.
    - Creates a new User instance with is_active=False until account activation.
    """
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {'write_only': True}  # Ensure password is write-only
        }

    def validate(self, data):
        """
        Check that password and confirmed_password match.
        """
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        """
        Create a new user with the provided email and password.

        The confirmed_password field is removed before creation.
        The user is initially inactive until activated via email.
        """
        validated_data.pop('confirmed_password')
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_active=False  # User remains inactive until activated
        )
        return user
