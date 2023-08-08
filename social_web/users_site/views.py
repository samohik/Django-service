from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import PasswordChangeView, LogoutView, LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import TemplateView, UpdateView

from users_site.forms import RegisterForm


class RegisterView(SuccessMessageMixin, generic.CreateView):
    template_name = "users_site/register.html"
    success_url = reverse_lazy("account:login")
    form_class = RegisterForm
    success_message = "Your profile was created successfully"


class EditProfileView(LoginRequiredMixin, UpdateView):
    template_name = "users_site/edit_profile.html"
    model = User
    fields = ["first_name", "last_name", "phone", "image"]
    success_url = reverse_lazy("account:profile")


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = "users_site/change_password.html"
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy("account:profile")


class LogOutView(LoginRequiredMixin, LogoutView):
    template_name = "users_site/logged_out.html"


class AuthenticateView(LoginView):
    template_name = "users_site/login.html"

    def form_valid(self, form):
        return super(AuthenticateView, self).form_valid(form)


class Main(TemplateView):
    template_name = "users_site/base.html"
