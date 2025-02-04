from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Course, Teacher, UserProfile, Lesson, LessonResource
from .serializers import (
    CourseSerializer,
    TeacherUpdateSerializer,
    TeacherCreateSerializer,
    TeacherListSerializer,
    LessonSerializer
)

import logging
import re

logger = logging.getLogger(__name__)


@login_required
def teacher_page(request):
    """Main dashboard view for teachers."""
    if not hasattr(request.user, 'teacher'):
        raise PermissionDenied
    
    teacher = request.user.teacher
    courses = teacher.courses_teaching.all()
    
    context = {
        'total_students': sum(course.students.count() for course in courses),
        'courses': courses,
    }
    
    return render(request, 'teacher/teacher_page.html', context)


@login_required
def teacher_courses(request):
    """View for displaying all courses of a teacher."""
    if not hasattr(request.user, 'teacher'):
        raise PermissionDenied
    
    # Get all courses assigned to the teacher
    courses = request.user.teacher.courses_teaching.all().order_by('-created_at')
    
    # Pagination - 9 courses per page
    paginator = Paginator(courses, 9)
    page = request.GET.get('page')
    courses = paginator.get_page(page)
    
    context = {
        'courses': courses,
    }
    
    return render(request, 'teacher/teacher_courses.html', context)


@login_required
def course_detail(request, uid):
    """View for displaying detailed information about a specific course."""
    course = get_object_or_404(Course, uid=uid)
    
    # Verify teacher has access to this course
    if request.user.teacher not in course.teachers.all():
        raise PermissionDenied
    
    context = {
        'course': course,
        'total_students': course.students.count(),
        'total_lessons': course.lessons.count(),
        'students': course.students.all(),  # Combined from course_students view
    }
    
   
    return render(request, 'teacher/course_detail.html', context)


@login_required
def course_details_api(request, uid):
    """API endpoint for getting course details."""
    try:
        course = get_object_or_404(Course, uid=uid)
        
        # Verify teacher has access to this course
        if request.user.teacher not in course.teachers.all():
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        data = {
            'name': course.name,
            'category': course.category,
            'description': course.description,
            'students_count': course.students.count(),
            'lessons_count': course.lessons.count(),
            'created_at': course.created_at.isoformat(),
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_teachers(request):
    """API endpoint for getting all teachers (admin only)."""
    teachers = Teacher.objects.all()
    serializer = TeacherListSerializer(teachers, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def create_lesson(request, course_uid):
    """Create a new lesson for a course"""
    try:
        course = get_object_or_404(Course, uid=course_uid)
        teacher = request.user.teacher
        
        if teacher not in course.teachers.all():
            return Response(
                {"error": "You don't have permission to add lessons to this course"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create the lesson
        lesson = Lesson.objects.create(
            course=course,
            created_by=teacher,
            title=request.data.get('title', '').strip(),
            description=request.data.get('description', '').strip(),
            order=Lesson.objects.filter(course=course).count()
        )

        # Handle multiple files
        files = request.FILES.getlist('files')
        for file in files:
            LessonResource.objects.create(
                lesson=lesson,
                type='file',
                file=file
            )

        # Extract URLs from description
        urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', lesson.description)
        for url in urls:
            if not url.startswith('http'):
                url = 'http://' + url
            LessonResource.objects.create(
                lesson=lesson,
                type='link',
                url=url
            )

        return Response(
            LessonSerializer(lesson).data,
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        print(f"Error creating lesson: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser])
def lesson_detail(request, course_uid, lesson_uid):
    course = get_object_or_404(Course, uid=course_uid)
    lesson = get_object_or_404(Lesson, uid=lesson_uid, course=course)
    
    if request.user.teacher not in course.teachers.all():
        return Response(
            {"error": "You don't have permission to modify this lesson"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.method == 'GET':
        serializer = LessonSerializer(lesson)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        try:
            # Update basic fields
            lesson.title = request.data.get('title', '').strip()
            lesson.description = request.data.get('description', '').strip()
            lesson.save()
            
            # Handle new files
            files = request.FILES.getlist('files')
            for file in files:
                LessonResource.objects.create(
                    lesson=lesson,
                    type='file',
                    file=file
                )
            
            # Extract new URLs from description
            urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', lesson.description)
            for url in urls:
                if not url.startswith('http'):
                    url = 'http://' + url
                # Only create if URL doesn't exist
                if not LessonResource.objects.filter(lesson=lesson, type='link', url=url).exists():
                    LessonResource.objects.create(
                        lesson=lesson,
                        type='link',
                        url=url
                    )
            
            return Response(LessonSerializer(lesson).data)
            
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    elif request.method == 'DELETE':
        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
def delete_resource(request, resource_id):
    resource = get_object_or_404(LessonResource, id=resource_id)
    
    if request.user.teacher not in resource.lesson.course.teachers.all():
        return Response(
            {"error": "You don't have permission to delete this resource"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    resource.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def reorder_lessons(request, course_uid):
    """Reorder lessons in a course"""
    course = get_object_or_404(Course, uid=course_uid)
    
    if request.user.teacher not in course.teachers.all():
        return Response(
            {"error": "You don't have permission to reorder lessons"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    lesson_orders = request.data.get('lesson_orders', [])
    
    for item in lesson_orders:
        lesson = get_object_or_404(Lesson, uid=item['uid'], course=course)
        lesson.order = item['order']
        lesson.save()
    
    return Response({"message": "Lessons reordered successfully"})