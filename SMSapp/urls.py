from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'subjects', views.SubjectViewSet, basename='api-subjects')
router.register(r'activities', views.ActivityViewSet, basename='api-activities')
router.register(r'enrollments', views.EnrollmentViewSet, basename='api-enrollments')
router.register(r'courses', views.CourseViewSet, basename='api-courses')
router.register(r'students', views.StudentViewSet, basename='api-students')
router.register(r'grades', views.GradeViewSet, basename='api-grades')

urlpatterns = [
    path('', views.index, name='index'),
    path('api/', include(router.urls)),
    path('index/', views.index, name='index'),
    path('subjects/', views.subjects, name='subjects'),
    path('subjects/<str:subject_code>/', views.subject_info, name='subject_info'),
    path('students/', views.students, name='students'),
    path('students/<str:student_id>/', views.student_info, name='student_info'),  # Add this line
    path('students/<str:student_id>/subjects/<str:subject_code>/', views.student_subject_info, name='student_subject_info'),
    path('courses/', views.courses, name='courses'),
    path('activities/<int:activity_id>/grades/', views.grades, name='grades'),
]