from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    """
    Базовая абстрактная модель с временными метками.

    Все модели наследуются от этого класса для автоматического
    добавления полей created_at и updated_at.
    """

    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        abstract = True


class Course(BaseModel):
    """
    Модель курса.

    Курс содержит название, описание и опциональное превью изображение.
    К курсу привязываются уроки через ForeignKey.
    Каждый курс имеет владельца (owner).
    """

    owner: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="Владелец курса",
        help_text="Пользователь, создавший курс",
    )
    title: models.CharField = models.CharField(
        max_length=200, verbose_name="Название курса", help_text="Укажите название курса"
    )
    description: models.TextField = models.TextField(
        verbose_name="Описание курса", help_text="Подробное описание курса"
    )
    preview: models.ImageField = models.ImageField(
        upload_to="courses/previews/",
        blank=True,
        null=True,
        verbose_name="Превью курса",
        help_text="Загрузите изображение для превью курса",
    )
    last_notification_sent: models.DateTimeField = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последнее уведомление отправлено",
        help_text="Время последнего отправленного уведомления подписчикам о курсе",
    )

    class Meta:  # type: ignore[misc]
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Строковое представление курса."""
        return self.title


class Lesson(BaseModel):
    """
    Модель урока.

    Урок принадлежит курсу и содержит название, описание,
    опциональное превью и ссылку на видео.
    Каждый урок имеет владельца (owner).
    """

    owner: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Владелец урока",
        help_text="Пользователь, создавший урок",
    )
    course: models.ForeignKey = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Курс",
        help_text="Выберите курс, к которому относится урок",
    )
    title: models.CharField = models.CharField(
        max_length=200, verbose_name="Название урока", help_text="Укажите название урока"
    )
    description: models.TextField = models.TextField(
        verbose_name="Описание урока", help_text="Подробное описание урока"
    )
    preview: models.ImageField = models.ImageField(
        upload_to="lessons/previews/",
        blank=True,
        null=True,
        verbose_name="Превью урока",
        help_text="Загрузите изображение для превью урока",
    )
    video_url: models.URLField = models.URLField(
        max_length=500,
        verbose_name="Ссылка на видео",
        help_text="Укажите ссылку на видео урока (YouTube, Vimeo и т.д.)",
    )

    class Meta:  # type: ignore[misc]
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ["course", "id"]

    def __str__(self) -> str:
        """Строковое представление урока."""
        return self.title


class Subscription(BaseModel):
    """
    Модель подписки на курс.

    Подписка связывает пользователя с курсом, на обновления которого
    он подписан. Один пользователь может иметь только одну подписку
    на конкретный курс.
    """

    user: models.ForeignKey = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="Пользователь",
        help_text="Пользователь, подписанный на курс",
    )
    course: models.ForeignKey = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="subscribers",
        verbose_name="Курс",
        help_text="Курс, на который подписан пользователь",
    )

    class Meta:  # type: ignore[misc]
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ("user", "course")
        indexes = [
            models.Index(fields=["user", "course"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        """Строковое представление подписки."""
        return f"{self.user} подписан на {self.course}"
