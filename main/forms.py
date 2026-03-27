from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from .models import Test, Question, Answer

class TestForm(forms.ModelForm):
    allowed_usernames = forms.CharField(
        required=False,
        label='Разрешённые ники (username)',
        help_text='Только для режима “Только выбранным пользователям”. Введите usernames через запятую.',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'user1, user2'}),
    )

    class Meta:
        model = Test
        fields = ['title', 'description', 'visibility']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Выбор логотипа'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Коротко опишите суть голосования'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            usernames = self.instance.allowed_users.values_list('username', flat=True)
            self.fields['allowed_usernames'].initial = ', '.join(usernames)

    def clean_allowed_usernames(self):
        raw = self.cleaned_data.get('allowed_usernames', '') or ''
        usernames = [u.strip() for u in raw.split(',') if u.strip()]
        seen = set()
        result = []
        for u in usernames:
            if u.lower() in seen:
                continue
            seen.add(u.lower())
            result.append(u)
        return result

    def save(self, commit=True):
        instance = super().save(commit=commit)
        usernames = self.cleaned_data.get('allowed_usernames', [])
        User = get_user_model()
        if instance.pk:
            if instance.visibility == Test.VISIBILITY_RESTRICTED:
                users = list(User.objects.filter(username__in=usernames))
                instance.allowed_users.set(users)
            else:
                instance.allowed_users.clear()
        return instance

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'question_type']
        labels = {
            'text': 'Текст вопроса',
            'question_type': 'Тип вопроса',
        }
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-select'}),
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']
        labels = {
            'text': 'Вариант ответа',
        }
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
        }

AnswerFormSetCreate = inlineformset_factory(
    Question,
    Answer,
    fields=('text',),
    extra=2,
    can_delete=True
)

AnswerFormSetEdit = inlineformset_factory(
    Question,
    Answer,
    fields=('text',),
    extra=0,
    can_delete=True
)