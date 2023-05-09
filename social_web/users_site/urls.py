from django.urls import path
from users_site.views import Main, RegisterView, AuthenticateView, LogOutView

app_name = "account"

urlpatterns = [
    path("", Main.as_view(), name="main"),
    path("login/", AuthenticateView.as_view(), name="login"),
    path("logout/", LogOutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
]
