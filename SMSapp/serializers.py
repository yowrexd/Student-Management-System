from rest_framework import serializers
from .models import Subject, Activity, StudentSubjectEnrollment, Student, Course, Grade, Section
from datetime import date

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['student_id', 'last_name', 'first_name', 'middle_name', 
                 'course', 'year_level', 'section', 'status']

    def _get_course(self, course_data):
        if isinstance(course_data, str):
            try:
                return Course.objects.get(course_abv=course_data)
            except Course.DoesNotExist:
                raise serializers.ValidationError({'course': 'Invalid course abbreviation'})
        return course_data

    def create(self, validated_data):
        # Handle course
        course = validated_data.get('course')
        validated_data['course'] = self._get_course(course)
        return Student.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Handle course
        course = validated_data.get('course')
        if isinstance(course, str):
            try:
                validated_data['course'] = Course.objects.get(course_abv=course)
            except Course.DoesNotExist:
                raise serializers.ValidationError({'course': 'Invalid course abbreviation'})

        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.course:
            data['course'] = instance.course.course_abv
            data['course_name'] = instance.course.course_name
        return data

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['subject_code', 'subject_title', 'course', 'school_year', 
                 'semester', 'year_level', 'section', 'archive']
        read_only_fields = ['archive']

    def validate_subject_code(self, value):
        if not value:
            raise serializers.ValidationError("Subject code is required")
        return value.upper()  # Convert to uppercase    def validate(self, data):
        # Check uniqueness for subject code during update
        if self.instance and 'subject_code' in data:
            new_code = data['subject_code'].upper()
            if new_code != self.instance.subject_code:
                if Subject.objects.filter(subject_code=new_code).exists():
                    raise serializers.ValidationError({
                        'subject_code': 'Subject with this code already exists'
                    })
            data['subject_code'] = new_code

        # Validate year level
        if data.get('year_level') and (data['year_level'] < 1 or data['year_level'] > 4):
            raise serializers.ValidationError({"year_level": "Year level must be between 1 and 4"})
        return data

class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ['activity_id', 'subject', 'activity_type', 'activity_name', 'total_items']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Include these fields in every response
        data['activity_id'] = instance.activity_id
        data['activity_type'] = instance.activity_type
        data['activity_name'] = instance.activity_name
        data['total_items'] = instance.total_items
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

class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ['grade_id', 'student', 'activity', 'student_grade']

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'course', 'year_level', 'section_name']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['course'] = instance.course.course_abv
        return data
