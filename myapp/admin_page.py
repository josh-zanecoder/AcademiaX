from django.shortcuts import render, redirect
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from .serializers import CourseSerializer, TeacherUpdateSerializer, TeacherCreateSerializer
from .models import Course, Teacher
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from .models import UserProfile
import traceback  # Add this import
import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse  # Add this import
from django.db import transaction  # Add this import

def is_superuser(user):
    return user.is_superuser





@login_required
def manage_teachers(request):
    teachers = Teacher.objects.all().order_by('first_name')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        teachers_data = [{
            'id': teacher.id,
            'first_name': teacher.first_name,
            'last_name': teacher.last_name,
            'email': teacher.user.email if teacher.user else '',
        } for teacher in teachers]
        return JsonResponse({'teachers': teachers_data}, safe=False)
    
    # Return HTML for normal requests
    return render(request, 'admin/manage_teachers.html', {
        'teachers': teachers,
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_teacher(request, teacher_id=None):
    try:
        # If teacher_id is provided, return single teacher
        if teacher_id:
            teacher = get_object_or_404(Teacher, id=teacher_id)
            data = {
                'id': teacher.id,
                'username': teacher.user.username,
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'email': teacher.user.email if teacher.user else '',
                'profile_picture': teacher.profile_picture.url if teacher.profile_picture else None,
                'courses_teaching': [str(course.uid) for course in teacher.courses_teaching.all()],
                'is_active': teacher.is_active
            }
            return Response(data)
        
        # If no teacher_id, return all teachers
        teachers = Teacher.objects.all().order_by('first_name')
        data = [{
            'id': teacher.id,
            'first_name': teacher.first_name,
            'last_name': teacher.last_name,
            'email': teacher.user.email if teacher.user else '',
            'profile_picture': teacher.profile_picture.url if teacher.profile_picture else None,
            'is_active': teacher.is_active
        } for teacher in teachers]
        return Response(data)
        
    except Exception as e:
        print(f"Error in get_teacher: {str(e)}")  # Add logging
        return Response({
            'error': 'Failed to fetch teacher(s)',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_teacher(request):
    try:
        print("Request Files:", request.FILES)  # Debug print
        print("Request Data:", request.data)    # Debug print
        
        # Convert request.data to mutable dict if it's not already
        data = request.data.copy() if hasattr(request.data, 'copy') else request.data
        
        # Handle course_ids if present
        if 'course_ids' in data:
            try:
                if isinstance(data['course_ids'], str):
                    json.loads(data['course_ids'])  # Validate JSON
            except json.JSONDecodeError as e:
                print("JSON Error:", str(e))
                return Response({
                    'error': 'Invalid course_ids format',
                    'detail': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        # Handle profile picture
        if 'profile_picture' in request.FILES:
            data['profile_picture'] = request.FILES['profile_picture']

        serializer = TeacherCreateSerializer(data=data)
        
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        teacher = serializer.save()
        
        return Response({
            'message': 'Teacher created successfully',
            'teacher': {
                'id': teacher.id,
                'first_name': teacher.first_name,
                'last_name': teacher.last_name,
                'username': teacher.user.username,
                'email': teacher.user.email,
                'profile_picture': teacher.profile_picture.url if teacher.profile_picture else None
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print("Full error:")
        print(traceback.format_exc())
        return Response({
            'error': 'Failed to create teacher',
            'detail': str(e),
            'trace': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_teacher(request, teacher_id):

    try:
        teacher = get_object_or_404(Teacher, id=teacher_id)
        serializer = TeacherUpdateSerializer(teacher, data=request.data, context={'request': request})
        
        if serializer.is_valid():
            teacher = serializer.save()
            return Response({
                'message': 'Teacher updated successfully',
                'teacher': {
                    'id': teacher.id,
                    'first_name': teacher.first_name,
                    'last_name': teacher.last_name,
                    'username': teacher.user.username,
                    'email': teacher.user.email,
                    'profile_picture': teacher.profile_picture.url if teacher.profile_picture else None
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        return Response({
            'error': 'Failed to update teacher',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_teacher(request, teacher_id):
    try:
        teacher = get_object_or_404(Teacher, id=teacher_id)
        
        # Delete profile picture if exists
        if teacher.profile_picture:
            teacher.profile_picture.delete(save=False)
        
        # Delete user profile
        UserProfile.objects.filter(user=teacher.user).delete()
        
        # Delete teacher and associated user
        teacher.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Teacher.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error deleting teacher: {str(e)}")  # For debugging
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)






@api_view(['GET'])
@permission_classes([IsAdminUser])
def manage_courses(request):
    courses = Course.objects.all().order_by('-created_at')
    teachers = Teacher.objects.all().order_by('first_name')
    return render(request, 'admin/manage_courses.html', {
        'courses': courses,
        'teachers': teachers,
    })

@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_courses(request):
    courses = Course.objects.all()
    serializer = CourseSerializer(courses, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_course(request):
    try:
        # Extract data from request
        teacher_ids = request.data.get('teacher_ids', [])
        
        data = {
            'name': request.data.get('name'),
            'category': request.data.get('category'),
            'description': request.data.get('description'),
            'teachers': teacher_ids  # Make sure this matches your serializer field
        }
        
        print("Received data:", data)  # Debug print
        print("Teacher IDs:", teacher_ids)  # Debug print
        
        serializer = CourseSerializer(data=data)
        if serializer.is_valid():
            course = serializer.save(created_by=request.user)
            # Explicitly set the teachers
            course.teachers.set(teacher_ids)
            
            # Re-serialize the course with the updated teachers
            updated_serializer = CourseSerializer(course)
            return Response(updated_serializer.data, status=status.HTTP_201_CREATED)
        
        print("Validation errors:", serializer.errors)  # Debug print
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        print("Error creating course:", str(e))
        return Response({
            'error': 'Failed to create course',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAdminUser])
def update_course(request, course_id):
    try:
        course = get_object_or_404(Course, uid=course_id)
        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': 'Failed to update course',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_course(request, course_id):
    try:
        course = get_object_or_404(Course, uid=course_id)
        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({
            'error': 'Failed to delete course',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)









