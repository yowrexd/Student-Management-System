from django.db import models

class Course(models.Model):
    course_abv = models.CharField(max_length=10, primary_key=True)
    course_name = models.CharField(max_length=100)

    def __str__(self):
        return self.course_name


class Student(models.Model):
    student_id = models.CharField(max_length=20, primary_key=True)
    last_name = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year_level = models.PositiveSmallIntegerField()
    section = models.CharField(max_length=20)

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
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    school_year = models.CharField(max_length=20)
    semester = models.PositiveSmallIntegerField(choices=SEMESTER_CHOICES)
    year_level = models.PositiveSmallIntegerField()
    section = models.CharField(max_length=20)
    archive = models.BooleanField(default=False)

    def __str__(self):
        return self.subject_title


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

    def __str__(self):
        return f"{self.activity_name} ({self.subject})"


class Grade(models.Model):
    grade_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    student_grade = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.student} - {self.activity}: {self.student_grade}"
