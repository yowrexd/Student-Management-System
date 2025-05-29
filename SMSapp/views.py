from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
from .models import Subject, Activity, StudentSubjectEnrollment, Course
from .serializers import (
    SubjectSerializer, ActivitySerializer, 
    StudentSubjectEnrollmentSerializer
)

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

def subject_info(request, subject_code):
    subject = Subject.objects.get(subject_code=subject_code)
    activities = Activity.objects.filter(subject=subject)
    enrolled_students = StudentSubjectEnrollment.objects.filter(subject=subject).select_related('student')
    
    context = {
        'subject': subject,
        'activities': activities,
        'enrolled_students': enrolled_students,
    }
    return render(request, 'subjectinfo.html', context)

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.filter(archive=False)
    serializer_class = SubjectSerializer
    lookup_field = 'subject_code'

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Subject created successfully',
                    'data': serializer.data
                })
            return JsonResponse({
                'status': 'error',
                'message': serializer.errors
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                self.perform_update(serializer)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Subject updated successfully',
                    'data': serializer.data
                })
            return JsonResponse({
                'status': 'error',
                'message': serializer.errors
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.archive = True  # Soft delete
            instance.save()
            return JsonResponse({
                'status': 'success',
                'message': 'Subject deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    @action(detail=True, methods=['get'])
    def info(self, request, subject_code=None):
        try:
            subject = self.get_object()
            activities = Activity.objects.filter(subject=subject)
            enrollments = StudentSubjectEnrollment.objects.filter(subject=subject).select_related('student')
            
            return JsonResponse({
                'status': 'success',
                'data': {
                    'subject': SubjectSerializer(subject).data,
                    'activities': ActivitySerializer(activities, many=True).data,
                    'enrollments': StudentSubjectEnrollmentSerializer(enrollments, many=True).data
                }
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    lookup_field = 'activity_id'

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return JsonResponse({
                'status': 'success',
                'data': {
                    'activity_id': instance.activity_id,
                    'activity_type': instance.activity_type,
                    'activity_name': instance.activity_name,
                    'total_items': instance.total_items,
                    'subject': instance.subject.subject_code
                }
            })
        except Activity.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Activity not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                return JsonResponse({
                    'status': 'success',
                    'data': serializer.data
                })
            return JsonResponse({
                'status': 'error',
                'message': serializer.errors
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response({
                    'status': 'success',
                    'message': 'Activity updated successfully!',
                    'data': serializer.data
                })
            return Response({
                'status': 'error',
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            return JsonResponse({
                'status': 'success',
                'message': 'Activity deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    def get_queryset(self):
        queryset = Activity.objects.all()
        subject_code = self.request.query_params.get('subject', None)
        if subject_code:
            queryset = queryset.filter(subject__subject_code=subject_code)
        return queryset

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = StudentSubjectEnrollment.objects.all()
    serializer_class = StudentSubjectEnrollmentSerializer

    def get_queryset(self):
        queryset = StudentSubjectEnrollment.objects.all()
        subject_code = self.request.query_params.get('subject', None)
        if subject_code:
            queryset = queryset.filter(subject__subject_code=subject_code)
        return queryset

