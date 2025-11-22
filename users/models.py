from typing import Any, ClassVar

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models

from lms.models import BaseModel


class UserManager(BaseUserManager[AbstractUser]):
    """Менеджер для кастомной модели пользователя."""

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> "User":
        """Создать и сохранить обычного пользователя."""
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)  # type: ignore[misc]
        user.set_password(password)  # type: ignore[attr-defined]
        user.save(using=self._db)  # type: ignore[attr-defined]
        return user  # type: ignore[return-value]

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any) -> "User":
        """Создать и сохранить суперпользователя."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Суперпользователь должен иметь is_staff=True")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Суперпользователь должен иметь is_superuser=True")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username: None = None  # type: ignore[assignment]

    email = models.EmailField(unique=True, verbose_name="Почта", help_text="Укажите почту")
    phone = models.CharField(max_length=35, blank=True, null=True, verbose_name="Телефон", help_text="Укажите телефон")
    city = models.CharField(max_length=50, blank=True, null=True, verbose_name="Город", help_text="Укажите город")
    avatar = models.ImageField(upload_to="users/avatars", blank=True, null=True, verbose_name="Загрузите аватар")
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()  # type: ignore[assignment]

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"


class Payment(BaseModel):
    """
    Модель платежа.

    Платёж привязан к владельцу и может быть за курс ИЛИ за отдельный урок.
    Содержит сумму оплаты, дату и способ оплаты.
    """

    PAYMENT_METHOD_CHOICES = [
        ("cash", "Наличные"),
        ("transfer", "Перевод на счёт"),
        ("stripe", "Оплата через Stripe"),
    ]

    owner: models.ForeignKey = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Владелец платежа",
        help_text="Пользователь, совершивший платёж",
    )
    payment_date: models.DateTimeField = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата оплаты",
        help_text="Дата и время совершения платежа",
    )
    course: models.ForeignKey | None = models.ForeignKey(  # type: ignore[assignment,misc]
        "lms.Course",
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
        verbose_name="Оплаченный курс",
        help_text="Курс, за который произведена оплата",
    )
    lesson: models.ForeignKey | None = models.ForeignKey(  # type: ignore[assignment,misc]
        "lms.Lesson",
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True,
        verbose_name="Оплаченный урок",
        help_text="Урок, за который произведена оплата",
    )
    amount: models.DecimalField = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма оплаты",
        help_text="Сумма платежа в рублях",
    )
    payment_method: models.CharField = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name="Способ оплаты",
        help_text="Выберите способ оплаты",
    )
    payment_link: models.URLField | None = models.URLField(  # type: ignore[assignment,misc]
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Ссылка на оплату",
        help_text="Ссылка на страницу оплаты Stripe",
    )
    stripe_session_id: models.CharField | None = models.CharField(  # type: ignore[assignment,misc]
        max_length=255,
        blank=True,
        null=True,
        verbose_name="ID сессии Stripe",
        help_text="Идентификатор платежной сессии Stripe",
    )

    class Meta:  # type: ignore[misc]
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ["-payment_date"]

    def __str__(self) -> str:
        """Строковое представление платежа."""
        if self.course:
            item = self.course.title  # type: ignore[attr-defined]
        elif self.lesson:
            item = self.lesson.title  # type: ignore[attr-defined]
        else:
            item = "Неизвестно"
        return f"Платёж {self.owner.email} - {item} - {self.amount}₽"  # type: ignore[attr-defined]

    def clean(self) -> None:
        """
        Валидация модели.

        Проверяет, что указан либо курс, либо урок (но не оба пустые).
        """
        super().clean()
        if not self.course and not self.lesson:
            raise ValidationError("Должен быть указан либо курс, либо урок для оплаты")
