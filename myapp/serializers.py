from rest_framework import serializers
from .models import Student, UserProfile, Course, Teacher, Lesson, LessonResource, Assessment, AssessmentScore
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User as DjangoUser
import json

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['user', 'role']

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
            attrs['user_type'] = 'admin'
            return attrs

        # Check if they're a teacher
        try:
            teacher = user.teacher
            attrs['user'] = user
            attrs['user_type'] = 'teacher'
            return attrs
        except (Teacher.DoesNotExist, AttributeError):
            # If not a teacher, check if they're a student
            try:
                student = user.student
                attrs['user'] = user
                attrs['user_type'] = 'student'
                return attrs
            except (Student.DoesNotExist, AttributeError):
                raise serializers.ValidationError({
                    'non_field_errors': ['Access denied. Invalid account type.']
                })

        return attrs

class TeacherSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')
    
    class Meta:
        model = Teacher
        fields = ['first_name', 'last_name', 'email', 'profile_picture']



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
    password = serializers.CharField(required=False, write_only=True, allow_blank=True)

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

    def validate_password(self, value):
        if value and len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value

    def update(self, instance, validated_data):
        try:
            # Update user information
            user = instance.user
            user.username = validated_data.get('username', user.username)
            user.email = validated_data.get('email', user.email)
            
            # Handle password update if provided
            password = validated_data.get('password')
            if password:
                user.set_password(password)
            
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
                # Delete old profile picture if it exists
                if instance.profile_picture:
                    try:
                        instance.profile_picture.delete(save=False)
                    except Exception:
                        pass  # Ignore errors if file doesn't exist
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
        fields = ['uid', 'name', 'category', 'description', 'image', 'created_by', 'teachers']
        read_only_fields = ['uid', 'created_by']

class LessonResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonResource
        fields = ['id', 'type', 'file', 'url', 'created_at']
        read_only_fields = ['id', 'created_at']

class LessonSerializer(serializers.ModelSerializer):
    created_by = TeacherSerializer(read_only=True)
    resources = LessonResourceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Lesson
        fields = [
            'uid',
            'title',
            'description',
            'resources',
            'created_by',
            'order',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['uid', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        course = self.context['course']
        teacher = self.context['teacher']
        lesson = Lesson.objects.create(
            course=course,
            created_by=teacher,
            **validated_data
        )
        return lesson 
    



    
class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    enrolled_courses = CourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'user', 'first_name', 'last_name', 'enrolled_courses']

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'course', 'title', 'type', 'link', 'max_score', 'due_date', 'description']
        read_only_fields = ['id']

class AssessmentScoreSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentScore
        fields = ['id', 'assessment', 'student', 'score', 'student_name']
        read_only_fields = ['id']

    def get_student_name(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username
