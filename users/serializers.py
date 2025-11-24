"""Сериализаторы для пользователей."""

from typing import Any

from rest_framework import serializers

from users.models import Payment, User


class PaymentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Payment.

    Валидирует, что указан либо курс, либо урок (минимум одно обязательно).
    """

    class Meta:  # type: ignore[misc]
        model = Payment
        fields = [
            "id",
            "owner",
            "payment_date",
            "course",
            "lesson",
            "amount",
            "payment_method",
            "payment_link",
            "stripe_session_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "payment_date", "payment_link", "stripe_session_id", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        """
        Валидация платежа.

        Проверяет, что указан либо курс, либо урок.
        При частичном обновлении (PATCH) учитывает существующие значения из instance,
        но только если поля отсутствуют (не переданы), а не если явно установлены в None.
        """
        if self.instance:
            course = attrs.get("course") if "course" in attrs else self.instance.course
            lesson = attrs.get("lesson") if "lesson" in attrs else self.instance.lesson
        else:
            course = attrs.get("course")
            lesson = attrs.get("lesson")

        if not course and not lesson:
            raise serializers.ValidationError("Должен быть указан либо курс, либо урок для оплаты")

        return attrs


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Публичный сериализатор для модели User.

    Используется для отображения профиля любого пользователя.
    Скрывает приватные данные: пароль, last_name, платежи.
    Согласно Дополнительному заданию.
    """

    class Meta:  # type: ignore[misc]
        model = User
        fields = ["id", "email", "first_name", "phone", "city", "avatar"]
        read_only_fields = ["id", "email", "first_name", "phone", "city", "avatar"]


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Детальный сериализатор для модели User.

    Используется для управления собственным профилем.
    Включает все данные, включая платежи.
    Согласно Дополнительному заданию.
    """

    password = serializers.CharField(write_only=True, required=False, style={"input_type": "password"})
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:  # type: ignore[misc]
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "city", "avatar", "password", "payments"]
        read_only_fields = ["id"]

    def create(self, validated_data: dict) -> User:
        """Создание пользователя с хешированием пароля."""
        password = validated_data.pop("password", None)
        user: User = User.objects.create(**validated_data)  # type: ignore[assignment]
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance: User, validated_data: dict) -> User:
        """Обновление пользователя с хешированием пароля."""
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.

    Требует email и password, дополнительно может принимать другие поля модели User.
    Хеширует пароль перед сохранением.
    """

    password = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:  # type: ignore[misc]
        model = User
        fields = ["id", "email", "password", "password_confirm", "first_name", "last_name", "phone", "city"]
        read_only_fields = ["id"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Проверка совпадения паролей."""
        if attrs.get("password") != attrs.get("password_confirm"):
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        """Создание пользователя с хешированием пароля."""
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user: User = User.objects.create(**validated_data)  # type: ignore[assignment]
        user.set_password(password)
        user.save()
        return user
