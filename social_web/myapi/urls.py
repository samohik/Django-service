from django.urls import path
from . import views


urlpatterns = [
    path(
        "registration/",
        views.UserRegistrationAPIView.as_view(),
        name="registration",
    ),
    path("friends/", views.UserFriendAPIView.as_view(), name="friends_list"),
    path(
        "friends/<int:id>/",
        views.FriendDetailAPIView.as_view(),
        name="friend_detail",
    ),
    path("requests/", views.RequestAPIView.as_view(), name="requests"),
    path(
        "requests/<int:id>",
        views.RequestDetailAPIView.as_view(),
        name="requests_detail",
    ),
]
