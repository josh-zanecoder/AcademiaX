from rest_framework import serializers
from .models import Student, UserProfile, Course, Teacher
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User as DjangoUser
import json


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'username', 'email', 'password', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}  # Password will not be included in responses
        }

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Nested serializer for user details
    
    class Meta:
        model = Student
        fields = ['id', 'user', 'first_name', 'last_name']

# For creating/updating students with user information
class StudentCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'username', 'email', 'password']

    def create(self, validated_data):
        # Extract user data
        username = validated_data.pop('username')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        
        # Create Django User
        user = DjangoUser.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create UserProfile
        UserProfile.objects.create(
            user=user,
            role='student'
        )
        
        # Create student profile
        student = Student.objects.create(user=user, **validated_data)
        return student

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    remember = serializers.BooleanField(default=False)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        # Use Django's built-in authenticate
        user = authenticate(username=username, password=password)
        
        if user is None:
            raise serializers.ValidationError({
                'non_field_errors': ['Invalid username or password']
            })
            
        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': ['Account is inactive']
            })

        # First check if user is superuser
        if user.is_superuser:
            attrs['user'] = user
            attrs['is_superuser'] = True
            return attrs

        # If not superuser, check if they're a student
        try:
            student = user.student
            if not hasattr(user, 'student'):
                raise serializers.ValidationError({
                    'non_field_errors': ['Access denied. Invalid account type.']
                })
            attrs['user'] = user
            attrs['is_superuser'] = False
            return attrs
        except (Student.DoesNotExist, AttributeError):
            raise serializers.ValidationError({
                'non_field_errors': ['Access denied. Student login only.']
            })

        return attrs 

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'first_name', 'last_name']



# Add TeacherListSerializer
class TeacherListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ['id', 'first_name', 'last_name']

class TeacherCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    course_ids = serializers.CharField(required=False)
    is_active = serializers.BooleanField(default=True)

    def validate_username(self, value):
        if DjangoUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        if DjangoUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def create(self, validated_data):
        try:
            # Parse course_ids from string
            course_ids_str = validated_data.pop('course_ids', '[]')
            course_ids = json.loads(course_ids_str)
            
            # Get the plain password before hashing
            plain_password = validated_data['password']
            
            # Create user
            user = DjangoUser.objects.create_user(
                username=validated_data['username'],
                email=validated_data['email'],
                password=validated_data['password'],
                is_active=True
            )
            
            # Create UserProfile with plain password
            UserProfile.objects.create(
                user=user,
                role='teacher',
                plain_password=plain_password
            )
            
            # Create Teacher
            teacher = Teacher.objects.create(
                user=user,
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                profile_picture=validated_data.get('profile_picture'),
                is_active=True
            )

            # Assign courses
            if course_ids:
                courses = Course.objects.filter(uid__in=course_ids)
                for course in courses:
                    course.teachers.add(teacher)

            return teacher
            
        except Exception as e:
            # If anything fails, cleanup
            if 'user' in locals():
                user.delete()
            raise serializers.ValidationError(str(e))

class TeacherUpdateSerializer(serializers.Serializer):

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    course_ids = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_username(self, value):
        instance = self.instance
        if Teacher.objects.exclude(id=instance.id).filter(user__username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        instance = self.instance
        if Teacher.objects.exclude(id=instance.id).filter(user__email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def update(self, instance, validated_data):
        try:
            # Update user information
            user = instance.user
            user.username = validated_data.get('username', user.username)
            user.email = validated_data.get('email', user.email)
            
            # Update active status if provided
            if 'is_active' in validated_data:
                user.is_active = validated_data['is_active']
                instance.is_active = validated_data['is_active']
            
            user.save()

            # Update teacher information
            instance.first_name = validated_data.get('first_name', instance.first_name)
            instance.last_name = validated_data.get('last_name', instance.last_name)

            # Update profile picture if provided
            if 'profile_picture' in validated_data:
                instance.profile_picture = validated_data['profile_picture']

            instance.save()

            # Update courses if provided
            if 'course_ids' in validated_data:
                course_ids = json.loads(validated_data['course_ids'])
                courses = Course.objects.filter(uid__in=course_ids)
                instance.courses_teaching.set(courses)

            return instance
            
        except Exception as e:
            raise serializers.ValidationError(str(e)) 
        






class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['uid', 'name', 'category', 'description', 'teachers', 'created_at']
        read_only_fields = ['uid', 'created_at']

    def update(self, instance, validated_data):
        teachers = validated_data.pop('teachers', None)
        
        # Update the basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update teachers if provided
        if teachers is not None:
            instance.teachers.set(teachers)
        
        return instance 