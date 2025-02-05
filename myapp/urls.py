from django.urls import path
from . import views
from . import admin_page
from . import teacher
from .import student

urlpatterns = [
    path('', views.index, name='index'),
    path('registration/', views.registration, name='registration'),
    path('api/register/', views.register_student, name='register_student'),
    path('login/', views.login_page, name='login'),
    path('api/login/', views.login_user, name='login_user'),
    path('logout', views.logout_user, name='logout'),

    path('student_page/', student.student_page, name='student_page'),
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


    path('teacher/', teacher.teacher_page, name='teacher_page'),
    path('teacher/courses/<uuid:uid>/', teacher.course_detail, name='course_detail'),
    path('teacher/courses/<uuid:uid>/students/', teacher.course_detail, name='teacher_course_students'),
    path('teacher/api/courses/<uuid:uid>/', teacher.course_details_api, name='teacher_course_api'),
    path('teacher/api/teachers/', teacher.get_teachers, name='teacher_list_api'),


  path('course/<str:uid>/', teacher.course_detail, name='course_detail'),
  path('teacher/courses/<uuid:course_uid>/lessons/', teacher.create_lesson, name='create_lesson'),
  path('teacher/courses/<uuid:course_uid>/lessons/<uuid:lesson_uid>/', teacher.lesson_detail, name='lesson_detail'),
  path('teacher/courses/<uuid:course_uid>/reorder-lessons/', teacher.reorder_lessons, name='reorder_lessons'),
  path('teacher/resources/<int:resource_id>/', teacher.delete_resource, name='delete_resource'),


  path('enroll/<uuid:course_uid>/', student.enroll_course, name='enroll_course'),
  path('student/course/<uuid:uid>/', student.student_course_detail, name='student_course_detail'),
  path('api/student/unenroll/<uuid:course_uid>/', student.unenroll_course, name='unenroll_course'),

  path('api/teacher/course/<uuid:course_uid>/', teacher.get_course, name='get_course'),
  path('api/teacher/course/create/', teacher.create_course, name='create_course'),
  path('api/teacher/course/<uuid:course_uid>/update/', teacher.update_course, name='update_course'),

  path('teacher/course/<uuid:course_uid>/assessment/', teacher.course_assessment, name='course_assessment'),
  path('api/teacher/assessment/create/', teacher.create_assessment, name='create_assessment'),
  path('api/teacher/assessment/<uuid:assessment_id>/', teacher.get_assessment, name='get_assessment'),
  path('api/teacher/assessment/<uuid:assessment_id>/update/', teacher.update_assessment, name='update_assessment'),
  path('api/teacher/assessment/<uuid:assessment_id>/scores/', teacher.get_assessment_scores, name='get_assessment_scores'),
  path('api/teacher/assessment/<uuid:assessment_id>/scores/update/', teacher.update_assessment_scores, name='update_assessment_scores'),
  path('api/teacher/assessment/<uuid:assessment_id>/submissions/', teacher.get_assessment_submissions, name='get_assessment_submissions'),
  path('api/teacher/assessment/<uuid:assessment_id>/submission/<uuid:submission_id>/grade/', teacher.grade_submission, name='grade_submission'),
  path('api/teacher/submission/<uuid:submission_id>/download/', teacher.download_submission, name='download_submission'),

  path('api/teacher/course/<uuid:course_uid>/assessments/', teacher.get_course_assessments, name='get_course_assessments'),

]