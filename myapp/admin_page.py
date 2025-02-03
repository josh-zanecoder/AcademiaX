from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test

def is_superuser(user):
    return user.is_superuser


@login_required
@user_passes_test(is_superuser)
def manage_courses(request):
    return render(request, 'admin/manage_courses.html')