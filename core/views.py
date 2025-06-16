from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from .models import School, UserProfile
from .forms import SchoolSignupForm
from django.db import transaction
from django.contrib import messages

# Create your views here.

def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'core/home.html')

def public_home(request):
    return render(request, 'core/public_home.html')


def school_signup(request):
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'POST':
        form = SchoolSignupForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'This username already exists.')
            else:
                try:
                    with transaction.atomic():
                        # Create the school
                        school = School.objects.create(
                            name=form.cleaned_data['name'],
                            address=form.cleaned_data['address'],
                            contact=form.cleaned_data['contact']
                        )

                        # Create the user (this will trigger the signal)
                        user = User.objects.create_user(
                            username=username,
                            email=form.cleaned_data['email'],
                            password=form.cleaned_data['password']
                        )

                        # Get the auto-created UserProfile and update it
                        profile = user.userprofile
                        profile.school = school
                        profile.is_admin = True
                        profile.save()

                        login(request, user)
                        return redirect('home')

                except Exception as e:
                    form.add_error(None, f"Something went wrong: {str(e)}")

    else:
        form = SchoolSignupForm()

    return render(request, 'core/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # Redirect to home if already logged in
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                login(request, user)
                messages.success(request, "You have been logged in successfully.")
                return redirect('home')  # Redirect to home after successful login
            else:
                return render(request, 'core/login.html', {'error': 'Invalid credentials'})
        except User.DoesNotExist:
            return render(request, 'core/login.html', {'error': 'User does not exist'})
    return render(request, 'core/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect('public_home')  # or 'login' or any page you want after logout

