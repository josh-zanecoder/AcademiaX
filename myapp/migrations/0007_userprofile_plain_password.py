# Generated by Django 5.1.4 on 2025-02-03 06:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0006_alter_course_students_alter_course_teachers_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='plain_password',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
