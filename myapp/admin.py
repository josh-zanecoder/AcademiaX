from django.contrib import admin
from .models import User, Student

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'created_at', 'updated_at')
    list_filter = ('role', 'created_at')
    search_fields = ('username', 'email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('username', 'email', 'password')
        }),
        ('Role', {
            'fields': ('role',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'first_name', 'last_name', 'get_email')
    search_fields = ('first_name', 'last_name', 'user__username', 'user__email')
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user__username'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'
