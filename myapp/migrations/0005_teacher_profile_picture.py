# Generated by Django 5.1.4 on 2025-02-03 03:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_course_students_teacher_course_teachers'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='teacher_profiles/'),
        ),
    ]
