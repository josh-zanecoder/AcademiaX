from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import StudentCreateSerializer, LoginSerializer, TeacherListSerializer
from django.contrib.auth import login, authenticate, logout
import logging
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Student, Teacher, Course
from rest_framework.permissions import IsAdminUser
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    return render(request, 'index.html')

def registration(request):
    return render(request, 'registration.html')

def login_page(request):
    return render(request, 'login.html')

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def admin_page(request):
    return render(request, 'admin/admin_page.html', {'user': request.user})

@login_required
def student_page(request):
    try:
        # Get the student profile of the logged-in user
        student = Student.objects.get(user=request.user)
        
        context = {
            'student': student,
            'user': request.user,
            'full_name': f"{student.first_name} {student.last_name}",
            'email': request.user.email,
            'username': request.user.username,
            # Add any other fields you want to display
        }
        
        return render(request, 'student/student_page.html', context)
    except Student.DoesNotExist:
        # Handle case where student profile doesn't exist
        return redirect('login')

@api_view(['POST'])
def register_student(request):
    serializer = StudentCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Registration successful!',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        'status': 'error',
        'message': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        remember = serializer.validated_data.get('remember', False)
        user_type = serializer.validated_data.get('user_type')
        
        login(request, user)
        
        if not remember:
            request.session.set_expiry(0)
        
        # Base response data
        response_data = {
            'status': 'success',
            'message': 'Login successful',
            'user': {
                'username': user.username,
                'email': user.email,
            }
        }

        # Different response based on user type
        if user_type == 'admin':
            response_data['redirect'] = '/admin_page/'
            response_data['user']['is_superuser'] = True
        
        elif user_type == 'teacher':
            response_data['redirect'] = '/teacher/'
            response_data['user'].update({
                'first_name': user.teacher.first_name,
                'last_name': user.teacher.last_name,
                'is_teacher': True
            })
        
        else:  # student
            response_data['redirect'] = '/student_page/'
            response_data['user'].update({
                'first_name': user.student.first_name,
                'last_name': user.student.last_name,
                'is_student': True
            })

        return Response(response_data)
    
    return Response({
        'status': 'error',
        'message': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@login_required
def logout_user(request):
    logout(request)
    return redirect('index')  # Redirect to home page after logout
