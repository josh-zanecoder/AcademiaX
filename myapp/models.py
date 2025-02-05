from django.db import models
from django.contrib.auth.models import User as DjangoUser  # Import Django's default User
import uuid

# Extend Django's User model with a OneToOneField
class UserProfile(models.Model):
    user = models.OneToOneField(DjangoUser, on_delete=models.CASCADE)
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    plain_password = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

class Student(models.Model):
    user = models.OneToOneField(DjangoUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Teacher(models.Model):
    user = models.OneToOneField(
        DjangoUser, 
        on_delete=models.CASCADE,
        related_name='teacher'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='teacher_profiles/', null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def delete(self, *args, **kwargs):
        # Store user reference
        user = self.user
        
        # Delete profile picture if exists
        if self.profile_picture:
            self.profile_picture.delete(save=False)
            
        # Delete the teacher instance first
        super().delete(*args, **kwargs)
        
        # Then delete the user
        user.delete()

class Course(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(
        upload_to='course_images/',
        blank=True,
        null=True,
        help_text="Course cover image"
    )
    teachers = models.ManyToManyField(
        Teacher, 
        related_name='courses_teaching',
        blank=True
    )
    students = models.ManyToManyField(
        Student, 
        related_name='enrolled_courses',
        blank=True
    )
    created_by = models.ForeignKey(
        DjangoUser,
        on_delete=models.CASCADE,
        related_name='courses_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"/courses/{self.uid}/"

    def delete(self, *args, **kwargs):
        # Delete the image file when deleting the course
        if self.image:
            self.image.delete(save=False)
        super().delete(*args, **kwargs)

class Lesson(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    created_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, related_name='lessons_created', null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title

class LessonResource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('file', 'File'),
        ('link', 'Link')
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='resources')
    type = models.CharField(max_length=10, choices=RESOURCE_TYPE_CHOICES)
    file = models.FileField(
        upload_to='lesson_files/',
        null=True,
        blank=True,
        help_text="Upload lesson materials (PDF, DOC, PPT, etc.)"
    )
    url = models.URLField(
        null=True,
        blank=True,
        help_text="URLs will be automatically extracted from the description"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} resource for {self.lesson.title}"

    def delete(self, *args, **kwargs):
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

    class Meta:
        ordering = ['created_at']

class Assessment(models.Model):
    ASSESSMENT_TYPES = [
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('exam', 'Exam'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=20, choices=ASSESSMENT_TYPES)
    link = models.URLField(help_text="Google Forms link", blank=True)
    max_score = models.PositiveIntegerField()
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New fields for file handling
    instructions_file = models.FileField(upload_to='assessment_instructions/', null=True, blank=True)
    allow_submissions = models.BooleanField(default=True)
    submission_folder = models.CharField(max_length=255, blank=True, help_text="Google Drive folder ID for submissions")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.course.name}"

class AssessmentSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assessment_submissions')
    submitted_file = models.FileField(upload_to='assessment_submissions/')
    submission_date = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)
    status = models.CharField(max_length=20, default='submitted', 
                            choices=[('draft', 'Draft'),
                                   ('submitted', 'Submitted'),
                                   ('late', 'Late'),
                                   ('graded', 'Graded')])

    class Meta:
        unique_together = ['assessment', 'student']
        ordering = ['-submission_date']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assessment.title}"

class AssessmentScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='scores')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assessment_scores')
    score = models.FloatField()
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['assessment', 'student']
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assessment.title}"