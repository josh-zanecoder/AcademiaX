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



