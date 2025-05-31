from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from rest_framework.decorators import api_view
from .models import Subject, Activity, Grade, Student, Course

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models  # Add this import
from .models import Subject, Activity, StudentSubjectEnrollment, Course, Student, Grade
from .serializers import (
    SubjectSerializer, ActivitySerializer, 
    StudentSubjectEnrollmentSerializer, CourseSerializer, StudentSerializer, GradeSerializer
)
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from django.utils import timezone
from django.db.models import Count, Q, OuterRef, Exists

def index(request):
    # Get counts for dashboard
    total_students = Student.objects.count()
    total_courses = Course.objects.count()
    total_subjects = Subject.objects.count()

    # Count activities without grades (pending activities)
    pending_activities = Activity.objects.exclude(
        activity_id__in=Grade.objects.values('activity')
    ).count()

    # Get recent activities without using date_assigned
    recent_activities = Activity.objects.all().order_by('-activity_id')[:5]

    context = {
        'total_students': total_students,
        'total_courses': total_courses,
        'total_subjects': total_subjects,
        'pending_activities': pending_activities,
        'new_students': Student.objects.count(),
        'recent_students': Student.objects.all()[:5],
        'recent_activities': recent_activities,
    }
    
    return render(request, 'index.html', context)

# default view for subjects
def subjects(request):
    subjects = Subject.objects.filter(is_active=True)  # Only show non-archived subjects
    courses = Course.objects.all()
    context = {
        'subjects': subjects,
        'courses': courses,
    }
    return render(request, 'subjects.html', context)

# view for subject details including activities and enrolled students
def subject_info(request, subject_code):
    subject = get_object_or_404(Subject, subject_code=subject_code)
    activities = Activity.objects.filter(subject=subject)
    
    # Count activities that have no grades
    pending_activities = activities.exclude(
        activity_id__in=Grade.objects.values('activity')
    ).count()

    context = {
        'subject': subject,
        'activities': activities,
        'pending_activities': pending_activities,
        'student_courses': Course.objects.all(),
        'student_sections': list(set(Student.objects.values_list('section', flat=True)))
    }
    
    return render(request, 'subjectinfo.html', context)

