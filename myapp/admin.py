from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Course, Teacher, UserProfile, Student

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_plain_password')
    
    def get_role(self, obj):
        return obj.userprofile.role if hasattr(obj, 'userprofile') else '-'
    get_role.short_description = 'Role'

    def get_plain_password(self, obj):
        if hasattr(obj, 'userprofile'):
            return obj.userprofile.plain_password or '********'
        return '********'
    get_plain_password.short_description = 'Password'

    def save_model(self, request, obj, form, change):
        if obj.password and not obj.password.startswith('pbkdf2_sha256'):
            # Store the plain text password
            if not change:  # Only for new users
                obj._password = obj.password
                # Save or update the plain password in UserProfile
                super().save_model(request, obj, form, change)
                UserProfile.objects.update_or_create(
                    user=obj,
                    defaults={'plain_password': obj._password}
                )
            else:
                super().save_model(request, obj, form, change)
        else:
            super().save_model(request, obj, form, change)

class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_profile_picture', 'first_name', 'last_name', 'user', 'get_email', 'get_courses', 'status_badge')
    search_fields = ('first_name', 'last_name', 'user__email')
    list_filter = ('courses_teaching__name', 'is_active')
    readonly_fields = ('get_profile_picture_preview',)
    fields = ('user', 'first_name', 'last_name', 'profile_picture', 'get_profile_picture_preview', 'is_active')
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_courses(self, obj):
        return ", ".join([course.name for course in obj.courses_teaching.all()])
    get_courses.short_description = 'Teaching Courses'
    
    def get_profile_picture(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.profile_picture.url)
        return format_html('<span>No Image</span>')
    get_profile_picture.short_description = 'Picture'
    
    def get_profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="200" height="200" style="border-radius: 8px;" />', obj.profile_picture.url)
        return format_html('<span>No Image</span>')
    get_profile_picture_preview.short_description = 'Profile Picture Preview'

    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 10px;">Active</span>')
        return format_html('<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 10px;">Inactive</span>')
    status_badge.short_description = 'Status'

class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'user', 'get_email', 'get_enrolled_courses')
    search_fields = ('first_name', 'last_name', 'user__email')
    list_filter = ('enrolled_courses__name',)
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def get_enrolled_courses(self, obj):
        return ", ".join([course.name for course in obj.enrolled_courses.all()])
    get_enrolled_courses.short_description = 'Enrolled Courses'

class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_by', 'created_at', 'get_teachers', 'get_students')
    search_fields = ('name', 'category', 'description')
    list_filter = ('category', 'created_at')
    filter_horizontal = ('teachers', 'students')
    
    def get_teachers(self, obj):
        return ", ".join([f"{teacher.first_name} {teacher.last_name}" for teacher in obj.teachers.all()])
    get_teachers.short_description = 'Teachers'
    
    def get_students(self, obj):
        return ", ".join([f"{student.first_name} {student.last_name}" for student in obj.students.all()])
    get_students.short_description = 'Students'

# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Register our models
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(Course, CourseAdmin)
