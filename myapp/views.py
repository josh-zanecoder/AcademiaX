from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import StudentCreateSerializer

# Create your views here.
def index(request):
    return render(request, 'index.html')

def registration(request):
    return render(request, 'students/registration.html')

@api_view(['POST'])
def register_student(request):
    serializer = StudentCreateSerializer(data=request.data)
    if serializer.is_valid():
        try:
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Registration successful!',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    return Response({
        'status': 'error',
        'message': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

