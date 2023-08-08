from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r"registration", views.UserRegistrationViewSet, basename="registration",)
router.register(r"login", views.LoginViewSet, basename="login",)
router.register(r"token_auth", views.TokenAuthenticateViewSet, basename="token_auth",)
router.register(r"profile", views.ProfileViewSet, basename="profile",)
router.register(r"friends", views.FriendViewSet, basename="friends",)
router.register(r"requests", views.RequestViewSet, basename="requests"),

urlpatterns = [
    path("", include(router.urls)),
]
