from django.db import models

# Create your models here.
class SchoolTexbook(models.Model):
    district = models.CharField(max_length=10)
    level = models.CharField(max_length=10)
    school = models.CharField(max_length=10)
    grade = models.CharField(max_length=5)
    grade_num = models.IntegerField(default=0)
    sub_chinese = models.CharField(max_length=20)
    sub_math = models.CharField(max_length=20)
    sub_science = models.CharField(max_length=20)
    sub_social = models.CharField(max_length=20)
    sub_english = models.CharField(max_length=20)


    class Meta:
        verbose_name = "出版社"
        verbose_name_plural = "出版社"

    def __str__(self):
        return self.school









