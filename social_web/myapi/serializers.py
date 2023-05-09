from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from users_site.models import Profile, FriendRequest


class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["username", "email", "password", ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "username",
        ]


class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["username", "user_friends"]


class RequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = [
            "to_user",
        ]


class RequestDetailSerializer(serializers.Serializer):
    choices = [
        ("accept", "Accept"),
        ("not_accept", "Not accept"),
    ]
    choice = serializers.ChoiceField(choices=choices)

    class Meta:
        fields = [
            "choice",
        ]
