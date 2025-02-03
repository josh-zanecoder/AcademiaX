from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registration/', views.registration, name='registration'),
    path('api/register/', views.register_student, name='register_student'),
    path('login/', views.login, name='login'),
]