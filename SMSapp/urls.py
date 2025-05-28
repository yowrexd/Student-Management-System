from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'students', views.StudentViewSet)
router.register(r'grades', views.GradeViewSet)
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'subjects', views.SubjectViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('students/', views.student_list, name='student_list'),
    path('students/<str:student_id>/', views.student_detail, name='student_detail'),
    path('api/', include(router.urls)),
    path('courses/', views.course_list, name='course_list'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('grades/', views.grade_list, name='grade_list'),
]