def student_info(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    enrollments = StudentSubjectEnrollment.objects.filter(student=student).select_related('subject')
    
    context = {
        'student': student,
        'enrollments': enrollments,
    }
    return render(request, 'studentinfo.html', context)

def student_subject_info(request, student_id, subject_code):
    student = get_object_or_404(Student, student_id=student_id)
    subject = get_object_or_404(Subject, subject_code=subject_code)
    activities = Activity.objects.filter(subject=subject)
    
    # Get grades for each activity
    grades = {}
    for activity in activities:
        grade = Grade.objects.filter(
            student=student,
            activity=activity
        ).first()
        grades[activity.activity_id] = grade.student_grade if grade else 'N/A'
    
    context = {
        'student': student,
        'subject': subject,
        'activities': activities,
        'grades': grades,
    }
    return render(request, 'studentsubinfo.html', context)

class SubjectViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Subject.objects.filter(archive=False)
    serializer_class = SubjectSerializer
    lookup_field = 'subject_code'

    def create(self, request, *args, **kwargs):
        try:
            print("Received data:", request.data)  # Debug print
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                self.perform_create(serializer)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Subject created successfully',
                    'data': serializer.data
                })
            print("Validation errors:", serializer.errors)  # Debug print
            return JsonResponse({
                'status': 'error',
                'message': serializer.errors
            }, status=400)
        except Exception as e:
            import traceback
            print("Exception:", str(e))  # Debug print
            print("Traceback:", traceback.format_exc())  # Debug print
            return JsonResponse({
                'status': 'error',
                'message': f"Server error: {str(e)}"
            }, status=500)
            
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            data = request.data.copy()
            
            # Ensure numeric fields are integers
            for field in ['year_level', 'semester']:
                if field in data:
                    data[field] = int(data[field])

            serializer = self.get_serializer(instance, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
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
            instance.delete()  # Perform actual deletion
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
    permission_classes = [AllowAny]
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
    permission_classes = [AllowAny]
    queryset = StudentSubjectEnrollment.objects.all()
    serializer_class = StudentSubjectEnrollmentSerializer

    def get_queryset(self):
        queryset = StudentSubjectEnrollment.objects.all()
        subject_code = self.request.query_params.get('subject', None)
        if subject_code:
            queryset = queryset.filter(subject__subject_code=subject_code)
        return queryset

    @action(detail=False, methods=['post'])
    def bulk_enroll(self, request):
        try:
            subject_code = request.data.get('subject_code')
            student_ids = request.data.get('student_ids', [])
            
            subject = Subject.objects.get(subject_code=subject_code)
            
            # Create enrollments for each student
            for student_id in student_ids:
                # Skip if already enrolled
                if not StudentSubjectEnrollment.objects.filter(
                    subject=subject,
                    student_id=student_id
                ).exists():
                    StudentSubjectEnrollment.objects.create(
                        subject=subject,
                        student_id=student_id
                    )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Students enrolled successfully'
            })
        except Subject.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Subject not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    @action(detail=False, methods=['post'])
    def remove_student(self, request):
        try:
            subject_code = request.data.get('subject_code')
            student_id = request.data.get('student_id')
            
            enrollment = StudentSubjectEnrollment.objects.filter(
                subject__subject_code=subject_code,
                student__student_id=student_id
            )
            
            if enrollment.exists():
                enrollment.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Student removed successfully'
                })
            return JsonResponse({
                'status': 'error',
                'message': 'Student enrollment not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class CourseViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'course_abv'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'status': 'success', 'data': serializer.data})
        return Response({'status': 'error', 'message': serializer.errors}, status=400)

    def update(self, request, *args, **kwargs):
        try:
            old_course = self.get_object()
            new_data = request.data
            
            # If the course code is changing, we need to handle related records
            if new_data['course_abv'] != old_course.course_abv:
                # Update all related records to point to the new course code
                Student.objects.filter(course=old_course).update(course=new_data['course_abv'])
                Subject.objects.filter(course=old_course).update(course=new_data['course_abv'])
                
                # Delete the old course and create a new one
                old_course.delete()
                new_course = Course.objects.create(
                    course_abv=new_data['course_abv'],
                    course_name=new_data['course_name']
                )
                serializer = self.get_serializer(new_course)
            else:
                # If only the name is changing, use normal update
                serializer = self.get_serializer(old_course, data=new_data)
                if serializer.is_valid():
                    serializer.save()
            
            return Response({
                'status': 'success',
                'data': serializer.data,
                'message': 'Course updated successfully'
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=400)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({'status': 'success'})
        except Exception as e:
            return Response({'status': 'error', 'message': str(e)}, status=400)

class StudentViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'student_id'

    def create(self, request, *args, **kwargs):
        try:
            print("Received data:", request.data)  # Debug log
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                student = serializer.save()
                response_serializer = self.get_serializer(student)
                return Response({
                    'status': 'success',
                    'message': 'Student created successfully',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            print("Validation errors:", serializer.errors)  # Debug log
            return Response({
                'status': 'error',
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Exception:", str(e))  # Debug log
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return JsonResponse({
            'status': 'success',
            'data': serializer.data
        })

    def update(self, request, *args, **kwargs):
        try:
            old_instance = self.get_object()
            new_id = request.data.get('student_id')
            data = request.data.copy()

            # Check if new ID already exists (but ignore if it's the same as current ID)
            if new_id and new_id != old_instance.student_id:
                if Student.objects.filter(student_id=new_id).exists():
                    return Response({
                        'status': 'error',
                        'message': f'Student ID {new_id} already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)

            serializer = self.get_serializer(old_instance, data=data, partial=True)
            if serializer.is_valid():
                try:
                    # Use the custom manager method to handle ID changes
                    updated_student = Student.objects.update_student_id(
                        old_instance.student_id, 
                        serializer.validated_data
                    )
                    return Response({
                        'status': 'success',
                        'data': self.get_serializer(updated_student).data,
                        'message': 'Student updated successfully'
                    })
                except Student.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'message': 'Student not found'
                    }, status=status.HTTP_404_NOT_FOUND)
                except Exception as e:
                    return Response({
                        'status': 'error',
                        'message': str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 'error',
                'message': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print("Error updating student:", str(e))
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
                'message': 'Student deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

class StudentAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': 'error',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class StudentDetailAPIView(APIView):
    permission_classes = [AllowAny]
    def get_object(self, student_id):
        return get_object_or_404(Student, student_id=student_id)

    def get(self, request, student_id):
        student = self.get_object(student_id)
        serializer = StudentSerializer(student)
        return Response({
            'status': 'success',
            'data': serializer.data
        })

    def put(self, request, student_id):
        student = self.get_object(student_id)
        serializer = StudentSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        return Response({
            'status': 'error',
            'message': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, student_id):
        student = self.get_object(student_id)
        student.delete()
        return Response({
            'status': 'success',
            'message': 'Student deleted successfully'
        })

def courses(request):
    return render(request, 'courses.html', {'courses': Course.objects.all()})

def students(request):
    students = Student.objects.all().select_related('course')
    courses = Course.objects.all()
    return render(request, 'students.html', {'students': students, 'courses': courses})

def grades(request, activity_id):
    activity = Activity.objects.select_related('subject').get(activity_id=activity_id)
    enrollments = StudentSubjectEnrollment.objects.filter(
        subject=activity.subject
    ).select_related('student').annotate(
        grade=models.Subquery(
            Grade.objects.filter(
                student=models.OuterRef('student'),
                activity=activity
            ).values('student_grade')[:1]
        )
    ).order_by('student__last_name', 'student__first_name')  # Order by last name, then first name

    context = {
        'activity': activity,
        'enrollments': enrollments,
    }
    return render(request, 'grades.html', context)

class GradeViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer

    @action(detail=False, methods=['post'])
    def save_grades(self, request):
        try:
            activity_id = request.data.get('activity_id')
            grades_data = request.data.get('grades', [])

            # Validate activity exists
            activity = Activity.objects.get(activity_id=activity_id)
            
            for grade_item in grades_data:
                student_id = grade_item['student_id']
                grade_value = grade_item['grade']
                
                Grade.objects.update_or_create(
                    student_id=student_id,
                    activity_id=activity_id,
                    defaults={'student_grade': grade_value}
                )

            return JsonResponse({'status': 'success'})
        except Activity.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Activity not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def activities_api(request, activity_id=None):
    if request.method == 'POST':
        try:
            activity_data = {
                'subject': Subject.objects.get(subject_code=request.data.get('subject')),
                'activity_type': request.data.get('activity_type'),
                'activity_name': request.data.get('activity_name'),
                'total_items': request.data.get('total_items')
            }
            activity = Activity.objects.create(**activity_data)
            return JsonResponse({
                'status': 'success',
                'message': 'Activity created successfully',
                'data': ActivitySerializer(activity).data
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    elif request.method == 'GET':
        if activity_id:
            activity = get_object_or_404(Activity, activity_id=activity_id)
            return JsonResponse({
                'status': 'success',
                'data': {
                    'activity_id': activity.activity_id,
                    'activity_type': activity.activity_type,
                    'activity_name': activity.activity_name,
                    'total_items': activity.total_items
                }
            })
        else:
            activities = Activity.objects.all()
            return JsonResponse({'status': 'success', 'data': ActivitySerializer(activities, many=True).data})

    elif request.method == 'PUT':
        try:
            activity = get_object_or_404(Activity, activity_id=activity_id)
            activity.activity_type = request.data.get('activity_type')
            activity.activity_name = request.data.get('activity_name')
            activity.total_items = request.data.get('total_items')
            activity.save()
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    elif request.method == 'DELETE':
        try:
            activity = get_object_or_404(Activity, activity_id=activity_id)
            activity.delete()
            return JsonResponse({'status': 'success', 'message': 'Activity deleted successfully'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@api_view(['POST'])
def archive_subject(request, subject_code):
    try:
        subject = get_object_or_404(Subject, subject_code=subject_code)
        subject.is_active = False
        subject.archived_date = timezone.now()
        subject.save()
        return JsonResponse({'status': 'success'})
    except Subject.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Subject not found'}, status=404)

@api_view(['DELETE'])
def delete_subject(request, subject_code):
    try:
        subject = Subject.objects.get(subject_code=subject_code)
        subject.delete()
        return JsonResponse({'status': 'success'})
    except Subject.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Subject not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@api_view(['POST'])
def unarchive_subject(request, subject_code):
    try:
        subject = Subject.objects.get(subject_code=subject_code)
        subject.is_active = True
        subject.archived_date = None
        subject.save()
        return JsonResponse({'status': 'success'})
    except Subject.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Subject not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def archived_subjects(request):
    subjects = Subject.objects.filter(is_active=False)
    return render(request, 'archived_subjects.html', {'subjects': subjects})