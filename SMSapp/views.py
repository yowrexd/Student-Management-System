from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Subject, Course
from .serializers import SubjectSerializer, CourseSerializer

def index(request):
    return render(request, 'index.html')

def subjects(request):
    subjects = Subject.objects.filter(archive=False).select_related('course')
    courses = Course.objects.all()
    context = {
        'subjects': subjects,
        'courses': courses,
    }
    return render(request, 'subjects.html', context)

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.filter(archive=False)
    serializer_class = SubjectSerializer
    lookup_field = 'subject_code'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                'status': 'success',
                'message': 'Subject added successfully!',
                'data': serializer.data
            })
        return Response({
            'status': 'error',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                'status': 'success',
                'message': 'Subject updated successfully!',
                'data': serializer.data
            })
        return Response({
            'status': 'error',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({
                'status': 'success',
                'message': 'Subject deleted successfully!'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

