from django.urls import path, include
from . import views

app_name = "account"

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('register/done/<int:user_id>/', views.register_done, name='register_done'),
    path('edit/', views.edit, name='edit'),
    path('users/', views.user_list, name='user_list'),
    path('users/follow/', views.user_follow, name='user_follow'),
    path('users/<str:username>/', views.user_detail, name='user_detail'),
]