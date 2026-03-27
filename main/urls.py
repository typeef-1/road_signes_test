from django.urls import path
from . import views


urlpatterns = [
    path('', views.TestListView.as_view(), name='test_list'),
    path('<int:pk>/', views.TestDetailView.as_view(), name='test_detail'),
    path('create/', views.TestCreateView.as_view(), name='test_create'),
    path('share/<uuid:share_uuid>/', views.TestShareDetailView.as_view(), name='test_share_detail'),
    path('share/<uuid:share_uuid>/take/', views.TestShareTakeView.as_view(), name='test_share_take'),
    path('share/<uuid:share_uuid>/result/', views.TestShareResultView.as_view(), name='test_share_result'),
    path('<int:pk>/take/', views.TestTakeView.as_view(), name='test_take'),
    path('<int:pk>/result/', views.TestResultView.as_view(), name='test_result'),
    path('<int:pk>/edit/', views.TestUpdateView.as_view(), name='test_edit'),
    path('question/<int:pk>/edit/', views.QuestionUpdateView.as_view(), name='question_edit'),
    path('test/<int:test_pk>/question/add/', views.QuestionCreateView.as_view(), name='question_add'),

]