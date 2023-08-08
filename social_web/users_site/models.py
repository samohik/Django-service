from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, blank=True, null=True
    )
    username = models.CharField(
        verbose_name="имя пользователя", max_length=100
    )
    phone = models.CharField(
        verbose_name="Office phone",
        max_length=50,
        validators=[
            RegexValidator(
                regex=r"^\+\d{3}[\s\S]*\d{2}[\s\S]*\d{3}[\s\S]*\d{2}[\s\S]*\d{2}$",
                message="Phone number must be in the format: '+999999999999'.",
            )
        ],
    )

    def __str__(self):
        return self.username


class Friend(models.Model):
    user = models.ForeignKey(
        Profile,
        verbose_name="User",
        on_delete=models.CASCADE,
        related_name="user_friends",
    )
    friend = models.ForeignKey(
        Profile,
        verbose_name="Friend",
        on_delete=models.CASCADE,
        related_name="list_friend",
    )
    message = models.TextField(
        verbose_name="Messages",
    )

    def __str__(self):
        return f"{self.user}"


class FriendRequest(models.Model):
    to_user = models.ForeignKey(
        Profile,
        verbose_name="To user",
        on_delete=models.CASCADE,
        related_name="to_user",
    )
    from_user = models.ForeignKey(
        Profile,
        verbose_name="From user",
        on_delete=models.CASCADE,
        related_name="from_user",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"To: {self.to_user}, From: {self.from_user}"
