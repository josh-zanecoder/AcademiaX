from django.test import TestCase, Client
from django.urls import reverse





class ViewsTestCase(TestCase):
    def setUp(self):
        # Initialize the test client
        self.client = Client()
    
    def test_index_view(self):
        # Test the index view
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
    
    def test_registration_view(self):
        # Test the registration view
        response = self.client.get(reverse('registration'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'students/registration.html')
