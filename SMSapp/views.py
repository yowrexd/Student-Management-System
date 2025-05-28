from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from .serializers import *
from .models import *
from django.http import JsonResponse
import json

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

    @action(detail=True, methods=['get'])
    def subjects(self, request, pk=None):
        student = self.get_object()
        enrollments = StudentSubjectEnrollment.objects.filter(student=student)
        subjects = [enrollment.subject for enrollment in enrollments]
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def grades(self, request, pk=None):
        student = self.get_object()
        subject_code = request.query_params.get('subject', None)
        if subject_code:
            grades = Grade.objects.filter(student=student, activity__subject_id=subject_code)
            serializer = GradeSerializer(grades, many=True)
            return Response(serializer.data)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        print("=== COURSE CREATE VIEW CALLED ===")
        print("Request method:", request.method)
        print("Request content type:", request.content_type)
        print("Received data:", request.data)
        # Explicitly check for blank course_abv
        course_abv = request.data.get('course_abv', '').strip()
        course_name = request.data.get('course_name', '').strip()
        if not course_abv:
            print("Validation error: course_abv is blank")
            return Response({'error': {'course_abv': ['Course Code is required.']}}, status=status.HTTP_400_BAD_REQUEST)
        if Course.objects.filter(course_abv=course_abv).exists():
            print("Validation error: duplicate course_abv")
            return Response({'error': {'course_abv': ['Course Code already exists.']}}, status=status.HTTP_400_BAD_REQUEST)
        # The serializer is used here for validation and saving
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            print("Saved course:", instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("Validation errors:", serializer.errors)
            return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            print("Update validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Update exception:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer

# Regular views for templates
def index(request):
    return render(request, 'index.html')

def student_list(request):
    students = Student.objects.all()
    courses = Course.objects.all()
    return render(request, 'students.html', {
        'students': students,
        'courses': courses
    })

def student_detail(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    return render(request, 'student_detail.html', {'student': student})

def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses.html', {'courses': courses})

def subject_list(request):
    subjects = Subject.objects.all()
    courses = Course.objects.all()

    # Add sample data if no subjects exist
    if not subjects:
        sample_subjects = [
            {
                'subject_code': 'COMP101',
                'subject_title': 'Introduction to Programming',
                'course_name': 'BSIT',
                'semester': '1st Semester',
                'school_year': '2023-2024',
                'year_level': 1,
                'section': 'A',
                'theme_color': '#1B5131'
            },
            {
                'subject_code': 'MATH201',
                'subject_title': 'Calculus 1',
                'course_name': 'BSIT',
                'semester': '1st Semester',
                'school_year': '2023-2024',
                'year_level': 2,
                'section': 'B',
                'theme_color': '#2d724a'
            },
            {
                'subject_code': 'ENG101',
                'subject_title': 'Technical Writing',
                'course_name': 'BSIT',
                'semester': '1st Semester',
                'school_year': '2023-2024',
                'year_level': 1,
                'section': 'C',
                'theme_color': '#34a853'
            }
        ]
        
        return render(request, 'subjects.html', {
            'sample_subjects': sample_subjects,
            'courses': courses
        })

    return render(request, 'subjects.html', {
        'subjects': subjects,
        'courses': courses
    })

def grade_list(request):
    grades = Grade.objects.all()
    return render(request, 'grades.html', {'grades': grades})

def subject_detail(request, subject_code):
    subject = get_object_or_404(Subject, pk=subject_code)
    activities = Activity.objects.filter(subject=subject)
    return render(request, 'subject_detail.html', {
        'subject': subject,
        'activities': activities
    })