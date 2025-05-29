from rest_framework import serializers
from .models import Subject, Course

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['course_abv', 'course_name']

class SubjectSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    
    class Meta:
        model = Subject
        fields = ['subject_code', 'subject_title', 'course', 'course_name', 
                 'school_year', 'semester', 'year_level', 'section']
