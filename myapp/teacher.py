from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Course, Teacher, UserProfile, Lesson, LessonResource, Assessment, AssessmentScore, Student, AssessmentSubmission
from .serializers import (
    CourseSerializer,
    TeacherUpdateSerializer,
    TeacherCreateSerializer,
    TeacherListSerializer,
    LessonSerializer,
    AssessmentSerializer,
    AssessmentScoreSerializer
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


@api_view(['GET'])
def get_course(request, course_uid):
    try:
        # Use select_related to optimize the query
        course = Course.objects.select_related(
            'created_by'
        ).prefetch_related(
            'teachers',
            'students',
            'lessons'
        ).get(
            uid=course_uid,
            teachers__id=request.user.teacher.id
        )
        
        # Prepare response data without additional queries
        response_data = {
            'status': 'success',
            'course': {
                'uid': str(course.uid),
                'name': course.name,
                'category': course.category,
                'description': course.description,
                'image': course.image.url if course.image else None,
                'students_count': course.students.count(),  # Count is already cached due to prefetch
                'lessons_count': course.lessons.count()     # Count is already cached due to prefetch
            }
        }
        
        return Response(response_data)
    except Course.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error fetching course: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Failed to fetch course details'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_teacher_course(request, course_id):
    try:
        # Get the course using the correct ManyToManyField name 'teachers'
        course = Course.objects.get(
            uid=course_id,
            teachers__id=request.user.teacher.id  # Use the teacher's ID for filtering
        )
        
        return Response({
            'status': 'success',
            'course': {
                'uid': str(course.uid),
                'name': course.name,
                'category': course.category,
                'description': course.description,
                'image': course.image.url if course.image else None
            }
        })
    except Course.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error fetching course: {str(e)}")  # Debug log
        return Response({
            'status': 'error',
            'message': 'Failed to fetch course details'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def create_course(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        
        # Create course with the authenticated user as created_by
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            # Save course with the authenticated user
            course = serializer.save(created_by=request.user)
            # Add the teacher to the teachers M2M field
            course.teachers.add(teacher)
            
            return Response({
                'status': 'success',
                'message': 'Course created successfully',
                'course': CourseSerializer(course).data
            })
        return Response({
            'status': 'error',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Teacher.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Teacher profile not found.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error creating course: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def update_course(request, course_uid):
    try:
        # Get the course and verify teacher has access
        course = Course.objects.get(
            uid=course_uid,
            teachers__id=request.user.teacher.id
        )
        
        # Print request data for debugging
        print("Request data:", request.data)
        print("Request FILES:", request.FILES)
        
        # Prepare data for serializer
        data = {
            'name': request.data.get('name'),
            'category': request.data.get('category'),
            'description': request.data.get('description'),
        }
        
        # Handle image upload
        if 'image' in request.FILES:
            data['image'] = request.FILES['image']
        
        serializer = CourseSerializer(course, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Course updated successfully',
                'course': serializer.data
            })
        
        print("Serializer errors:", serializer.errors)  # Debug log
        return Response({
            'status': 'error',
            'errors': serializer.errors,
            'message': 'Validation failed'
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Course.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error updating course: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to update course: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def course_assessment(request, course_uid):
    course = get_object_or_404(Course, uid=course_uid)
    
    # Verify teacher has access to this course
    if request.user.teacher not in course.teachers.all():
        raise PermissionDenied
    
    context = {
        'course': course,
        'total_students': course.students.count(),
        'total_lessons': course.lessons.count(),
    }
    
    return render(request, 'teacher/course_assessment.html', context)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def create_assessment(request):
    try:
        course = get_object_or_404(Course, uid=request.data.get('course'), teachers__id=request.user.teacher.id)
        
        # Prepare data for serializer
        data = {
            'course': course.id,
            'title': request.data.get('title'),
            'description': request.data.get('description'),
            'type': request.data.get('type'),
            'link': request.data.get('link'),
            'max_score': request.data.get('max_score'),
            'due_date': request.data.get('due_date'),
            'allow_submissions': request.data.get('allow_submissions', True),
        }
        
        # Handle instructions file
        if 'instructions_file' in request.FILES:
            data['instructions_file'] = request.FILES['instructions_file']
        
        serializer = AssessmentSerializer(data=data)
        if serializer.is_valid():
            assessment = serializer.save()
            return Response({
                'status': 'success',
                'message': 'Assessment created successfully',
                'assessment': serializer.data
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        print(f"Error creating assessment: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_assessment(request, assessment_id):
    try:
        assessment = get_object_or_404(Assessment, 
                                     id=assessment_id, 
                                     course__teachers__id=request.user.teacher.id)
        
        serializer = AssessmentSerializer(assessment)
        return Response({
            'status': 'success',
            'assessment': serializer.data
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@parser_classes([MultiPartParser, FormParser])
def update_assessment(request, assessment_id):
    try:
        assessment = get_object_or_404(Assessment, 
                                     id=assessment_id, 
                                     course__teachers__id=request.user.teacher.id)
        
        # Prepare the data
        data = {
            'title': request.data.get('title'),
            'description': request.data.get('description'),
            'type': request.data.get('type'),
            'link': request.data.get('link'),
            'max_score': request.data.get('max_score'),
            'due_date': request.data.get('due_date'),
            'allow_submissions': request.data.get('allow_submissions', True),
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        # Handle file if provided
        if 'instructions_file' in request.FILES:
            data['instructions_file'] = request.FILES['instructions_file']
        
        serializer = AssessmentSerializer(assessment, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Assessment updated successfully',
                'assessment': serializer.data
            })
        
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        print(f"Error updating assessment: {str(e)}")  # Add logging
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_assessment_scores(request, assessment_id):
    try:
        assessment = get_object_or_404(Assessment, 
                                     id=assessment_id, 
                                     course__teachers__id=request.user.teacher.id)
        
        # Get all students in the course
        students = assessment.course.students.all()
        
        # Get existing scores
        scores = AssessmentScore.objects.filter(assessment=assessment)
        scores_dict = {str(score.student.id): score.score for score in scores}  # Convert UUID to string
        
        students_data = [{
            'id': str(student.id),  # Convert UUID to string
            'name': student.user.get_full_name() or student.user.username,
            'score': scores_dict.get(str(student.id))  # Use string UUID as key
        } for student in students]
        
        return Response({
            'status': 'success',
            'max_score': assessment.max_score,
            'students': students_data
        })
    except Exception as e:
        print(f"Error in get_assessment_scores: {str(e)}")  # Debug log
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def update_assessment_scores(request, assessment_id):
    try:
        assessment = get_object_or_404(Assessment, 
                                     id=assessment_id, 
                                     course__teachers__id=request.user.teacher.id)
        
        scores_data = request.data  # Format: {student_id: score}
        
        # Update or create scores
        for student_id, score in scores_data.items():
            try:
                student = Student.objects.get(id=student_id)
                AssessmentScore.objects.update_or_create(
                    assessment=assessment,
                    student=student,
                    defaults={'score': float(score)}
                )
            except Student.DoesNotExist:
                print(f"Student not found: {student_id}")  # Debug log
                continue
            except Exception as e:
                print(f"Error updating score for student {student_id}: {str(e)}")  # Debug log
                continue
        
        return Response({
            'status': 'success',
            'message': 'Scores updated successfully'
        })
    except Exception as e:
        print(f"Error in update_assessment_scores: {str(e)}")  # Debug log
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_assessment_submissions(request, assessment_id):
    try:
        assessment = get_object_or_404(Assessment, 
                                     id=assessment_id, 
                                     course__teachers__id=request.user.teacher.id)
        
        submissions = AssessmentSubmission.objects.filter(assessment=assessment)
        submissions_data = []
        
        for submission in submissions:
            # Get score if exists
            score = AssessmentScore.objects.filter(
                assessment=assessment,
                student=submission.student
            ).first()
            
            submissions_data.append({
                'id': str(submission.id),
                'student_name': submission.student.user.get_full_name() or submission.student.user.username,
                'student_id': str(submission.student.id),
                'status': submission.status,
                'submission_date': submission.submission_date,
                'file_url': request.build_absolute_uri(submission.submitted_file.url) if submission.submitted_file else None,
                'comments': submission.comments,
                'score': score.score if score else None,
                'feedback': score.feedback if score else None,
                'is_late': submission.submission_date > assessment.due_date if assessment.due_date else False
            })
        
        return Response({
            'status': 'success',
            'submissions': submissions_data
        })
        
    except Exception as e:
        print(f"Error getting submissions: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def grade_submission(request, assessment_id, submission_id):
    try:
        assessment = get_object_or_404(Assessment, 
                                     id=assessment_id, 
                                     course__teachers__id=request.user.teacher.id)
        submission = get_object_or_404(AssessmentSubmission, 
                                     id=submission_id, 
                                     assessment=assessment)
        
        score = float(request.data.get('score', 0))
        feedback = request.data.get('feedback', '')
        
        # Validate score
        if score < 0 or score > assessment.max_score:
            return Response({
                'status': 'error',
                'message': f'Score must be between 0 and {assessment.max_score}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update or create score
        assessment_score, created = AssessmentScore.objects.update_or_create(
            assessment=assessment,
            student=submission.student,
            defaults={
                'score': score,
                'feedback': feedback
            }
        )
        
        # Update submission status
        submission.status = 'graded'
        submission.save()
        
        return Response({
            'status': 'success',
            'message': 'Submission graded successfully'
        })
        
    except Exception as e:
        print(f"Error grading submission: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def download_submission(request, submission_id):
    try:
        submission = get_object_or_404(AssessmentSubmission, 
                                     id=submission_id,
                                     assessment__course__teachers__id=request.user.teacher.id)
        
        if not submission.submitted_file:
            return Response({
                'status': 'error',
                'message': 'No file found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        file_path = submission.submitted_file.path
        if default_storage.exists(file_path):
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{submission.submitted_file.name}"'
            return response
            
        return Response({
            'status': 'error',
            'message': 'File not found'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        print(f"Error downloading submission: {str(e)}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_course_assessments(request, course_uid):
    try:
        course = get_object_or_404(Course, uid=course_uid, teachers__id=request.user.teacher.id)
        assessments = Assessment.objects.filter(course=course)
        serializer = AssessmentSerializer(assessments, many=True)
        
        return Response({
            'status': 'success',
            'assessments': serializer.data
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

