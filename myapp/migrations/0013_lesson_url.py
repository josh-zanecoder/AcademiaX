# Generated by Django 5.1.4 on 2025-02-04 02:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0012_alter_lesson_options_remove_lesson_content_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lesson',
            name='url',
            field=models.URLField(blank=True, help_text='Link to external resource (Google Drive, YouTube, etc.)', null=True),
        ),
    ]
