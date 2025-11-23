from django.urls import path

from .apps import VehicleConfig
from rest_framework.routers import DefaultRouter

from .views import (
    CarViewSet,
    MotoCreateAPIView,
    MotoListAPIView,
    MotoRetrieveAPIView,
    MotoUpdateAPIView,
    MotoDestroyAPIView,
    MilageCreateAPIView, MotoMilageListAPIView, MilageListAPIView,
)

app_name = VehicleConfig.name

router = DefaultRouter()
router.register(r"cars", CarViewSet, basename="cars")

urlpatterns = [
    path("moto/create/", MotoCreateAPIView.as_view(), name="moto-create"),
    path("moto/", MotoListAPIView.as_view(), name="moto-list"),
    path("moto/<int:pk>/", MotoRetrieveAPIView.as_view(), name="moto-get"),
    path("moto/update/<int:pk>/", MotoUpdateAPIView.as_view(), name="moto-update"),
    path("moto/delete/<int:pk>/", MotoDestroyAPIView.as_view(), name="moto-delete"),

    #milage
    path("milage/", MilageListAPIView.as_view() , name="milage-list"),
    path("milage/create/", MilageCreateAPIView.as_view() , name="milage-create"),
    path("moto/milage/", MotoMilageListAPIView.as_view() , name="moto-milage"),
] + router.urls
