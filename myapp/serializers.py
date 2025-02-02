from rest_framework import serializers
from .models import Student, UserProfile
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User as DjangoUser


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