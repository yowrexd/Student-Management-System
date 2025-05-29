from rest_framework import serializers
from .models import Subject, Activity, StudentSubjectEnrollment, Student, Course
from datetime import date

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['subject_code', 'subject_title', 'course', 'school_year', 
                 'semester', 'year_level', 'section', 'archive']
        read_only_fields = ['archive']

    def validate_subject_code(self, value):
        if not value:
            raise serializers.ValidationError("Subject code is required")
        return value.upper()  # Convert to uppercase

    def validate(self, data):
        # Add any cross-field validation here
        if data.get('year_level') and (data['year_level'] < 1 or data['year_level'] > 4):
            raise serializers.ValidationError({"year_level": "Year level must be between 1 and 4"})
        return data

class ActivitySerializer(serializers.ModelSerializer):
    date_assigned = serializers.DateField(default=date.today, read_only=True)
    
    class Meta:
        model = Activity
        fields = ['activity_id', 'subject', 'activity_type', 'activity_name', 'total_items', 'date_assigned']
        read_only_fields = ['activity_id', 'date_assigned']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Include these fields in every response
        data['activity_id'] = instance.activity_id
        data['activity_type'] = instance.activity_type
        data['activity_name'] = instance.activity_name
        data['total_items'] = instance.total_items
        data['date_assigned'] = instance.date_assigned.strftime('%Y-%m-%d')
        return data

class StudentSubjectEnrollmentSerializer(serializers.ModelSerializer):
    student = StudentSerializer(read_only=True)
    
    class Meta:
        model = StudentSubjectEnrollment
        fields = '__all__'

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['course_abv', 'course_name']
