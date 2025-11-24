# Руководство разработчика

Документация по требованиям к коду, тестированию и workflow разработки проекта.

## 📋 Содержание

1. [TDD Workflow (Test-Driven Development)](#tdd-workflow-test-driven-development)
2. [Требования к коду](#требования-к-коду)
3. [Требования к тестам](#требования-к-тестам)
4. [Инструменты качества кода](#инструменты-качества-кода)
5. [Валидация данных](#валидация-данных)
6. [Workflow разработки](#workflow-разработки)
7. [Архитектурные Best Practices](#архитектурные-best-practices)
8. [Примеры использования](#примеры-использования)
9. [Known Issues & Solutions](#known-issues--solutions)

---

## TDD Workflow (Test-Driven Development)

### ⚠️ ОБЯЗАТЕЛЬНЫЙ порядок разработки

**В этом проекте мы следуем строгому TDD подходу!**

#### Цикл RED-GREEN-REFACTOR

```
1. 🔴 RED: Пишем тест (он падает - функционала еще нет)
         ↓
2. 🟢 GREEN: Пишем минимальный код, чтобы тест прошел
         ↓
3. 🔵 REFACTOR: Улучшаем код, тесты остаются зелеными
         ↓
    Повторяем для следующей функции
```

#### Золотое правило

**НЕТ КОДА БЕЗ ТЕСТОВ!**

Любой функциональный код должен быть покрыт тестами **ДО** или **ОДНОВРЕМЕННО** с его написанием.

#### Порядок разработки модулей

**1. Core (apps/core/)** - Фундамент системы
```bash
# Пример: Разработка BaseModel
pytest tests/core/test_models.py::test_base_model_soft_delete  # RED
# → Пишем метод soft_delete() в BaseModel
pytest tests/core/test_models.py::test_base_model_soft_delete  # GREEN
# → Рефакторим если нужно
```

Порядок:
- ✅ BaseModel → тесты → реализация
- ✅ OwnedModel → тесты → реализация
- ✅ BaseService → тесты → реализация
- ✅ Mixins → тесты → реализация
- ✅ Permissions → тесты → реализация
- ✅ Validators → тесты → реализация

**2. Users (apps/users/)** - Управление пользователями
```bash
# Пример: Разработка User модели
pytest tests/users/test_models.py::test_user_creation  # RED
# → Создаем User модель
pytest tests/users/test_models.py::test_user_creation  # GREEN
```

**3. Mailings (apps/mailings/)** - Бизнес-логика рассылок
```bash
# Аналогично для Recipient, Message, Mailing, Attempt
pytest tests/mailings/test_models.py::test_recipient_creation  # RED → GREEN
```

#### Пример TDD сессии

```bash
# 1. Пишем тест
$ cat > tests/core/test_models.py
@pytest.mark.django_db
def test_base_model_has_created_at():
    obj = SomeModel.objects.create(name="Test")
    assert obj.created_at is not None
    assert isinstance(obj.created_at, datetime)

# 2. Запускаем - должен упасть (RED)
$ pytest tests/core/test_models.py::test_base_model_has_created_at
FAILED - AttributeError: 'SomeModel' object has no attribute 'created_at'

# 3. Добавляем поле в BaseModel
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

# 4. Запускаем - должен пройти (GREEN)
$ pytest tests/core/test_models.py::test_base_model_has_created_at
PASSED

# 5. Рефакторим если нужно, тесты продолжают проходить
```

#### Проверка покрытия

После каждого модуля проверяем 100% покрытие:

```bash
# Проверка покрытия core
pytest --cov=apps/core --cov-report=term-missing tests/core/

# Должно быть 100%
apps/core/models.py      100%
apps/core/services.py    100%
apps/core/mixins.py      100%
...
```

#### Что делать если тест не падает сразу?

Если написали тест и он сразу зеленый - **возможно что-то не так!**

- Проверьте, что тестируете новую функциональность
- Убедитесь, что тест действительно проверяет нужное поведение
- Попробуйте специально сломать код - тест должен упасть

---

## Требования к коду

### 1. Структура проекта

```
project_root/
├── apps/                   # Все Django приложения
│   ├── core/              # ЯДРО - неизменяемая основа
│   │   ├── models.py      # BaseModel, OwnedModel
│   │   ├── services.py    # BaseService, BaseCRUDService
│   │   ├── mixins.py      # Переиспользуемые миксины
│   │   ├── permissions.py # Проверка прав доступа
│   │   └── validators.py  # Pydantic валидаторы
│   ├── users/             # Управление пользователями
│   └── mailings/          # Управление рассылками
├── config/                # Настройки Django
├── tests/                 # Все тесты
└── static/                # Статические файлы
```

### 2. Принципы архитектуры

#### ABC классы (Abstract Base Classes)

**ОБЯЗАТЕЛЬНО**: Абстрактные классы НЕ должны содержать реализации!

```python
# ✅ ПРАВИЛЬНО - чистая абстракция
class BaseService(ABC):
    @abstractmethod
    def validate(self, data: dict[str, Any]) -> bool:
        pass

# ❌ НЕПРАВИЛЬНО - содержит реализацию
class BaseService(ABC):
    def __init__(self):
        self.errors = []  # Это реализация!
```

**Решение**: Разделяем на абстракцию и реализацию

```python
class BaseService(ABC):
    """Чистая абстракция"""
    @abstractmethod
    def validate(self, data: dict[str, Any]) -> bool:
        pass

class BaseServiceWithErrors(BaseService):
    """Реализация с обработкой ошибок"""
    def __init__(self):
        self.errors = []
```

#### Композиция вместо наследования

**Используем миксины** для переиспользования кода:

```python
class RecipientService(BaseCRUDService, OwnerFilterMixin, LoggingMixin):
    def __init__(self):
        super().__init__(Recipient)
```

#### Dependency Injection

Сервисы получают зависимости через `__init__`:

```python
class MailingService:
    def __init__(self, email_sender: EmailSender, logger: Logger):
        self.email_sender = email_sender
        self.logger = logger
```

### 3. Типизация кода

#### ⚠️ ОБЯЗАТЕЛЬНОЕ требование: 100% Type Coverage

**Проект ОБЯЗАН поддерживать 100% покрытие типами с нулевыми ошибками mypy!**

```bash
# Проверка типизации (должна показывать 0 ошибок)
poetry run mypy .
# Expected output: Success: no issues found in 51 source files
```

#### Явная типизация всех полей моделей Django

**ОБЯЗАТЕЛЬНО**: Все поля Django моделей должны иметь явные type annotations:

```python
# ✅ ПРАВИЛЬНО - явная типизация
class User(AbstractUser, BaseModel):
    email: models.EmailField = models.EmailField(
        verbose_name="Email адрес",
        unique=True
    )
    
    avatar: models.ImageField = models.ImageField(
        upload_to="users/avatars/%Y/%m/%d/",
        blank=True,
        null=True
    )
    
    phone: models.CharField = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

# ❌ НЕПРАВИЛЬНО - нет типизации
class User(AbstractUser, BaseModel):
    email = models.EmailField(verbose_name="Email адрес")  # Нет аннотации!
    avatar = models.ImageField(upload_to="...")  # Нет аннотации!
```

#### Generic Service Pattern

**ОБЯЗАТЕЛЬНО**: Сервисы должны использовать Generic[T] для правильного вывода типов:

```python
from typing import Generic, TypeVar, Optional
from django.db.models import Model, QuerySet

T = TypeVar("T", bound=Model)

# ✅ ПРАВИЛЬНО - Generic pattern
class BaseCRUDService(Generic[T]):
    """Базовый CRUD сервис с Generic типизацией"""
    
    def __init__(self, model_class: type[T]) -> None:
        self.model_class = model_class
    
    def get_by_id(self, pk: int) -> Optional[T]:
        """Возвращает конкретный тип модели, не Model"""
        return self.model_class.objects.filter(pk=pk).first()
    
    def get_all(self) -> QuerySet[T]:
        """Возвращает типизированный QuerySet"""
        return self.model_class.objects.all()

# Использование в конкретных сервисах
class RecipientService(BaseCRUDService[Recipient]):
    def __init__(self):
        super().__init__(Recipient)
    
    # Методы автоматически возвращают Recipient, не Model!
```

#### Целевые type: ignore директивы

**Используйте только целевые type: ignore** для реальных ограничений Django:

```python
# ✅ ПРАВИЛЬНО - целевой ignore для Django ORM
class RecipientForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipients"].queryset = (  # type: ignore[attr-defined]
            Recipient.objects.filter(owner=user, is_active=True)
        )

# ✅ ПРАВИЛЬНО - целевой ignore для custom user методов
if not self.request.user.is_manager():  # type: ignore[union-attr]
    queryset = queryset.filter(owner=self.request.user)

# ✅ ПРАВИЛЬНО - целевой ignore для override Django методов
class UserManager(DjangoUserManager):
    def create_user(
        self, 
        email: str, 
        password: Optional[str] = None, 
        **extra_fields: Any
    ) -> "User":  # type: ignore[override]
        pass

# ❌ НЕПРАВИЛЬНО - слишком широкий ignore
def some_function():  # type: ignore
    pass  # Игнорирует ВСЕ типы ошибок!

# ❌ НЕПРАВИЛЬНО - множественные ignore без необходимости
def create_user(...) -> "User":  # type: ignore[name-defined,override]
    # Должен быть только override, а name-defined решается через TYPE_CHECKING
    pass
```

#### TYPE_CHECKING для forward references

**Используйте TYPE_CHECKING** для разрешения circular imports:

```python
from typing import TYPE_CHECKING, Any, Optional
from django.contrib.auth.models import UserManager as DjangoUserManager

# ✅ ПРАВИЛЬНО - импорт только для type checking
if TYPE_CHECKING:
    from apps.users.models import User

class UserManager(DjangoUserManager):
    def create_user(
        self, 
        email: str, 
        password: Optional[str] = None,
        **extra_fields: Any
    ) -> "User":  # type: ignore[override]
        """User в кавычках - forward reference"""
        pass

# ❌ НЕПРАВИЛЬНО - реальный импорт вызовет circular import
from apps.users.models import User  # Ошибка!
```

#### Категории type: ignore директив

Используйте только следующие категории:

| Директива | Когда использовать | Пример |
|-----------|-------------------|---------|
| `[override]` | Django метод с другой сигнатурой | UserManager.create_user() |
| `[attr-defined]` | Django ORM атрибуты | queryset, owner_id, input_formats |
| `[union-attr]` | Custom методы на request.user | is_manager(), is_active |
| `[no-any-return]` | self.model возвращает Any | return user (в Manager) |
| `[assignment]` | reverse_lazy() возвращает _StrPromise | next_page = str(reverse_lazy(...)) |

#### Проверка типизации

**Запускайте mypy регулярно:**

```bash
# Полная проверка проекта
poetry run mypy .

# Проверка конкретного модуля
poetry run mypy apps/core/

# Проверка с подробным выводом
poetry run mypy --show-error-codes apps/

# Должен быть результат:
# Success: no issues found in 51 source files
```

#### Интеграция в CI/CD

```bash
# В pipeline добавьте проверку mypy ПЕРЕД тестами
poetry run mypy .
if [ $? -ne 0 ]; then
    echo "❌ Mypy проверка провалена! Исправьте ошибки типов."
    exit 1
fi

poetry run pytest
```

#### Важно помнить

- ❌ **НЕТ ошибок mypy = НЕТ merge!**
- ✅ Все поля моделей должны быть типизированы
- ✅ Generic[T] pattern для всех базовых сервисов
- ✅ Только целевые type: ignore директивы
- ✅ TYPE_CHECKING для forward references
- ✅ Документируйте причину каждого type: ignore

---

### 4. Неиспользуемые параметры

#### ⚠️ ОБЯЗАТЕЛЬНОЕ требование: Префикс подчеркивания

**Если параметры `*args` или `**kwargs` не используются в методе, они ОБЯЗАНЫ начинаться с подчеркивания: `*_args`, `**_kwargs`.**

Это явно показывает что параметры объявлены для совместимости с интерфейсом, но не используются в реализации.

#### Примеры правильного использования:

```python
# ✅ ПРАВИЛЬНО - args не используется, поэтому _args
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *_args, **options) -> None:
        """Обработка команды."""
        force = options["force"]  # Используем только options
        # args здесь не используется
        ...

# ✅ ПРАВИЛЬНО - args и kwargs не используются, поэтому _args и _kwargs
from rest_framework.views import APIView

class SubscriptionAPIView(APIView):
    def post(self, request: Request, *_args: Any, **_kwargs: Any) -> Response:
        """Toggle подписки на курс."""
        user = request.user  # Используем только request
        # args и kwargs здесь не используются
        ...

# ✅ ПРАВИЛЬНО - args используется, поэтому без подчеркивания
class SomeClass:
    def method(self, *args, **kwargs):
        """Метод использующий args."""
        for arg in args:  # args используется!
            print(arg)
        return kwargs
```

#### Примеры неправильного использования:

```python
# ❌ НЕПРАВИЛЬНО - args объявлен но не используется
class Command(BaseCommand):
    def handle(self, *args, **options) -> None:
        force = options["force"]
        # args нигде не используется!

# ❌ НЕПРАВИЛЬНО - kwargs объявлен но не используется
class SomeView(APIView):
    def post(self, request: Request, *args, **kwargs) -> Response:
        data = request.data
        # args и kwargs нигде не используются!
```

#### Когда применять:

- ✅ Django management команды: `handle(self, *_args, **options)`
- ✅ DRF APIView методы: `post(request, *_args, **_kwargs)`
- ✅ Сигналы Django: `signal_handler(sender, *_args, **_kwargs)`
- ✅ Любые методы где параметр нужен для совместимости с интерфейсом

#### Проверка:

**Ruff/Pylint автоматически предупредит** об неиспользуемых параметрах:

```bash
poetry run ruff check .
# ARG002 Unused method argument: `args`
```

---

### 5. Статические методы (@staticmethod)

#### ⚠️ ОБЯЗАТЕЛЬНОЕ требование: Явные static методы

**Если метод класса НЕ использует `self`, он ОБЯЗАН быть помечен декоратором `@staticmethod`.**

Это явно показывает что метод не зависит от состояния экземпляра класса.

#### Когда делать staticmethod:

```python
# ✅ ПРАВИЛЬНО - helper метод не использует self
class PaymentProcessor:
    @staticmethod
    def validate_card_number(card: str) -> bool:
        """Валидация номера карты."""
        # Работает только с параметрами, self не нужен
        return len(card) == 16 and card.isdigit()
    
    def process_payment(self, amount: Decimal) -> bool:
        """Обработка платежа."""
        # Использует self.config, self.api_key и т.д.
        card = self.get_card_number()
        if not self.validate_card_number(card):  # Вызов static метода
            return False
        ...

# ✅ ПРАВИЛЬНО - utility функция в классе
class StringUtils:
    @staticmethod
    def slugify(text: str) -> str:
        """Преобразование текста в slug."""
        return text.lower().replace(" ", "-")
```

#### Когда НЕ делать staticmethod:

```python
# ❌ НЕ делать staticmethod - это часть Django/DRF интерфейса
class UserSerializer(serializers.ModelSerializer):
    def validate(self, attrs: dict) -> dict:
        """Валидация данных."""
        # Метод НЕ использует self, но это часть DRF интерфейса!
        # НЕ НАДО делать @staticmethod
        return attrs
    
    def create(self, validated_data: dict) -> User:
        """Создание пользователя."""
        # Метод НЕ использует self напрямую, но это часть DRF интерфейса!
        # НЕ НАДО делать @staticmethod
        return User.objects.create(**validated_data)

# ❌ НЕ делать staticmethod - использует self косвенно
class CourseViewSet(viewsets.ModelViewSet):
    def get_permissions(self) -> list:
        """Получение списка permissions."""
        # Использует self.action (косвенно через Django machinery)
        # НЕ НАДО делать @staticmethod
        if self.action == "create":
            return [IsAuthenticated()]
        return [IsOwner()]

# ❌ НЕ делать staticmethod - Django management команда
class Command(BaseCommand):
    def _create_user(self) -> User:
        """Создание пользователя."""
        # Использует self.stdout.write()
        # НЕ НАДО делать @staticmethod
        self.stdout.write("Creating user...")
        return User.objects.create(...)
```

#### Исключения из правила:

**НЕ делайте staticmethod для:**

| Тип метода | Причина | Пример |
|-----------|---------|--------|
| Django/DRF интерфейсы | Переопределение базового класса | `validate()`, `create()`, `update()` |
| Методы использующие self косвенно | Django machinery автоматически передает self | `get_permissions()`, `get_queryset()` |
| Magic методы | Часть Python протокола | `__init__()`, `__str__()`, `__repr__()` |
| Методы с self.stdout, self.context | Используют атрибуты экземпляра | Management команды, DRF serializers |

#### Проверка:

**Mypy/Pylint предупредит** если метод может быть статическим:

```bash
poetry run mypy .
# note: Consider using @staticmethod for 'validate_card_number'
```

#### Преимущества staticmethod:

- ✅ Явно показывает что метод не зависит от состояния класса
- ✅ Можно вызывать без создания экземпляра: `PaymentProcessor.validate_card_number(card)`
- ✅ Улучшает читаемость и понимание кода
- ✅ Помогает в рефакторинге и тестировании

---

### 6. Язык документации и комментариев

#### ⚠️ ОБЯЗАТЕЛЬНОЕ требование: Русский язык

**Весь проект ОБЯЗАН использовать русский язык для документации и комментариев!**

Это критически важно для:
- Единообразия кодовой базы
- Удобства чтения и поддержки
- Снижения порога входа для русскоязычных разработчиков

#### Что должно быть на русском:

```python
# ✅ ПРАВИЛЬНО - docstrings на русском
class Course(BaseModel):
    """
    Модель курса.
    
    Курс содержит название, описание и опциональное превью изображение.
    К курсу привязываются уроки через ForeignKey.
    """
    pass

def create_user(email: str, password: str) -> User:
    """
    Создать нового пользователя.
    
    Args:
        email: Email адрес пользователя
        password: Пароль пользователя
        
    Returns:
        User: Созданный объект пользователя
        
    Raises:
        ValidationError: Если email невалидный
    """
    pass

# ✅ ПРАВИЛЬНО - комментарии на русском
# Проверяем что пользователь активен
if user.is_active:
    # Отправляем уведомление
    send_notification(user)

# ❌ НЕПРАВИЛЬНО - docstrings на английском
class Course(BaseModel):
    """
    Course model.
    
    Course contains title, description and optional preview image.
    """
    pass

# ❌ НЕПРАВИЛЬНО - комментарии на английском
# Check if user is active
if user.is_active:
    pass
```

#### Исключения:

Только следующие элементы могут быть на английском:
- Названия переменных, функций, классов (camelCase/snake_case)
- Названия полей в базе данных
- URL пути и routing
- Технические константы и enum значения

```python
# ✅ ПРАВИЛЬНО - код на английском, документация на русском
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для управления пользователями."""
    
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    
    def create(self, request):
        """Создать нового пользователя через API."""
        pass
```

#### Проверка:

Перед коммитом проверьте:
- ✅ Все docstrings на русском
- ✅ Все комментарии на русском  
- ✅ Конфигурационные файлы (urls.py, wsgi.py, asgi.py) на русском
- ✅ README.md и документация на русском

---

### 5. Отсутствие дублирования (DRY)

- Используем миксины для общего функционала
- Создаем базовые классы для похожих сущностей
- Функции должны делать одну вещь хорошо

### 6. Качество кода

#### flake8

Код **ОБЯЗАТЕЛЬНО** должен проходить проверку flake8 без ошибок:

```bash
poetry run flake8 apps/ config/
```

#### Документация

Все классы, методы и функции **ОБЯЗАТЕЛЬНО** должны быть задокументированы на русском языке:

```python
def create_recipient(email: str, name: str) -> Recipient:
    """
    Создать нового получателя рассылки.
    
    Args:
        email: Email адрес получателя
        name: Полное имя получателя
        
    Returns:
        Созданный объект Recipient
        
    Raises:
        ValidationError: Если email невалидный
    """
    pass
```

---

## Требования к тестам

### 1. Фреймворк

**Используем pytest-django** вместо Django unittest:

```bash
# Запуск тестов
pytest

# Параллельное выполнение (быстрее)
pytest -n auto

# С покрытием кода
pytest --cov=apps --cov-report=html

# С переиспользованием БД (еще быстрее)
pytest --reuse-db -n auto
```

### 2. Стратегия тестирования

**Порядок приоритета** (от ядра к приложениям):

1. **apps/core/** - тесты ядра (100% покрытие)
   - BaseModel, OwnedModel
   - BaseService, BaseCRUDService
   - Миксины (OwnerFilterMixin, LoggingMixin, CacheMixin)
   - Permissions

2. **apps/users/** - тесты users (100% покрытие)
   - Модель User
   - UserService
   - Формы, views

3. **apps/mailings/** - тесты mailings (100% покрытие)
   - Модели (Recipient, Message, Mailing, Attempt)
   - Сервисы
   - Команды management
   - Формы, views

4. **Интеграционные тесты**
   - Полный цикл рассылки
   - Проверка прав доступа (User vs Manager)

### 3. Принципы тестирования

#### Изоляция тестов

Каждый тест независим и не влияет на другие:

```python
@pytest.mark.django_db
def test_create_recipient():
    # Arrange
    data = {"email": "test@example.com", "full_name": "Test User"}
    
    # Act
    recipient = Recipient.objects.create(**data)
    
    # Assert
    assert recipient.email == "test@example.com"
    # БД автоматически откатывается после теста
```

#### Нет дублей в покрытии

Тесты не должны покрывать код более одного раза:

```python
# ✅ ПРАВИЛЬНО - тестируем BaseModel один раз
def test_base_model_soft_delete():
    obj = SomeModel.objects.create(name="Test")
    obj.soft_delete()
    assert obj.is_active == False

# ❌ НЕПРАВИЛЬНО - повторное тестирование того же функционала
def test_recipient_soft_delete():
    recipient = Recipient.objects.create(...)
    recipient.soft_delete()  # Уже протестировано в BaseModel!
```

#### Моки для внешних сервисов

**ОБЯЗАТЕЛЬНО** мокировать:
- `send_mail()` - не отправляем реальные письма
- Внешние API
- Файловую систему (где возможно)

```python
@pytest.mark.django_db
def test_send_mailing(mocker):
    # Мокируем отправку email
    mock_send = mocker.patch('django.core.mail.send_mail')
    
    # Отправляем рассылку
    send_mailing(mailing_id=1)
    
    # Проверяем что send_mail был вызван
    assert mock_send.called
```

#### Параметризация тестов

Используем `@pytest.mark.parametrize` для тестирования множества сценариев:

```python
@pytest.mark.parametrize("email,valid", [
    ("test@example.com", True),
    ("invalid", False),
    ("@example.com", False),
    ("test@", False),
])
def test_email_validation(email, valid):
    result = validate_email(email)
    assert result == valid
```

#### Фикстуры для переиспользования

```python
@pytest.fixture
def user():
    return User.objects.create_user(
        email="user@example.com",
        password="password123"
    )

@pytest.fixture
def manager():
    user = User.objects.create_user(
        email="manager@example.com",
        password="password123"
    )
    user.is_staff = True
    user.save()
    return user

def test_user_permissions(user, manager):
    # Используем фикстуры
    pass
```

### 4. Структура тестов

```
tests/
├── core/
│   ├── test_models.py        # Тесты BaseModel, OwnedModel
│   ├── test_services.py      # Тесты BaseService, BaseCRUDService
│   ├── test_mixins.py        # Тесты миксинов
│   └── test_permissions.py   # Тесты прав доступа
├── users/
│   ├── test_models.py        # Тесты User модели
│   ├── test_services.py      # Тесты UserService
│   └── test_views.py         # Тесты views
├── mailings/
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_views.py
│   └── test_commands.py      # Тесты management команд
└── integration/
    └── test_mailing_flow.py  # Интеграционные тесты
```

### 5. Целевое покрытие

**100% покрытие функционального кода** без избыточных проверок!

```bash
# Проверка покрытия
pytest --cov=apps --cov-report=term-missing

# HTML отчет
pytest --cov=apps --cov-report=html
# Открыть htmlcov/index.html
```

---

## Инструменты качества кода

### 1. Установленные инструменты

- **flake8** - проверка стиля кода
- **black** - автоформатирование
- **isort** - сортировка импортов
- **pre-commit** - автоматические проверки перед коммитом

### 1. Установленные инструменты

⚠️ **ВАЖНО: Порядок проверки линтерами**

Линтеры должны выполняться **СТРОГО** в следующем порядке:

1. **ruff** - ПЕРВЫЙ! Быстрая проверка на баги и стиль (новый стандарт)
2. **mypy** - проверка типизации (100% type coverage)
3. **black** - автоформатирование кода
4. **isort** - сортировка импортов
5. **flake8** - дополнительные проверки стиля

**Инструменты:**
- **ruff** - современная быстрая замена flake8/pylint
- **mypy** - проверка типов
- **black** - автоформатирование
- **isort** - сортировка импортов
- **flake8** - дополнительные проверки
- **pre-commit** - автоматические проверки перед коммитом
- **pytest-django** - тестирование
- **pytest-cov** - покрытие кода

### 2. Конфигурационные файлы

#### `pyproject.toml`

Настройки ruff, black, isort, mypy, pytest:

```toml
[tool.ruff]
line-length = 119
preview = true
exclude = [".venv", "migrations", "attached_assets", "scripts", ".pythonlibs", ".local"]
force-exclude = true

[tool.ruff.lint]
select = ["B", "E", "F", "C90", "UP", "SIM"]
fixable = ["ALL"]

[tool.black]
line-length = 119
exclude = '''(^\.pythonlibs|^\.local|/(\.eggs|\.git|\.mypy_cache|migrations|attached_assets|scripts)/)'''

[tool.isort]
line_length = 119
profile = "black"
skip_glob = ["scripts/*", ".pythonlibs/*", ".local/*"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
ignore_missing_imports = true
exclude = ["^scripts/", "^\\.pythonlibs/", "^\\.local/", "^migrations/"]
```

**Исключения из проверок линтеров:**

Следующие папки исключены из проверок всех линтеров (Ruff, Black, isort, Mypy, Flake8):

- **`scripts/`** — служебные утилиты для разработки (`check.py`, `fix.py`, `watch.sh`). Не требуют production-level code quality.
- **`.pythonlibs/`, `.local/`** — системные папки Replit. Автоматически генерируются средой выполнения.
- **`migrations/`** — автогенерируемые Django миграции.
- **`attached_assets/`** — медиа-файлы и статика.

Это обеспечивает быструю работу CI/CD и фокусирует проверки на production коде.

### 3. Команды проверки

```bash
# ⚠️ ОБЯЗАТЕЛЬНЫЙ ПОРЯДОК!

# 1. RUFF - ПЕРВЫЙ!
poetry run ruff check apps/ config/ tests/

# Автоматическое исправление (безопасно)
poetry run ruff check --fix apps/ config/ tests/

# 2. MYPY - проверка типов (100% обязательно!)
poetry run mypy .

# 3. BLACK - автоформатирование
poetry run black apps/ config/ tests/

# 4. ISORT - сортировка импортов
poetry run isort apps/ config/ tests/

# 5. FLAKE8 - дополнительные проверки
poetry run flake8 apps/ config/

# Все проверки одной командой
poetry run ruff check . && \
  poetry run mypy . && \
  poetry run black --check . && \
  poetry run isort --check . && \
  poetry run flake8 apps/ config/

# Тесты
poetry run pytest

# Тесты с покрытием
poetry run pytest --cov=apps --cov-report=html
```

### 4. Pre-commit hooks

Настроить автоматические проверки перед коммитом:

```bash
# Установить pre-commit hooks
poetry run pre-commit install

# Запустить на всех файлах
poetry run pre-commit run --all-files
```

## Серверное кэширование

### Гибкая конфигурация через .env

Проект поддерживает два бэкенда кэширования с автоматическим выбором через переменные окружения:

**locmem (по умолчанию):**
- ✅ Простота: zero setup, работает из коробки
- ✅ Скорость: очень быстрый (всё в памяти процесса)
- ✅ Идеально для development и single-process приложений
- ❌ Кэш НЕ разделяется между воркерами (если запустить `gunicorn -w 4`, каждый процесс имеет свой кэш)
- ❌ Теряется при перезапуске сервера

**redis:**
- ✅ Разделяется между всеми процессами/воркерами
- ✅ Может быть персистентным (переживёт перезапуск)
- ✅ Production-ready решение
- ❌ Требует установки и настройки отдельного сервиса Redis
- ❌ Небольшой network overhead (хотя Redis очень быстрый)

### Переключение бэкендов

```bash
# В .env файле для development (по умолчанию)
CACHE_BACKEND=locmem
CACHE_TIMEOUT=300  # 5 минут

# Для production с несколькими воркерами
CACHE_BACKEND=redis
REDIS_URL=redis://127.0.0.1:6379/1
CACHE_TIMEOUT=600  # 10 минут для production
```

### Использование в коде

CacheMixin обрабатывает кэширование прозрачно - код работает одинаково с любым бэкендом:

```python
from apps.core.mixins import CacheMixin
from apps.core.services import BaseCRUDService
from apps.mailings.models import Recipient

class RecipientService(BaseCRUDService, CacheMixin):
    """Сервис с автоматическим кэшированием"""
    
    def __init__(self):
        super().__init__(Recipient)
    
    def get_all_cached(self, user):
        """Кэш работает автоматически, независимо от бэкенда"""
        cache_key = f"recipients_{user.id}"
        return self._get_or_set_cache(cache_key, lambda: self.get_all())
```

### Когда использовать Redis

Переключайтесь на Redis если:
1. Запускаете приложение с несколькими воркерами (`gunicorn -w 4+`)
2. Нужна персистентность кэша между перезапусками
3. Переходите в production с высокой нагрузкой

### Установка Redis (опционально)

Для использования Redis бэкенда:

```bash
# Пакет redis уже установлен в проекте через Poetry

# Для Windows - установите Redis через WSL или Redis for Windows
# Для Linux/macOS
sudo apt-get install redis-server  # Debian/Ubuntu
brew install redis                  # macOS

# Запустите Redis
redis-server

# Проверьте подключение
redis-cli ping  # Должен ответить "PONG"
```

---

## Валидация данных

### 1. Django Forms (основной инструмент)

**Используйте Django Forms/ModelForms для:**
- Валидации форм пользователя
- Проверки данных моделей
- Автоматической генерации HTML форм
- Обработки GET/POST запросов

#### Пример Django Form

```python
from django import forms
from .models import Recipient

class RecipientForm(forms.ModelForm):
    """Форма создания получателя"""
    
    class Meta:
        model = Recipient
        fields = ['email', 'full_name', 'comment']
    
    def clean_full_name(self):
        """Кастомная валидация имени"""
        full_name = self.cleaned_data.get('full_name')
        if not full_name or not full_name.strip():
            raise forms.ValidationError("Имя не может быть пустым")
        return full_name.strip()

# Использование в view
def create_recipient(request):
    if request.method == 'POST':
        form = RecipientForm(request.POST)
        if form.is_valid():
            recipient = form.save(commit=False)
            recipient.owner = request.user
            recipient.save()
            return redirect('success')
    else:
        form = RecipientForm()
    return render(request, 'form.html', {'form': form})
```

### 2. Pydantic (для сложных случаев)

**Используйте Pydantic, когда Django Forms недостаточно:**
- Сложная кросс-полевая валидация
- Интеграция с внешними API
- Валидация настроек (.env файлов) через pydantic-settings
- Сериализация/десериализация сложных структур данных

#### Пример Pydantic валидатора

```python
from pydantic import BaseModel, field_validator, model_validator

class ComplexValidator(BaseModel):
    """Пример сложной валидации с Pydantic"""
    
    email: str
    password: str
    password_confirm: str
    
    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        """Проверка домена через внешний API"""
        # Ваша сложная логика с внешним API
        if not is_valid_domain(v.split('@')[1]):
            raise ValueError('Недопустимый email домен')
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """Кросс-полевая валидация"""
        if self.password != self.password_confirm:
            raise ValueError('Пароли не совпадают')
        return self

# Использование
try:
    validator = ComplexValidator(**data)
    validated_data = validator.model_dump()
except ValidationError as e:
    errors = e.errors()
```

### 3. Когда что использовать?

| Задача | Инструмент | Причина |
|--------|-----------|---------|
| Формы пользователя | Django Forms | Встроенная интеграция с Django |
| CRUD операции | ModelForms | Автоматическая связь с моделями |
| Валидация .env | Pydantic Settings | Специализированный инструмент |
| Сложная бизнес-логика | Pydantic | Мощные возможности валидации |
| API запросы/ответы | Django Forms или Pydantic | В зависимости от сложности |

---

## Архитектурные Best Practices

### Динамическое отображение API endpoints

**Проблема:** При статической регистрации endpoints на главной странице API (`/api/`) приходится вручную обновлять список при добавлении новых ViewSet-ов.

**Решение:** Динамический сбор endpoints из роутеров всех приложений.

#### Принцип работы

```python
# config/views.py
@api_view(["GET"])
def api_root(request: Request, response_format: str | None = None) -> Response:
    """
    Корневой эндпоинт API со списком всех доступных ресурсов.
    Динамически собирает все endpoints из роутеров приложений.
    """
    from lms.urls import router as lms_router
    from users.urls import router as users_router

    endpoints: dict[str, str] = {}

    # Автоматически собираем endpoints из роутера LMS приложения
    for _, _, basename in lms_router.registry:
        endpoints[basename] = reverse(f"lms:{basename}-list", request=request, format=response_format)

    # Автоматически собираем endpoints из роутера Users приложения
    for _, _, basename in users_router.registry:
        endpoints[basename] = reverse(f"users:{basename}-list", request=request, format=response_format)

    # Generic Views добавляем вручную (если не используют роутер)
    endpoints["lesson"] = reverse("lms:lesson-list", request=request, format=response_format)

    return Response(endpoints)
```

#### Преимущества

✅ **Автоматизация** - новые ViewSet-ы появляются на главной странице API автоматически  
✅ **Масштабируемость** - легко добавлять новые приложения  
✅ **DRY принцип** - нет дублирования списка endpoints  
✅ **Меньше ошибок** - невозможно забыть добавить endpoint вручную

#### Использование в router.registry

`router.registry` возвращает список кортежей: `(prefix, viewset, basename)`

```python
# Пример содержимого router.registry
[
    ('users', UserViewSet, 'user'),
    ('payments', PaymentViewSet, 'payment'),
    ('courses', CourseViewSet, 'course'),
]
```

Используем распаковку с `_` для неиспользуемых переменных:
```python
for _, _, basename in router.registry:
    # Используем только basename
    endpoints[basename] = reverse(f"app:{basename}-list", ...)
```

#### Когда применять

- ✅ Проекты с несколькими приложениями
- ✅ API с частым добавлением новых ресурсов
- ✅ Когда важна автоматическая документация API
- ❌ Не нужно для очень простых API с 1-2 endpoints

---

### Оптимизация запросов к базе данных

**Проблема N+1:** При загрузке связанных объектов Django ORM по умолчанию выполняет отдельный запрос для каждого связанного объекта, что приводит к огромному количеству запросов к БД.

**Пример проблемы:**
```python
# ❌ Плохо: N+1 запросов
courses = Course.objects.all()  # 1 запрос для курсов
for course in courses:
    print(course.lesson_set.all())  # N запросов для уроков каждого курса!
# Итого: 1 + N запросов (например, 1 + 10 = 11 запросов для 10 курсов)
```

**Решение:** Используйте `select_related()` и `prefetch_related()` для предзагрузки связанных объектов.

#### Когда что использовать

| Ситуация | Метод | Как работает |
|----------|-------|--------------|
| **ForeignKey, OneToOneField** | `select_related()` | SQL JOIN - одним запросом |
| **ManyToManyField** | `prefetch_related()` | Два запроса: основной + связанные |
| **Обратные связи (model_set)** | `prefetch_related()` | Два запроса: основной + связанные |
| **Глубокие связи** | `Prefetch()` с вложенными | Комбинация методов |

#### Примеры оптимизации

**1. select_related() для ForeignKey:**

```python
# ❌ Плохо: N+1 запросов
lessons = Lesson.objects.all()  # 1 запрос
for lesson in lessons:
    print(lesson.course.title)  # N запросов для каждого курса!

# ✅ Хорошо: 1 запрос с JOIN
lessons = Lesson.objects.select_related('course')
for lesson in lessons:
    print(lesson.course.title)  # Курс уже загружен!
```

**2. prefetch_related() для обратных связей:**

```python
# ❌ Плохо: N+1 запросов
courses = Course.objects.all()  # 1 запрос
for course in courses:
    print(course.lesson_set.all())  # N запросов!

# ✅ Хорошо: 2 запроса (курсы + все уроки сразу)
courses = Course.objects.prefetch_related('lesson_set')
for course in courses:
    print(course.lesson_set.all())  # Уроки уже загружены!
```

**3. Комбинация методов:**

```python
# Платежи с пользователем, курсом и уроком
payments = Payment.objects.select_related('user', 'course', 'lesson')
# 1 запрос с тремя JOIN вместо 1 + 3N запросов!
```

**4. Глубокие prefetch с вложенными запросами:**

```python
from django.db.models import Prefetch

# Загружаем мотоциклы с пробегами и авторами пробегов
motos = Moto.objects.prefetch_related(
    Prefetch(
        'milage_set',
        queryset=Milage.objects.select_related('created_by')
    )
).all()

# Для нашего проекта: курсы с уроками и данными авторов уроков
courses = Course.objects.prefetch_related(
    Prefetch(
        'lesson_set',
        queryset=Lesson.objects.select_related('course')
    )
)
```

#### Применение в ViewSet

**Всегда** добавляйте оптимизацию запросов в `queryset` ViewSet'ов и Generic Views:

```python
class CourseViewSet(viewsets.ModelViewSet):
    """
    Оптимизация: prefetch_related('lesson_set') предзагружает все уроки
    одним запросом, устраняя проблему N+1 при отображении списка курсов.
    """
    queryset = Course.objects.prefetch_related("lesson_set")
    serializer_class = CourseSerializer


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Оптимизация: select_related('course') загружает связанный курс
    одним JOIN запросом вместо отдельного запроса для каждого урока.
    """
    queryset = Lesson.objects.select_related("course")
    serializer_class = LessonSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """
    Оптимизация: select_related('user', 'course', 'lesson') предзагружает
    все связанные объекты одним запросом, устраняя проблему N+1.
    """
    queryset = Payment.objects.select_related("user", "course", "lesson")
    serializer_class = PaymentSerializer
```

#### Проверка количества запросов

**Способ 1: Django Debug Toolbar** (для development)

```python
# settings.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

**Способ 2: connection.queries** (в коде)

```python
from django.db import connection
from django.test.utils import override_settings

@override_settings(DEBUG=True)
def test_queries():
    courses = Course.objects.prefetch_related('lesson_set')
    list(courses)  # Триггерим выполнение запроса
    
    print(f"Количество запросов: {len(connection.queries)}")
    for query in connection.queries:
        print(query['sql'])
```

#### Правила оптимизации

✅ **Всегда используйте** `select_related()`/`prefetch_related()` для связей, которые будут использоваться  
✅ **Проверяйте** количество запросов во время разработки  
✅ **Добавляйте оптимизацию** при создании ViewSet, а не потом  
❌ **Не оптимизируйте** связи, которые не используются (лишняя нагрузка на БД)

---

### Service Layer для внешних интеграций

**Принцип:** Для интеграций с внешними API (Stripe, SendGrid, Twilio) используйте простые функции в отдельных модулях `services.py`, а не классы.

**Почему функции, а не классы?**

Для простых API интеграций (без сложного состояния) функции имеют ряд преимуществ:

✅ **Простота** - нет boilerplate кода (инициализация, self, __init__)  
✅ **Нет состояния** - каждая операция независима, легче тестировать  
✅ **Читаемость** - имя функции сразу говорит что она делает  
✅ **Простое тестирование** - минимум setup, просто моки параметров

#### Когда использовать функции

✅ API без состояния между вызовами (Stripe, SendGrid, Twilio)  
✅ Простые операции: создать, получить, проверить статус  
✅ Нет необходимости в конфигурации для каждого вызова  
✅ Нет наследования или полиморфизма

**Пример с функциями (правильно):**

```python
# users/services.py
def create_stripe_product_and_price(name: str, amount: Decimal) -> tuple[str, str]:
    """
    Создает продукт и цену в Stripe.
    
    Args:
        name: Название продукта
        amount: Сумма в рублях
    
    Returns:
        tuple: (product_id, price_id)
    """
    amount_in_cents = int(amount * 100)
    product = stripe.Product.create(name=name)
    price = stripe.Price.create(
        product=product.id,
        unit_amount=amount_in_cents,
        currency="rub",
    )
    return product.id, price.id

# Использование во ViewSet
class PaymentViewSet(viewsets.ModelViewSet):
    def create(self, request):
        product_id, price_id = create_stripe_product_and_price(
            name="Курс Python",
            amount=Decimal("2500.00")
        )
```

**Пример с классами (излишняя сложность):**

```python
# ❌ Не делайте так для простых API
class StripeService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.stripe = stripe
        self.stripe.api_key = api_key
    
    def create_product(self, name: str, amount: Decimal) -> tuple[str, str]:
        # Та же логика, но с лишним boilerplate
        ...

# Использование требует создания экземпляра
service = StripeService(settings.STRIPE_SECRET_KEY)
product_id, price_id = service.create_product("Курс Python", Decimal("2500.00"))
```

#### Когда использовать классы

Классы имеют смысл в следующих случаях:

✅ **Сложное состояние** - если нужно хранить настройки между вызовами  
✅ **Много конфигурации** - если куча параметров повторяется  
✅ **Наследование** - разные типы провайдеров (Stripe, PayPal, Yandex.Kassa)  
✅ **Полиморфизм** - нужна общая абстракция для разных реализаций

**Пример, когда класс оправдан:**

```python
# Абстракция для разных платежных провайдеров
class PaymentGateway(ABC):
    @abstractmethod
    def create_payment(self, amount: Decimal) -> str:
        pass

class StripeGateway(PaymentGateway):
    def __init__(self, api_key: str, currency: str = "rub"):
        self.api_key = api_key
        self.currency = currency
    
    def create_payment(self, amount: Decimal) -> str:
        # Использует self.currency
        ...

class PayPalGateway(PaymentGateway):
    def create_payment(self, amount: Decimal) -> str:
        ...

# Использование
gateway = StripeGateway(api_key=settings.STRIPE_KEY, currency="rub")
payment_id = gateway.create_payment(Decimal("2500.00"))
```

#### Структура services.py

**Рекомендуемая структура:**

```python
# users/services.py
"""
Сервисные функции для работы с платежами и внешними платежными системами.

Этот модуль содержит функции для интеграции с Stripe API:
- Создание продуктов и цен в Stripe
- Создание платежных сессий
- Проверка статуса платежей
"""

import stripe
from decimal import Decimal
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product_and_price(name: str, amount: Decimal) -> tuple[str, str]:
    """Создает продукт и цену в Stripe."""
    ...


def create_stripe_checkout_session(
    price_id: str, 
    success_url: str, 
    cancel_url: str
) -> tuple[str, str]:
    """Создает платежную сессию Stripe Checkout."""
    ...


def check_stripe_payment_status(session_id: str) -> str:
    """Проверяет статус платежа в Stripe."""
    ...
```

#### Best Practices

✅ **Type hints везде** - полная типизация функций для безопасности  
✅ **Docstrings на русском** - документируй назначение, параметры, возвращаемое значение  
✅ **Proper error handling** - обрабатывай исключения API корректно  
✅ **Один модуль = одна интеграция** - `stripe_services.py`, `sendgrid_services.py`  
✅ **Тестируй с моками** - не зависи от реального API в тестах

#### Референс-документация

Полная документация по профессиональной реализации Stripe интеграции доступна в:

📄 **[docs/STRIPE_INTEGRATION.md](docs/STRIPE_INTEGRATION.md)**

Этот документ содержит:
- Детальное обоснование архитектурного решения
- Описание всех сервисных функций с примерами
- Интеграцию с Django моделями и ViewSet'ами
- Стратегию тестирования (25 тестов с 100% coverage)
- Best practices и примеры использования

Используйте этот документ как референс для других интеграций (SendGrid, Twilio, PayPal и т.д.).

---

## Workflow разработки

### 1. Создание новой фичи

```bash
# 1. Создаем новую ветку (если используется Git)
git checkout -b feature/new-feature

# 2. Пишем код
# ... редактируем файлы ...

# 3. Автоформатирование
poetry run black apps/ config/
poetry run isort apps/ config/

# 4. Проверка стиля
poetry run flake8 apps/ config/

# 5. Запуск тестов
poetry run pytest

# 6. Проверка покрытия
poetry run pytest --cov=apps --cov-report=term-missing

# 7. Коммит (pre-commit hooks запустятся автоматически)
git add .
git commit -m "Добавлена новая фича"
```

### 2. Перед коммитом

Pre-commit hooks **автоматически** выполнят:
1. Удаление trailing whitespace
2. Проверка YAML/TOML файлов
3. Black форматирование
4. isort сортировка импортов
5. flake8 проверка стиля

Если проверка не пройдена - коммит будет отклонен!

### 3. Запуск тестов

```bash
# Все тесты
pytest

# Только тесты core
pytest tests/core/

# Конкретный файл
pytest tests/core/test_models.py

# Конкретный тест
pytest tests/core/test_models.py::test_base_model_soft_delete

# Параллельно (быстрее)
pytest -n auto

# С переиспользованием БД (еще быстрее)
pytest --reuse-db -n auto

# С покрытием
pytest --cov=apps --cov-report=html
```

---

## Примеры использования

### Пример 1: Создание нового сервиса

```python
# apps/mailings/services.py
from apps.core.services import BaseCRUDService
from apps.core.mixins import LoggingMixin, CacheMixin
from apps.mailings.models import Recipient

class RecipientService(BaseCRUDService, LoggingMixin, CacheMixin):
    """Сервис для управления получателями рассылок"""
    
    def __init__(self):
        super().__init__(Recipient)
    
    def validate(self, data: dict) -> bool:
        """Кастомная валидация получателя"""
        if not super().validate(data):
            return False
            
        # Дополнительные проверки
        if not data.get('email'):
            self.add_error("Email обязателен")
            return False
            
        return True
```

### Пример 2: Использование сервиса во view

```python
# apps/mailings/views.py
from django.views.generic import CreateView
from apps.mailings.services import RecipientService

class RecipientCreateView(CreateView):
    def form_valid(self, form):
        service = RecipientService()
        
        data = form.cleaned_data
        recipient = service.create(data, owner=self.request.user)
        
        if recipient:
            return redirect('success')
        else:
            # Показываем ошибки
            for error in service.get_errors():
                form.add_error(None, error)
            return self.form_invalid(form)
```

### Пример 3: Тестирование сервиса

```python
# tests/mailings/test_services.py
import pytest
from apps.mailings.services import RecipientService
from apps.users.models import User

@pytest.fixture
def user(db):
    return User.objects.create_user(email="test@example.com")

@pytest.fixture
def service():
    return RecipientService()

@pytest.mark.django_db
class TestRecipientService:
    def test_create_recipient(self, service, user):
        # Arrange
        data = {
            "email": "recipient@example.com",
            "full_name": "Test Recipient"
        }
        
        # Act
        recipient = service.create(data, owner=user)
        
        # Assert
        assert recipient is not None
        assert recipient.email == "recipient@example.com"
        assert recipient.owner == user
    
    def test_create_without_email_fails(self, service, user):
        # Arrange
        data = {"full_name": "Test"}
        
        # Act
        recipient = service.create(data, owner=user)
        
        # Assert
        assert recipient is None
        assert service.has_errors()
        assert "Email обязателен" in service.get_errors()
```

---

## Known Issues & Solutions

Документация критических проблем, с которыми мы столкнулись в процессе разработки, и их решений.

### 🔴 Проблема #1: APScheduler + PostgreSQL Connection Issues

**Симптомы:**
```
SSL SYSCALL error: EOF detected
server closed the connection unexpectedly
```

При выполнении scheduled tasks (автоматическая отправка рассылок) возникали SSL timeout errors и разрывы соединения с PostgreSQL.

**Причина:**
APScheduler выполняет задачи в отдельных потоках. Django автоматически управляет database connections в основном потоке (request/response cycle), но **не закрывает старые соединения** в background threads. Старые соединения накапливаются и становятся stale, что приводит к SSL errors.

**Решение:**

1. **Декоратор `@close_db_connections`** для автоматического управления соединениями:

```python
# apps/mailings/scheduler.py

from functools import wraps
from django.db import close_old_connections

def close_db_connections(func):
    """
    Декоратор для автоматического закрытия старых DB соединений
    в background задачах APScheduler.
    
    Django автоматически управляет connections в request/response cycle,
    но не в background threads. Этот декоратор закрывает старые соединения
    до и после выполнения задачи.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Закрываем старые соединения перед выполнением
        close_old_connections()
        try:
            return func(*args, **kwargs)
        finally:
            # Закрываем соединения после выполнения
            close_old_connections()
    return wrapper

@close_db_connections
def _execute_scheduled_mailings():
    """Основная функция планировщика"""
    # ... логика отправки рассылок
```

2. **Retry logic с exponential backoff** для temporary SSL errors:

```python
MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    try:
        # DB operations
        break
    except Exception as e:
        error_msg = str(e)
        # Проверяем на SSL ошибки и разрывы соединения
        is_ssl_error = "SSL connection" in error_msg or "server closed the connection" in error_msg
        
        if is_ssl_error and attempt < MAX_RETRIES - 1:
            # Exponential backoff: 1s, 2s, 4s
            sleep(1 * (2 ** attempt))
            close_old_connections()  # Force reconnect
            continue
        raise
```

3. **Database settings оптимизация** (`config/settings.py`):

```python
DATABASES = {
    'default': {
        # ...
        'CONN_MAX_AGE': 600,  # Переиспользуем соединения до 10 минут
        'CONN_HEALTH_CHECKS': True,  # Проверка соединений перед использованием
    }
}
```

**Результат:**
- ✅ SSL timeout errors устранены полностью
- ✅ Scheduled tasks выполняются стабильно
- ✅ Автоматическое переподключение при temporary network issues

**Файлы:**
- `apps/mailings/scheduler.py` - декоратор `@close_db_connections`
- `config/settings.py` - database connection settings

---

### 🔴 Проблема #2: Browser Cache (304 Not Modified) для Scheduler Status

**Симптомы:**
Статус "Последний запуск планировщика: XX:XX" на главной странице не обновляется даже после выполнения scheduled mailings. Браузер возвращает **304 Not Modified** и показывает старый cached контент.

**Причина:**
Для оптимизации используется HTTP conditional requests (ETag). При расчёте ETag для главной страницы мы учитывали:
- Количество рассылок
- Количество активных рассылок  
- Количество уникальных получателей

**НО НЕ учитывали** `scheduler_last_run` - timestamp последнего запуска планировщика.

Когда планировщик обновлял только `scheduler_last_run` (без изменения статистики), ETag оставался прежним, и браузер использовал cached версию страницы.

**Решение:**

Добавили `scheduler_last_run` в источники данных для расчёта ETag:

```python
# apps/mailings/views.py

def calculate_etag_for_home(request: HttpRequest) -> str:
    """
    Рассчитывает ETag для главной страницы на основе данных пользователя.
    
    ETag включает scheduler_last_run чтобы браузер обновлял страницу
    при изменении статуса планировщика (даже если статистика не изменилась).
    """
    user = request.user
    if not user.is_authenticated:
        return "anonymous"

    # Получаем scheduler_last_run из кэша
    scheduler_last_run = cache.get("scheduler_last_run")
    
    # Источники данных для ETag
    data_sources = {
        "user_id": user.id,
        "total_mailings": get_cached_total_mailings(user),
        "active_mailings": get_cached_active_mailings(user),
        "unique_recipients": get_cached_unique_recipients(user),
        "scheduler_last_run": scheduler_last_run,  # ← КРИТИЧНО!
    }

    # MD5 hash от данных
    data_string = json.dumps(data_sources, sort_keys=True)
    return hashlib.md5(data_string.encode()).hexdigest()
```

**До исправления:**
```
User opens page → ETag: "abc123" (based on stats only)
Scheduler runs → scheduler_last_run updated
User refreshes → Server: ETag still "abc123" → Browser: 304 Not Modified (stale data)
```

**После исправления:**
```
User opens page → ETag: "abc123"
Scheduler runs → scheduler_last_run updated  
User refreshes → Server: ETag now "def456" → Browser: 200 OK (fresh data) ✅
```

**Результат:**
- ✅ Статус планировщика обновляется немедленно при refresh
- ✅ Browser cache работает корректно для других данных
- ✅ Optimal balance между caching и актуальностью данных

**Файлы:**
- `apps/mailings/views.py` - функция `calculate_etag_for_home()`
- `apps/mailings/scheduler.py` - обновление `cache.set("scheduler_last_run", ...)`

---

### 💡 Уроки

**1. Background Tasks & Database:**
- Django ORM connections НЕ управляются автоматически в non-request threads
- Всегда используйте `close_old_connections()` в APScheduler/Celery tasks
- Добавляйте retry logic для temporary network issues

**2. HTTP Caching:**
- ETag должен включать **ВСЕ** данные, отображаемые на странице
- Тестируйте browser cache с `curl -I` или DevTools Network tab
- Eventual consistency допустима для некритичной статистики, но не для real-time данных

**3. Debugging:**
- Проверяйте logs планировщика: `logs/django.log`
- Используйте `LOG_TO_CONSOLE=True` для видимости cache hits/misses
- Мониторьте DB connections: `SELECT * FROM pg_stat_activity;`

---

## Работа с базой данных и Fixtures

### ⚠️ КРИТИЧНО: Безопасность данных

**ЗОЛОТОЕ ПРАВИЛО: Никогда не пересоздавайте базу данных без резервного копирования данных!**

База данных может быть пересоздана только в двух случаях:
1. **Пустая БД** - в таблицах нет данных (проверить перед пересозданием!)
2. **После выгрузки данных** - данные сохранены в fixtures или SQL dump

### Проверка наличия данных перед пересозданием

**ОБЯЗАТЕЛЬНО** проверяйте наличие данных в БД перед любыми деструктивными операциями:

```bash
# Способ 1: Через Django shell
python manage.py shell
>>> from django.apps import apps
>>> for model in apps.get_models():
...     count = model.objects.count()
...     if count > 0:
...         print(f"{model._meta.label}: {count} записей")

# Способ 2: SQL запрос (PostgreSQL)
python manage.py dbshell
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables
WHERE n_live_tup > 0
ORDER BY n_live_tup DESC;
```

### Процедура безопасного пересоздания БД

#### Шаг 1: Проверка наличия данных

```bash
# Проверить все таблицы на наличие данных
python manage.py shell -c "
from django.apps import apps
has_data = False
for model in apps.get_models():
    count = model.objects.count()
    if count > 0:
        print(f'✅ {model._meta.label}: {count} записей')
        has_data = True
if not has_data:
    print('✓ БД пуста, можно пересоздавать')
else:
    print('⚠️ ВНИМАНИЕ: В БД есть данные! Сделайте резервную копию!')
"
```

#### Шаг 2: Выгрузка данных (если есть)

**Если в БД есть данные, ОБЯЗАТЕЛЬНО выгрузите их:**

```bash
# Способ 1: Django Fixtures (JSON формат)
# Выгрузка всех данных
python -Xutf8 manage.py dumpdata --indent 4 --output backup_all.json

# Выгрузка конкретных приложений
python -Xutf8 manage.py dumpdata users --indent 4 --output backup_users.json
python -Xutf8 manage.py dumpdata lms.Course --indent 4 --output backup_courses.json
python -Xutf8 manage.py dumpdata lms.Lesson --indent 4 --output backup_lessons.json

# Способ 2: PostgreSQL dump (полная резервная копия)
pg_dump -U $PGUSER -h $PGHOST -p $PGPORT $PGDATABASE > backup.sql

# Способ 3: Экспорт в CSV (если fixtures не работает)
python manage.py shell << EOF
import csv
from lms.models import Course

with open('courses.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'title', 'description', 'created_at'])
    for course in Course.objects.all():
        writer.writerow([course.id, course.title, course.description, course.created_at])
print('Exported to courses.csv')
EOF
```

#### Шаг 3: Пересоздание БД (только для пустой БД или после выгрузки!)

```bash
# ОПАСНАЯ ОПЕРАЦИЯ! Только после выгрузки данных или для пустой БД!

# Удаление всех таблиц и пересоздание схемы
python manage.py dbshell << EOF
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO public;
EOF

# Удаление файлов миграций
rm -rf */migrations/0*.py

# Создание новых миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate
```

#### Шаг 4: Восстановление данных

```bash
# Способ 1: Загрузка fixtures
python manage.py loaddata backup_users.json
python manage.py loaddata backup_courses.json
python manage.py loaddata backup_lessons.json

# Способ 2: PostgreSQL restore
psql -U $PGUSER -h $PGHOST -p $PGPORT $PGDATABASE < backup.sql

# Способ 3: Программное восстановление из CSV
python manage.py shell << EOF
import csv
from lms.models import Course
from datetime import datetime

with open('courses.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        Course.objects.create(
            id=row['id'],
            title=row['title'],
            description=row['description']
        )
print('Restored from courses.csv')
EOF
```

### Работа с Fixtures

#### Что такое Fixtures?

Fixtures - это сериализованные данные в JSON/YAML/XML формате для быстрой загрузки тестовых или начальных данных.

**Используйте fixtures для:**
- Тестовых данных для разработки
- Демо-данных для презентаций
- Миграции данных между окружениями
- Резервного копирования небольших наборов данных

#### Создание Fixtures

```bash
# Создать директорию для fixtures (если нет)
mkdir -p app_name/fixtures

# Выгрузить все данные приложения
python -Xutf8 manage.py dumpdata app_name --indent 4 --output app_name/fixtures/initial_data.json

# Выгрузить конкретную модель
python -Xutf8 manage.py dumpdata app_name.ModelName --indent 4 --output app_name/fixtures/model_data.json

# Выгрузить несколько моделей
python -Xutf8 manage.py dumpdata lms.Course lms.Lesson --indent 4 --output lms/fixtures/courses_and_lessons.json

# Исключить конкретные приложения (например, contenttypes)
python -Xutf8 manage.py dumpdata --exclude=contenttypes --exclude=auth.Permission --indent 4 --output full_backup.json
```

**Флаг `-Xutf8`** важен для корректной работы с русским текстом на некоторых платформах.

#### Загрузка Fixtures

```bash
# Загрузить конкретный файл
python manage.py loaddata app_name/fixtures/initial_data.json

# Загрузить все fixtures из app_name/fixtures/
python manage.py loaddata initial_data

# Загрузить несколько файлов
python manage.py loaddata users_data courses_data lessons_data
```

Django автоматически ищет fixtures в директориях `app_name/fixtures/`.

#### Структура Fixture файла

```json
[
  {
    "model": "lms.course",
    "pk": 1,
    "fields": {
      "created_at": "2025-10-27T18:15:43.316Z",
      "updated_at": "2025-10-27T18:15:43.316Z",
      "title": "Python для начинающих",
      "description": "Полный курс по Python",
      "preview": "courses/previews/python_course.jpg"
    }
  },
  {
    "model": "lms.lesson",
    "pk": 1,
    "fields": {
      "created_at": "2025-10-27T18:15:44.101Z",
      "updated_at": "2025-10-27T18:15:44.101Z",
      "course": 1,
      "title": "Введение в Python",
      "description": "Первый урок",
      "preview": "lessons/previews/intro_lesson.jpg",
      "video_url": "https://www.youtube.com/watch?v=intro"
    }
  }
]
```

**Примечание:** Поля `preview` опциональны (`blank=True, null=True`), но рекомендуется указывать пути к реальным файлам в `media/` для полной функциональности API.

#### Управление ID в Fixtures

**Важно:** При загрузке fixtures Django использует указанные `pk` (primary key):

```bash
# Если нужно сбросить счетчики ID после загрузки
python manage.py shell
>>> from django.core.management import call_command
>>> call_command('sqlsequencereset', 'lms')
# Скопируйте вывод и выполните в dbshell
```

### Troubleshooting PostgreSQL

#### 🔴 Проблема: "cursor does not exist" при dumpdata

**Симптомы:**
```bash
python manage.py dumpdata lms.Course --indent 4 --output courses.json
CommandError: Unable to serialize database: cursor "_django_curs_XXX_sync_1" does not exist
```

**Причины:**
1. Соединение с PostgreSQL было прервано или курсор был закрыт
2. База данных пуста (0 записей в таблице)
3. Старое/зависшее соединение с базой данных
4. Несовместимость структуры таблиц с моделями

**Решения:**

**Решение 1: Перезапуск сервера и проверка данных**
```bash
# Перезапустить Django сервер (закрывает все соединения)
# Или перезапустить workflow, если используете

# Проверить наличие данных
python manage.py shell -c "from lms.models import Course; print(f'Courses: {Course.objects.count()}')"

# Если 0 записей - создать тестовые данные, затем повторить dumpdata
```

**Решение 2: Использование альтернативного формата**
```bash
# Если JSON dumpdata не работает, используйте SQL dump
pg_dump -U $PGUSER -h $PGHOST -p $PGPORT -t lms_course $PGDATABASE > courses.sql

# Или экспорт через Python
python manage.py shell << EOF
import json
from lms.models import Course
from django.core.serializers import serialize

data = serialize('json', Course.objects.all(), indent=4)
with open('courses.json', 'w', encoding='utf-8') as f:
    f.write(data)
print('Exported to courses.json')
EOF
```

**Решение 3: Проверка и синхронизация схемы БД**
```bash
# Проверить статус миграций
python manage.py showmigrations

# Если есть неприменённые миграции
python manage.py migrate

# Если структура БД не соответствует моделям
python manage.py migrate --run-syncdb
```

**Решение 4: Полное пересоздание БД (ТОЛЬКО для пустой БД!)**
```bash
# ⚠️ ОПАСНО! Только если БД пуста или данные выгружены!

# 1. Проверить что БД пуста
python manage.py shell -c "
from django.apps import apps
for model in apps.get_models():
    count = model.objects.count()
    if count > 0:
        print(f'STOP! {model._meta.label} has {count} records!')
        exit(1)
print('OK: Database is empty')
"

# 2. Только если OK - пересоздать БД
python manage.py dbshell << EOF
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO public;
EOF

# 3. Удалить миграции
rm -rf */migrations/0*.py

# 4. Создать новые миграции
python manage.py makemigrations

# 5. Применить миграции
python manage.py migrate

# 6. Создать тестовые данные
python manage.py shell << EOF
from lms.models import Course
Course.objects.create(title="Test Course", description="Test")
print("Created test data")
EOF

# 7. Попробовать dumpdata снова
python -Xutf8 manage.py dumpdata lms.Course --indent 4 --output courses.json
```

#### Профилактика проблем с курсорами

**Лучшие практики:**

1. **Регулярно проверяйте соединения:**
```bash
# Мониторинг активных соединений
python manage.py dbshell
SELECT count(*) as connections, state 
FROM pg_stat_activity 
WHERE datname = current_database() 
GROUP BY state;
```

2. **Используйте connection pooling:**
```python
# config/settings.py
DATABASES = {
    'default': {
        # ...
        'CONN_MAX_AGE': 600,           # Переиспользуем соединения до 10 минут
        'CONN_HEALTH_CHECKS': True,    # Проверка соединений перед использованием
    }
}
```

3. **Закрывайте старые соединения в scheduled tasks:**
```python
from django.db import close_old_connections

def my_scheduled_task():
    close_old_connections()  # Перед выполнением
    try:
        # Ваш код
        pass
    finally:
        close_old_connections()  # После выполнения
```

### Полезные команды для работы с БД

```bash
# Проверка подключения к БД
python manage.py dbshell -c "SELECT version();"

# Список всех таблиц
python manage.py dbshell -c "\dt"

# Размер базы данных
python manage.py dbshell -c "SELECT pg_size_pretty(pg_database_size(current_database()));"

# Количество записей в каждой таблице
python manage.py dbshell << EOF
SELECT schemaname, tablename, n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
EOF

# Информация о соединениях
python manage.py dbshell -c "SELECT * FROM pg_stat_activity WHERE datname = current_database();"
```

### Чек-лист работы с БД

Перед любыми деструктивными операциями:

- [ ] Проверили наличие данных в БД
- [ ] Выгрузили данные в fixtures/SQL dump (если есть данные)
- [ ] Сохранили резервную копию в безопасное место
- [ ] Протестировали восстановление из резервной копии
- [ ] Документировали процедуру для команды

**ПОМНИТЕ: Потеря данных необратима! Всегда делайте резервные копии!**

---

## Чек-лист перед коммитом

- [ ] Код отформатирован (black, isort)
- [ ] Нет ошибок flake8
- [ ] Все новые функции/классы задокументированы
- [ ] Написаны тесты для нового кода
- [ ] Все тесты проходят (`pytest`)
- [ ] Покрытие кода не уменьшилось
- [ ] Pre-commit hooks проходят успешно

---

## Полезные ссылки

- [pytest-django документация](https://pytest-django.readthedocs.io/)
- [Pydantic документация](https://docs.pydantic.dev/)
- [Black документация](https://black.readthedocs.io/)
- [flake8 правила](https://flake8.pycqa.org/en/latest/user/error-codes.html)

---

## Статические файлы (Static Files)

### Структура static директории

Проект использует статические файлы для стилистики и интерактивности:

```
static/
├── css/
│   ├── bootstrap.min.css    # Bootstrap 5 CSS фреймворк
│   └── custom.css            # Кастомные стили проекта
└── js/
    ├── bootstrap.bundle.min.js  # Bootstrap JS с Popper
    └── category-filter.js       # Кастомная JS логика
```

### Использование в Django шаблонах

**ОБЯЗАТЕЛЬНО** подключайте статические файлы в шаблонах:

```django
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="{% static 'css/bootstrap.min.css' %}">
    
    <!-- Custom CSS -->
    <link rel="stylesheet" href="{% static 'css/custom.css' %}">
</head>
<body>
    <!-- Ваш контент -->
    
    <!-- Bootstrap JS -->
    <script src="{% static 'js/bootstrap.bundle.min.js' %}"></script>
    
    <!-- Custom JS -->
    <script src="{% static 'js/category-filter.js' %}"></script>
</body>
</html>
```

### Настройка статических файлов

В `config/settings.py`:

```python
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]  # Для разработки
STATIC_ROOT = BASE_DIR / "staticfiles"     # Для production
```

### Сборка статики для production

```bash
# Собрать все статические файлы в STATIC_ROOT
poetry run python manage.py collectstatic --noinput
```

### Правила работы со статикой

1. **Всегда используйте {% static %}**: Не хардкодите пути к файлам
2. **Bootstrap 5**: Используется как основа для UI
3. **custom.css**: Для переопределения Bootstrap и кастомных стилей
4. **Именование JS файлов**: kebab-case (category-filter.js, не categoryFilter.js)
5. **Минификация**: В production используйте минифицированные версии

### Добавление новых статических файлов

```bash
# 1. Добавить файл в static/css/ или static/js/
static/css/my-component.css

# 2. Подключить в шаблоне
{% load static %}
<link rel="stylesheet" href="{% static 'css/my-component.css' %}">

# 3. Для production - собрать статику
poetry run python manage.py collectstatic
```


---

## Настройка окружения для разработки

### ⚠️ ВАЖНО: Использование .env файла

**Проект ОБЯЗАТЕЛЬНО использует .env файл для всех параметров конфигурации!**

Это необходимо для:
- Локальной разработки на любой платформе (Windows/Mac/Linux)
- Тестирования на разных машинах
- Согласованности окружения между разработчиками

### Создание .env файла (Windows/Локальная разработка)

1. **Скопируйте .env.example в .env:**
   ```bash
   # Windows (PowerShell)
   Copy-Item .env.example .env
   
   # Linux/Mac
   cp .env.example .env
   ```

2. **Обновите параметры в .env:**
   ```bash
   # Обязательные параметры для изменения:
   SECRET_KEY="ваш-уникальный-секретный-ключ"
   
   # PostgreSQL (установите свои параметры)
   DB_NAME=drf
   DB_USER=ваш_пользователь
   DB_PASSWORD=ваш_пароль
   DB_HOST=localhost
   DB_PORT=5432
   ```

3. **Проверьте, что .env в .gitignore:**
   ```bash
   # .gitignore уже содержит:
   .env
   ```

### Структура .env файла

```bash
# Django Core
SECRET_KEY="django-insecure-ЗАМЕНИТЕ-НА-СВОЙ-КЛЮЧ"
DEBUG=True

# Database
DB_NAME=drf
DB_USER=drf_user
DB_PASSWORD=drf_password
DB_HOST=localhost
DB_PORT=5432

# Email (для разработки используем console backend)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=True
LOG_DIR=logs

# Timezone
TZ=Europe/Moscow

# Cache (locmem для разработки, redis для production)
CACHE_ENABLED=True
CACHE_BACKEND=locmem
CACHE_TIMEOUT=30

# CORS (разрешенные origins для фронтенда)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Telegram Bot (получить через @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_WEBHOOK_SECRET=random_secret_string

# DRF
DRF_PAGE_SIZE=20
```

### Генерация SECRET_KEY

**ОБЯЗАТЕЛЬНО** сгенерируйте уникальный SECRET_KEY для вашего .env:

```python
# Способ 1: Python консоль
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Способ 2: Django shell
python manage.py shell
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
```

### Настройка PostgreSQL на Windows

1. **Установите PostgreSQL:**
   - Скачайте с https://www.postgresql.org/download/windows/
   - Запомните пароль для пользователя postgres

2. **Создайте базу данных:**
   ```sql
   -- Подключитесь к PostgreSQL
   psql -U postgres
   
   -- Создайте пользователя
   CREATE USER drf_user WITH PASSWORD 'ваш_пароль';
   
   -- Создайте базу данных
   CREATE DATABASE drf OWNER drf_user;
   
   -- Дайте права
   GRANT ALL PRIVILEGES ON DATABASE drf TO drf_user;
   ```

3. **Обновите .env:**
   ```bash
   DB_NAME=drf
   DB_USER=drf_user
   DB_PASSWORD=ваш_пароль
   DB_HOST=localhost
   DB_PORT=5432
   ```

### Работа в Production/Cloud vs Локально

**В Production/Cloud окружении:**
- Параметры берутся из переменных окружения (environment variables)
- DATABASE_URL часто настраивается автоматически платформой
- SECRET_KEY и другие секреты добавляются через панель управления

**В локальной разработке:**
- Параметры берутся из .env файла
- PostgreSQL устанавливается локально
- Все настройки в .env файле

**Код работает в обоих случаях** благодаря:
```python
# config/settings.py
load_dotenv(override=True, encoding="utf8")  # Загружает .env если есть
SECRET_KEY = os.getenv("SECRET_KEY")         # Берет из .env или environment
```

### Проверка настройки

```bash
# 1. Проверьте, что .env создан
ls -la .env  # должен существовать

# 2. Проверьте подключение к БД
python manage.py migrate

# 3. Запустите сервер
python manage.py runserver

# 4. Проверьте переменные окружения
python manage.py shell
>>> import os
>>> print(os.getenv('SECRET_KEY'))  # должен показать ваш ключ
>>> print(os.getenv('DEBUG'))        # должен показать True
```

### Безопасность

- ❌ **НИКОГДА** не коммитьте .env в git
- ✅ Всегда используйте .env.example как шаблон
- ✅ Каждый разработчик создает свой .env локально
- ✅ В production используйте переменные окружения сервера
- ✅ SECRET_KEY должен быть уникальным для каждого окружения


---

## Автоматизация проверок кода

### 🚀 Быстрый старт

**Одна команда для всех проверок:**
```bash
poetry run check
```

**Автоматическое исправление проблем:**
```bash
poetry run fix
```

### Доступные инструменты

#### 1. **poetry run check** - Полная проверка кода ✅

Запускает ВСЕ линтеры в правильном порядке:
1. Ruff (быстрая проверка багов)
2. Mypy (проверка типов)
3. Black (форматирование)
4. Isort (сортировка импортов)
5. Flake8 (дополнительные проверки)
6. Django check (проверка настроек)

```bash
# Запустить все проверки
poetry run check
```

#### 2. **poetry run fix** - Автоисправление 🔧

Автоматически исправляет большинство проблем:
- Форматирует код (Black)
- Сортирует импорты (Isort)
- Исправляет простые баги (Ruff)

```bash
poetry run fix
```

#### 3. **Watch-режим** - Проверка в реальном времени 👀

Автоматически проверяет код при сохранении файлов:

```bash
./scripts/watch.sh
```

#### 4. **VS Code автоформатирование** ⚡

Настройки в `.vscode/settings.json` включают автоформатирование при сохранении (Ctrl+S / Cmd+S):
- ✅ Black форматирование
- ✅ Isort сортировка импортов
- ✅ Удаление trailing whitespace

### Рекомендуемый Workflow

```bash
# 1. Работаете в IDE с автоформатированием (Ctrl+S)
# 2. Перед коммитом запускаете:
poetry run check

# 3. Если есть ошибки:
poetry run fix

# 4. Делаете коммит (pre-commit тоже проверит):
git add .
git commit -m "Добавил новую фичу"
```

**Золотое правило:** Никогда не коммитьте код, который не проходит `poetry run check`! 🚫

---

## Архитектура моделей проекта

### Иерархия базовых моделей

```
BaseModel (абстрактная)
├── timestamps: created_at, updated_at
├── ordering по created_at
└── Используется для User модели

SoftDeletableModel(BaseModel) (абстрактная)
├── наследует: created_at, updated_at
├── добавляет: is_active
├── методы: soft_delete(), restore()
└── Используется для обычных моделей

OwnedModel(SoftDeletableModel) (абстрактная)
├── наследует: created_at, updated_at, is_active
├── добавляет: owner (FK to User)
└── Используется для моделей с владельцем
```

### Использование в коде

**Для User модели:**
```python
from django.contrib.auth.models import AbstractUser
from apps.core.models import BaseModel

class User(AbstractUser, BaseModel):
    # Получает is_active от AbstractUser
    # Получает created_at, updated_at от BaseModel
    pass
```

**Для обычных моделей:**
```python
from apps.core.models import SoftDeletableModel

class MyModel(SoftDeletableModel):
    # Получает created_at, updated_at, is_active
    # Методы: soft_delete(), restore()
    name = models.CharField(max_length=100)
```

**Для моделей с владельцем:**
```python
from apps.core.models import OwnedModel

class MyOwnedModel(OwnedModel):
    # Получает created_at, updated_at, is_active, owner
    # Методы: soft_delete(), restore()
    title = models.CharField(max_length=200)
```

### ⚠️ ВАЖНО

- **НЕ используйте** `SoftDeletableModel` для User модели (конфликт is_active)
- **Используйте** `BaseModel` для User и других моделей без soft delete
- **Используйте** `SoftDeletableModel` для моделей с soft delete
- **Используйте** `OwnedModel` для моделей с owner и soft delete

