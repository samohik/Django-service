from django.contrib import admin

from users_site.models import (
    Profile,
    Friend,
    FriendRequest,
)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["username", "id"]


@admin.register(Friend)
class FriendsAdmin(admin.ModelAdmin):
    list_display = ["user", "friend"]


@admin.register(FriendRequest)
class RequestAdmin(admin.ModelAdmin):
    list_display = ["from_user", "to_user", "accepted"]
