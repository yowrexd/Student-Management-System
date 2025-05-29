from django.db import models
from django.utils import timezone
import datetime

class Course(models.Model):
    course_abv = models.CharField(max_length=10, primary_key=True)
    course_name = models.CharField(max_length=100)

    def __str__(self):
        return self.course_name


class StudentManager(models.Manager):
    def update_student_id(self, old_id, new_data):
        student = self.get(student_id=old_id)
        new_id = new_data.get('student_id', old_id)
        
        # If ID is changing and new ID doesn't exist
        if new_id != old_id:
            # Create new student with new ID
            self.create(
                student_id=new_id,
                last_name=new_data.get('last_name', student.last_name),
                first_name=new_data.get('first_name', student.first_name),
                middle_name=new_data.get('middle_name', student.middle_name),
                course=new_data.get('course', student.course),
                year_level=new_data.get('year_level', student.year_level),
                section=new_data.get('section', student.section)
            )
            # Delete old student record
            student.delete()
            # Get and return the new student record
            return self.get(student_id=new_id)
        
        # If no ID change, just update fields
        for key, value in new_data.items():
            setattr(student, key, value)
        student.save()
        return student


class Student(models.Model):
    student_id = models.CharField(max_length=20, primary_key=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year_level = models.PositiveSmallIntegerField()
    section = models.CharField(max_length=20)

    objects = StudentManager()

    def __str__(self):
        return f"{self.student_id} - {self.last_name}, {self.first_name}"


class Subject(models.Model):
    SEMESTER_CHOICES = [
        (1, '1st Semester'),
        (2, '2nd Semester'),
        (3, 'Summer'),
    ]

    subject_code = models.CharField(max_length=20, primary_key=True)
    subject_title = models.CharField(max_length=100)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)  # Make course optional
    school_year = models.CharField(max_length=20)
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_CHOICES)
    year_level = models.PositiveSmallIntegerField()
    section = models.CharField(max_length=20)
    archive = models.BooleanField(default=False)

    class Meta:
        ordering = ['subject_code']

    def __str__(self):
        return f"{self.subject_code} - {self.subject_title}"


class StudentSubjectEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} enrolled in {self.subject}"


class Activity(models.Model):
    ACTIVITY_TYPE_CHOICES = [
        ('Quiz', 'Quiz'),
        ('Activities', 'Activities'),
        ('Exam', 'Exam'),
        ('Project', 'Project'),
    ]

    activity_id = models.AutoField(primary_key=True)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE_CHOICES)
    activity_name = models.CharField(max_length=100)
    total_items = models.PositiveIntegerField()
    date_assigned = models.DateField(default=datetime.date.today)  # Changed from timezone.now

    def __str__(self):
        return f"{self.activity_name} ({self.subject})"


class Grade(models.Model):
    grade_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    student_grade = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.student} - {self.activity}: {self.student_grade}"
