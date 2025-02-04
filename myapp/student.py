from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import StudentCreateSerializer, LoginSerializer, TeacherListSerializer, CourseSerializer, StudentSerializer
from django.contrib.auth import login, authenticate, logout
import logging
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Student, Teacher, Course
from rest_framework.permissions import IsAdminUser
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages



@login_required
def student_page(request):
    try:
        student = Student.objects.get(user=request.user)
        
        # Get all courses
        all_courses = Course.objects.all()
        # Get courses where student is not enrolled
        available_courses = Course.objects.exclude(students=student)
        
        context = {
            'student': student,
            'user': request.user,
            'available_courses': available_courses,
        }
        
        return render(request, 'student/student_page.html', context)
    except Student.DoesNotExist:
        return redirect('login')

@api_view(['POST'])
def enroll_course(request, course_uid):
    try:
        student = Student.objects.get(user=request.user)
        course = get_object_or_404(Course, uid=course_uid)
        
        # Check if already enrolled
        if student in course.students.all():
            return Response({
                'status': 'error',
                'message': 'You are already enrolled in this course.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Add student to course
        course.students.add(student)
        
        # Serialize the updated data
        course_data = CourseSerializer(course).data
        student_data = StudentSerializer(student).data
        
        return Response({
            'status': 'success',
            'message': f'Successfully enrolled in {course.name}!',
            'course': course_data,
            'student': student_data,
            'enrolled_count': student.enrolled_courses.count()
        }, status=status.HTTP_200_OK)
        
    except Student.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Student profile not found.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def student_course_detail(request, uid):
    try:
        student = Student.objects.get(user=request.user)
        course = get_object_or_404(Course, uid=uid)
        
        # Check if student is enrolled in this course
        if student not in course.students.all():
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({
                    'status': 'error',
                    'message': 'You are not enrolled in this course.'
                }, status=403)
            messages.error(request, 'You are not enrolled in this course.')
            return redirect('student_page')

        if request.headers.get('Accept') == 'application/json':
            # Return JSON response for API requests
            course_data = CourseSerializer(course).data
            student_data = StudentSerializer(student).data
            
            return JsonResponse({
                'status': 'success',
                'course': course_data,
                'student': student_data
            })
        else:
            # Return HTML response for browser requests
            context = {
                'student': student,
                'course': course,
                'user': request.user,
            }
            return render(request, 'student/student_course.html', context)
        
    except Student.DoesNotExist:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'status': 'error',
                'message': 'Student profile not found.'
            }, status=404)
        return redirect('login')
    except Exception as e:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
        messages.error(request, 'An error occurred.')
        return redirect('student_page')

@api_view(['POST'])
def unenroll_course(request, course_uid):
    try:
        student = Student.objects.get(user=request.user)
        course = get_object_or_404(Course, uid=course_uid)
        
        # Check if student is enrolled
        if student not in course.students.all():
            return Response({
                'status': 'error',
                'message': 'You are not enrolled in this course.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove student from course
        course.students.remove(student)
        
        return Response({
            'status': 'success',
            'message': f'Successfully unenrolled from {course.name}',
            'enrolled_count': student.enrolled_courses.count()
        }, status=status.HTTP_200_OK)
        
    except Student.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Student profile not found.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)