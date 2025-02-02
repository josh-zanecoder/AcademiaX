from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('registration/', views.registration, name='registration'),
    path('api/register/', views.register_student, name='register_student'),
    path('login/', views.login_page, name='login'),
    path('api/login/', views.login_user, name='login_user'),
    path('student_page/', views.student_page, name='student_page'),
    path('admin_page/', views.admin_page, name='admin_page'),
    path('logout', views.logout_user, name='logout'),
]