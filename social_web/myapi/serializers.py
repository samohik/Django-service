import datetime

from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from users_site.models import Profile, FriendRequest, Friend


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
    phone = serializers.CharField(
        required=False,
        validators=[
            RegexValidator(
                regex=r"^\+\d{3}[\s\S]*\d{2}[\s\S]*\d{3}[\s\S]*\d{2}[\s\S]*\d{2}$",
                message="Phone number must be in the format: '+999999999999'.",
            )
        ],
    )
    username = serializers.CharField(
        required=False,
    )

    class Meta:
        model = Profile
        fields = [
            "username",
            "phone",
        ]


class MessageSerializer(serializers.ModelSerializer):
    # user = serializers.IntegerField(required=False)
    # friend = serializers.IntegerField(required=False)
    messages = serializers.CharField()

    class Meta:
        model = Friend
        fields = [
            # "user",
            # "friend",
            "messages",
        ]

    def create(self, validated_data):
        p_user = validated_data['user']
        p_friend = validated_data['friend']

        # print(type(user), type(friend))

        messages = validated_data.pop('messages')

        user = Friend.objects.filter(
            user=p_user,
            friend=p_friend,
        ).first()

        # print(user.message)

        friend = Friend.objects.filter(
            user=p_friend,
            friend=p_user,
        ).first()

        message = f"{datetime.datetime.now().strftime('%Y.%m.%d|%H:%M')}|{user.user}: {messages}\n"

        user.message += message
        user.save()

        friend.message += message
        friend.save()

        return message


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
    choice = serializers.ChoiceField(
        required=True,
        choices=choices,
    )

    class Meta:
        fields = [
            "choice",
        ]


class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs, ):
        username = self.context['request'].data.get('username')
        password = self.context['request'].data.get('password')

        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed('Invalid login credentials.')

        login(self.context['request'], user)
        return user
