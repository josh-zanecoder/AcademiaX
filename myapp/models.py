from django.db import models

# Create your models here.

class User(models.Model):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    
    id = models.AutoField(primary_key=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.username

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
