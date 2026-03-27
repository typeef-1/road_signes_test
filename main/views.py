from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from django.db import models
from django.http import Http404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
from .models import Test, Question, Answer, UserAnswer, TestResult
from .forms import TestForm, QuestionForm, AnswerFormSetCreate, AnswerFormSetEdit


class TestListView(ListView):
    model = Test
    template_name = 'tests/test_list.html'
    context_object_name = 'tests'
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset().select_related('author')
        user = self.request.user
        if user.is_authenticated:
            return qs.filter(
                (
                    models.Q(visibility=Test.VISIBILITY_PUBLIC)
                    | models.Q(author=user)
                    | models.Q(visibility=Test.VISIBILITY_RESTRICTED, allowed_users=user)
                )
            ).distinct()
        return qs.filter(visibility=Test.VISIBILITY_PUBLIC)

class TestDetailView(DetailView):
    model = Test
    template_name = 'tests/test_detail.html'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if not obj.can_view(self.request.user, via_share_link=False):
            raise Http404()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['share_url'] = self.request.build_absolute_uri(
            reverse_lazy('test_share_detail', kwargs={'share_uuid': self.object.share_uuid})
        )
        return context

class TestCreateView(LoginRequiredMixin, CreateView):
    model = Test
    form_class = TestForm
    template_name = 'tests/test_form.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        self.object = form.save()
        messages.info(self.request, 'Голосование создано. Теперь добавьте вопросы.')
        return redirect('question_add', test_pk=self.object.pk)

class TestTakeView(LoginRequiredMixin, View):
    def get(self, request, pk):
        test = get_object_or_404(Test, pk=pk)
        if not test.can_view(request.user, via_share_link=False):
            raise Http404()
        if TestResult.objects.filter(user=request.user, test=test).exists():
            messages.warning(request, 'Вы уже прошли этот тест.')
            return redirect('test_result', pk=pk)
        questions = test.questions.all()
        context = {'test': test, 'questions': questions}
        return render(request, 'tests/test_take.html', context)

    def post(self, request, pk):
        test = get_object_or_404(Test, pk=pk)
        if not test.can_view(request.user, via_share_link=False):
            raise Http404()
        if TestResult.objects.filter(user=request.user, test=test).exists():
            messages.warning(request, 'Вы уже проголосовали в этом голосовании.')
            return redirect('test_detail', pk=test.id)

        for question in test.questions.all():
            if question.question_type == 'single':
                selected_id = request.POST.get(f'question_{question.id}')
                if selected_id:
                    answer = get_object_or_404(Answer, id=selected_id, question=question)
                    UserAnswer.objects.create(
                        user=request.user,
                        question=question,
                        selected_answer=answer
                    )
            elif question.question_type == 'multiple':
                selected_ids = request.POST.getlist(f'question_{question.id}')
                for ans_id in selected_ids:
                    answer = get_object_or_404(Answer, id=ans_id, question=question)
                    UserAnswer.objects.create(
                        user=request.user,
                        question=question,
                        selected_answer=answer
                    )
            elif question.question_type == 'text':
                text_answer = request.POST.get(f'question_{question.id}', '')
                UserAnswer.objects.create(
                    user=request.user,
                    question=question,
                    text_answer=text_answer
                )

        TestResult.objects.create(user=request.user, test=test)
        messages.success(request, 'Спасибо! Ваш голос учтён.')
        return redirect('test_result', pk=test.id)

class TestResultView(LoginRequiredMixin, DetailView):
    model = Test
    template_name = 'tests/test_result.html'
    context_object_name = 'test'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if not obj.can_view(self.request.user, via_share_link=False):
            raise Http404()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_voted'] = TestResult.objects.filter(user=self.request.user, test=self.object).exists()

        user_answers = UserAnswer.objects.filter(
            user=self.request.user,
            question__test=self.object,
        ).select_related('question', 'selected_answer')
        context['user_answers'] = user_answers

        question_stats = []
        for question in self.object.questions.all().prefetch_related('answers'):
            if question.question_type in ('single', 'multiple'):
                votes_qs = (
                    UserAnswer.objects.filter(question=question, selected_answer__isnull=False)
                    .values('selected_answer', 'selected_answer__text')
                    .annotate(votes=Count('id'))
                    .order_by('-votes', 'selected_answer__text')
                )
                total_votes = sum(v['votes'] for v in votes_qs)
                question_stats.append(
                    {
                        'question': question,
                        'type': question.question_type,
                        'total_votes': total_votes,
                        'options': list(votes_qs),
                    }
                )
            else:
                texts = (
                    UserAnswer.objects.filter(question=question)
                    .exclude(text_answer='')
                    .values_list('text_answer', flat=True)
                    .order_by('-id')[:50]
                )
                question_stats.append(
                    {
                        'question': question,
                        'type': question.question_type,
                        'texts': list(texts),
                    }
                )
        context['question_stats'] = question_stats
        return context

class TestUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Test
    form_class = TestForm
    template_name = 'tests/test_form.html'
    success_url = reverse_lazy('test_list')

    def test_func(self):
        test = self.get_object()
        return self.request.user == test.author or self.request.user.is_superuser


class TestShareDetailView(DetailView):
    model = Test
    template_name = 'tests/test_detail.html'
    slug_field = 'share_uuid'
    slug_url_kwarg = 'share_uuid'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        if not obj.can_view(self.request.user, via_share_link=True):
            raise Http404()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['share_url'] = self.request.build_absolute_uri(
            reverse_lazy('test_share_detail', kwargs={'share_uuid': self.object.share_uuid})
        )
        return context


class TestShareTakeView(LoginRequiredMixin, View):
    def get(self, request, share_uuid):
        test = get_object_or_404(Test, share_uuid=share_uuid)
        if not test.can_view(request.user, via_share_link=True):
            raise Http404()
        return redirect('test_take', pk=test.pk)


class TestShareResultView(LoginRequiredMixin, View):
    def get(self, request, share_uuid):
        test = get_object_or_404(Test, share_uuid=share_uuid)
        if not test.can_view(request.user, via_share_link=True):
            raise Http404()
        return redirect('test_result', pk=test.pk)


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect('landing')
    form = UserCreationForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('landing')
    return render(request, "registration/signup.html", {"form": form})


class QuestionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Question
    form_class = QuestionForm
    template_name = 'tests/question_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = AnswerFormSetEdit(self.request.POST, instance=self.object, prefix='answers')
        else:
            context['formset'] = AnswerFormSetEdit(instance=self.object, prefix='answers')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('test_detail', kwargs={'pk': self.object.test.id})

    def test_func(self):
        question = self.get_object()
        return self.request.user == question.test.author or self.request.user.is_superuser

class QuestionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Question
    form_class = QuestionForm
    template_name = 'tests/question_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.test = get_object_or_404(Test, pk=kwargs['test_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test'] = self.test
        if self.request.POST:
            context['formset'] = AnswerFormSetCreate(self.request.POST, prefix='answers')
        else:
            context['formset'] = AnswerFormSetCreate(prefix='answers')
        return context

    def form_valid(self, form):
        form.instance.test = self.test
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            return redirect('test_detail', pk=self.test.id)
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def test_func(self):
        return self.request.user == self.test.author or self.request.user.is_superuser