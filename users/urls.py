"""URL routing для Users API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from users.views import PaymentViewSet, RegisterView, UserViewSet

app_name = "users"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("", include(router.urls)),
]
