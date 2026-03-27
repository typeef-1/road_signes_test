from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
import uuid

class Test(models.Model):
    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_UNLISTED = 'unlisted'
    VISIBILITY_RESTRICTED = 'restricted'

    VISIBILITY_CHOICES = (
        (VISIBILITY_PUBLIC, 'Публичное (видно всем)'),
        (VISIBILITY_UNLISTED, 'По ссылке (не показывать в списке)'),
        (VISIBILITY_RESTRICTED, 'Только выбранным пользователям'),
    )

    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name="Описание")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tests')
    visibility = models.CharField(
        max_length=12,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        verbose_name='Доступ',
    )
    share_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    allowed_users = models.ManyToManyField(
        User,
        blank=True,
        related_name='allowed_tests',
        verbose_name='Разрешённые пользователи',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def can_view(self, user, via_share_link: bool = False) -> bool:
        if user and (user.is_superuser or user == self.author):
            return True
        if self.visibility == self.VISIBILITY_PUBLIC:
            return True
        if self.visibility == self.VISIBILITY_UNLISTED:
            return bool(via_share_link)
        if self.visibility == self.VISIBILITY_RESTRICTED:
            if not user or not user.is_authenticated:
                return False
            return self.allowed_users.filter(pk=user.pk).exists()
        return False

class Question(models.Model):
    QUESTION_TYPES = (
        ('single', 'Одиночный выбор'),
        ('multiple', 'Множественный выбор'),
        ('text', 'Текстовый ответ'),
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name="Текст вопроса")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='single')
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.test.title} - {self.text[:50]}"

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=300, verbose_name="Текст ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный")

    def __str__(self):
        return self.text

class UserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(blank=True, verbose_name="Текстовый ответ")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'],
                condition=Q(selected_answer__isnull=True),
                name='uniq_user_question_for_text',
            ),
            models.UniqueConstraint(
                fields=['user', 'question', 'selected_answer'],
                condition=Q(selected_answer__isnull=False),
                name='uniq_user_question_selected_answer',
            ),
        ]

class TestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.FloatField(verbose_name="Баллы", default=0)
    max_score = models.FloatField(verbose_name="Максимум баллов", default=0)
    percentage = models.FloatField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.test.title} - {self.percentage}%"