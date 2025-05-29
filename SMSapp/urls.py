from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api/subjects', views.SubjectViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('index/', views.index, name='index'),
    path('subjects/', views.subjects, name='subjects'),
    path('subjects/<str:subject_code>/', views.subject_info, name='subject_info'),
    path('', include(router.urls)),
]