from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, Student
from .serializers import StudentCreateSerializer

class UserModelTest(TestCase):
    def setUp(self):
        print("\nTesting User Model...")
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            role="student"
        )

    def test_user_creation(self):
        print("✓ Testing user creation")
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.role, "student")

    def test_user_str_method(self):
        print("✓ Testing user string representation")
        self.assertEqual(str(self.user), "testuser")

class StudentModelTest(TestCase):
    def setUp(self):
        print("\nTesting Student Model...")
        self.user = User.objects.create(
            username="studentuser",
            email="student@example.com",
            password="testpass123",
            role="student"
        )
        self.student = Student.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe"
        )

    def test_student_creation(self):
        print("✓ Testing student creation")
        self.assertEqual(self.student.first_name, "John")
        self.assertEqual(self.student.last_name, "Doe")
        self.assertEqual(self.student.user.username, "studentuser")

    def test_student_str_method(self):
        print("✓ Testing student string representation")
        self.assertEqual(str(self.student), "John Doe")

class RegistrationViewTest(APITestCase):
    def setUp(self):
        print("\nTesting Registration API...")
        self.client = Client()
        self.register_url = reverse('register_student')
        self.valid_payload = {
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'password': 'newpass123',
            'first_name': 'Jane',
            'last_name': 'Smith'
        }

    def test_valid_registration(self):
        print("✓ Testing valid student registration")
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertTrue(User.objects.filter(username='newstudent').exists())

    def test_invalid_registration_duplicate_username(self):
        print("✓ Testing duplicate username registration")
        # Create first user
        self.client.post(self.register_url, self.valid_payload, format='json')
        
        # Try to create another user with same username
        response = self.client.post(self.register_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_registration_missing_fields(self):
        print("✓ Testing registration with missing fields")
        invalid_payload = {
            'username': 'newstudent',
            'email': 'newstudent@example.com'
            # missing password, first_name, last_name
        }
        response = self.client.post(
            self.register_url,
            invalid_payload,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class SerializerTest(TestCase):
    def setUp(self):
        print("\nTesting Serializers...")
        self.valid_data = {
            'username': 'testserializer',
            'email': 'serializer@test.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'Serializer'
        }

    def test_valid_serializer(self):
        print("✓ Testing valid serializer data")
        serializer = StudentCreateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_serializer(self):
        print("✓ Testing invalid serializer data")
        invalid_data = self.valid_data.copy()
        invalid_data.pop('email')  # Remove required field
        serializer = StudentCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

class TemplateTest(TestCase):
    def setUp(self):
        print("\nTesting Templates...")
        self.client = Client()

    def test_index_page_load(self):
        print("✓ Testing index page load")
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_registration_page_load(self):
        print("✓ Testing registration page load")
        response = self.client.get(reverse('registration'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'students/registration.html')
