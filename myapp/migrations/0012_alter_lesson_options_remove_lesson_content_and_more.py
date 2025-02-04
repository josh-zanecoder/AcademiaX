# Generated by Django 5.1.4 on 2025-02-04 02:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0011_alter_lesson_unique_together_lesson_file_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='lesson',
            options={},
        ),
        migrations.RemoveField(
            model_name='lesson',
            name='content',
        ),
        migrations.RemoveField(
            model_name='lesson',
            name='video_url',
        ),
        migrations.AlterField(
            model_name='lesson',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='file',
            field=models.FileField(blank=True, help_text='Upload lesson materials (PDF, DOC, PPT, etc.)', null=True, upload_to='lesson_files/'),
        ),
    ]
