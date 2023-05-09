from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = [
            "username",
        ]


class EditUserForm(UserChangeForm):
    class Meta:
        model = User
        # fields = '__all__'
        fields = [
            "first_name",
            "last_name",
        ]
