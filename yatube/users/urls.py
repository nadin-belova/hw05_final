# Импортируем из приложения django.contrib.auth нужный view-класс
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.views import PasswordChangeDoneView
from django.urls import path
from . import views


app_name = "users"

urlpatterns = [
    path(
        "logout/",
        # Прямо в описании обработчика укажем шаблон,
        # который должен применяться для отображения возвращаемой страницы.
        # Да, во view-классах так можно! Как их не полюбить.
        LogoutView.as_view(template_name="users/logged_out.html"),
        name="logout"
        # Полный адрес страницы регистрации - auth/signup/,
        # но префикс auth/ обрабатывется в головном urls.py
    ),
    # Полный адрес страницы регистрации - auth/signup/,
    # но префикс auth/ обрабатывется в головном urls.py
    path("signup/", views.SignUp.as_view(), name="signup"),
    path("login/", LoginView.as_view(
        template_name="users/login.html"),
        name="login"
    ),
    path(
        "password_change/",
        PasswordChangeView.as_view(
            template_name="users/password_change_form.html",
            success_url="auth/password_change/done/",
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        PasswordChangeDoneView.as_view(
            template_name="users/password_change_done.html"
        ),
        name="password_change_done",
    ),

]
