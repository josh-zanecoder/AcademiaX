from rest_framework import serializers
from .models import User, Student

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
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
        
        # Create user
        user = User.objects.create(
            username=username,
            email=email,
            password=password,  # In production, use set_password() for proper hashing
            role='student'
        )
        
        # Create student profile
        student = Student.objects.create(user=user, **validated_data)
        return student 