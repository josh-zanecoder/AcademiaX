from django.urls import path
from . import views
from . import admin_page

urlpatterns = [
    path('', views.index, name='index'),
    path('registration/', views.registration, name='registration'),
    path('api/register/', views.register_student, name='register_student'),
    path('login/', views.login_page, name='login'),
    path('api/login/', views.login_user, name='login_user'),
    path('logout', views.logout_user, name='logout'),

    path('student_page/', views.student_page, name='student_page'),
    path('admin_page/', views.admin_page, name='admin_page'),
   



    path('manage_courses/', admin_page.manage_courses, name='manage_courses'),
    path('api/courses/', admin_page.get_courses, name='get_courses'),
    path('api/courses/create/', admin_page.create_course, name='create_course'),

    path('api/courses/<uuid:course_id>/update/', admin_page.update_course, name='update_course'),
    path('api/courses/<uuid:course_id>/delete/', admin_page.delete_course, name='delete_course'),

    path('manage_teachers/', admin_page.manage_teachers, name='manage_teachers'),
    path('api/teachers/', admin_page.get_teacher, name='get_teachers'),
    path('api/teachers/create/', admin_page.create_teacher, name='create_teacher'),
    path('api/teachers/<int:teacher_id>/', admin_page.get_teacher, name='get_teacher'),
    path('api/teachers/<int:teacher_id>/update/', admin_page.update_teacher, name='update_teacher'),
    path('api/teachers/<int:teacher_id>/delete/', admin_page.delete_teacher, name='delete_teacher'),
]