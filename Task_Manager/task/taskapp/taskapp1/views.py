from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import UserProfile, Task, TaskUpdate
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Q
import re

def _build_unique_username(requested_username, first_name, last_name, email):
    """Generate a unique username from input values when needed."""
    username = (requested_username or '').strip()
    if username:
        return username

    name_seed = f"{(first_name or '').strip()}{(last_name or '').strip()}".lower()
    email_seed = (email.split('@')[0].lower() if email and '@' in email else '')
    base_username = name_seed or email_seed or 'employee'
    base_username = re.sub(r'[^a-z0-9._-]', '', base_username) or 'employee'

    username = base_username
    suffix = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{suffix}"
        suffix += 1
    return username

def landing_page(request):
    """Landing page with login options"""
    return render(request, 'taskapp1/landing.html')

def admin_login1_view(request):
    """Admin login page"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                profile = user.userprofile
                if profile.role == 'admin':
                    login(request, user)
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, 'Access denied. Admin credentials required.')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User profile not found.')
        else:
            messages.error(request, 'Invalid credentials.')
    
    return render(request, 'taskapp1/admin_login.html')

def employee_login_view(request):
    """Employee login page"""
    if request.method == 'POST':
        credential = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        if not credential or not password:
            messages.error(request, 'Please enter both username/email and password.')
            return render(request, 'taskapp1/employee_login.html')

        # Support login with either username or email.
        login_username = credential
        if '@' in credential:
            email_user = User.objects.filter(email__iexact=credential).first()
            if email_user:
                login_username = email_user.username
         
        user = authenticate(request, username=login_username, password=password)
        if user is not None:
            try:
                profile = user.userprofile
                if profile.role == 'employee':
                    login(request, user)
                    return redirect('employee_dashboard')
                else:
                    messages.error(request, 'Access denied. Employee credentials required.')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User profile not found.')
        else:
            messages.error(request, 'Invalid credentials.')
    
    return render(request, 'taskapp1/employee_login.html')

def employee_register_view(request):
    """Employee registration page"""
    if request.method == 'POST':
        requested_username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', '').strip()

        if not all([first_name, last_name, email, password, confirm_password]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'taskapp1/employee_register.html')
         
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'taskapp1/employee_register.html')
         
        if requested_username and User.objects.filter(username=requested_username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'taskapp1/employee_register.html')
         
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'taskapp1/employee_register.html')

        username = _build_unique_username(requested_username, first_name, last_name, email)
         
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            UserProfile.objects.create(
                user=user,
                role='employee',
                phone=phone,
                department=department
            )
             
            messages.success(
                request,
                f'Registration successful! You can login with email or username: {username}'
            )
            return redirect('employee_login')
        except Exception as e:
            messages.error(request, 'Registration failed. Please try again.')
    
    return render(request, 'taskapp1/employee_register.html')

@login_required
def admin_dashboard(request):
    """Admin dashboard"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('landing_page')
    
    tasks = Task.objects.all()
    employees_count = User.objects.filter(userprofile__role='employee').count()
    
    # Task statistics
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status='pending').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    completed_tasks = tasks.filter(status='completed').count()
    
    context = {
        'tasks': tasks[:10],  # Show latest 10 tasks
        'employees_count': employees_count,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
    }
    
    return render(request, 'taskapp1/admin_dashboard.html', context)

@login_required
def employee_dashboard(request):
    """Employee dashboard"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'employee':
        messages.error(request, 'Access denied.')
        return redirect('landing_page')

    if request.method == 'POST':
        department = request.POST.get('department', '').strip()
        if not department:
            messages.error(request, 'Department cannot be empty.')
            return redirect('employee_dashboard')
        if len(department) > 50:
            messages.error(request, 'Department must be 50 characters or fewer.')
            return redirect('employee_dashboard')

        profile = request.user.userprofile
        profile.department = department
        profile.save(update_fields=['department'])
        messages.success(request, 'Department updated successfully.')
        return redirect('employee_dashboard')
     
    tasks = Task.objects.filter(assigned_to=request.user)
    
    # Task statistics for employee
    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status='pending').count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    completed_tasks = tasks.filter(status='completed').count()
    
    context = {
        'tasks': tasks,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
    }
    
    return render(request, 'taskapp1/employee_dashboard.html', context)

@login_required
def assign_task(request):
    """Admin assigns task to employee"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('landing_page')
    
    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        assigned_to_id = request.POST['assigned_to']
        priority = request.POST['priority']
        due_date = request.POST['due_date']
        
        try:
            assigned_to = User.objects.get(id=assigned_to_id)
            
            task = Task.objects.create(
                title=title,
                description=description,
                assigned_to=assigned_to,
                assigned_by=request.user,
                priority=priority,
                due_date=due_date
            )
            
            messages.success(request, f'Task "{title}" assigned to {assigned_to.get_full_name()}')
            return redirect('admin_dashboard')
        except User.DoesNotExist:
            messages.error(request, 'Selected employee not found.')
    
    employees = User.objects.filter(userprofile__role='employee')
    return render(request, 'taskapp1/assign_task.html', {'employees': employees})

@login_required
def update_task_status(request, task_id):
    """Employee updates task status"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'employee':
        messages.error(request, 'Access denied.')
        return redirect('landing_page')
    
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    
    if request.method == 'POST':
        status = request.POST['status']
        update_message = request.POST.get('update_message', '')
        completion_notes = request.POST.get('completion_notes', '')
        
        task.status = status
        if completion_notes:
            task.completion_notes = completion_notes
        task.save()
        
        # Create update record
        TaskUpdate.objects.create(
            task=task,
            updated_by=request.user,
            update_message=update_message or f'Status changed to {status}'
        )
        
        messages.success(request, 'Task updated successfully!')
        return redirect('employee_dashboard')
    
    return render(request, 'taskapp1/update_task.html', {'task': task})

@login_required
def task_details(request, task_id):
    """View task details and updates"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check access permissions
    if request.user.userprofile.role == 'employee' and task.assigned_to != request.user:
        messages.error(request, 'Access denied.')
        return redirect('employee_dashboard')
    
    updates = task.updates.all()
    
    return render(request, 'taskapp1/task_details.html', {
        'task': task,
        'updates': updates
    })

@login_required
def edit_task(request, task_id):
    """Admin edits task"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('landing_page')
    
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        task.title = request.POST['title']
        task.description = request.POST['description']
        task.priority = request.POST['priority']
        task.due_date = request.POST['due_date']
        
        # Change assigned employee if needed
        assigned_to_id = request.POST['assigned_to']
        if int(assigned_to_id) != task.assigned_to.id:
            task.assigned_to = User.objects.get(id=assigned_to_id)
            
            TaskUpdate.objects.create(
                task=task,
                updated_by=request.user,
                update_message=f'Task reassigned to {task.assigned_to.get_full_name()}'
            )
        
        task.save()
        messages.success(request, 'Task updated successfully!')
        return redirect('admin_dashboard')
    
    employees = User.objects.filter(userprofile__role='employee')
    return render(request, 'taskapp1/edit_task.html', {
        'task': task,
        'employees': employees
    })

@login_required
def delete_task(request, task_id):
    """Admin deletes task"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('landing_page')
    
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('admin_dashboard')
    
    return render(request, 'taskapp1/delete_task.html', {'task': task})

@login_required
def all_tasks(request):
    """Admin views all tasks"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('landing_page')
    
    tasks = Task.objects.all()
    
    # Filter options
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    employee_filter = request.GET.get('employee', '')
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if employee_filter:
        tasks = tasks.filter(assigned_to__id=employee_filter)
    
    # Get the selected employee name
    selected_employee = None
    if employee_filter:
        try:
            selected_employee = User.objects.get(id=employee_filter)
        except User.DoesNotExist:
            selected_employee = None
    
    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    employees = User.objects.filter(userprofile__role='employee')
    
    context = {
        'page_obj': page_obj,
        'employees': employees,
        'selected_employee': selected_employee,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'employee_filter': employee_filter,
    }
    
    return render(request, 'taskapp1/all_tasks.html', context)

@login_required
def admin_employees(request):
    """Admin views all employees in a dedicated page"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('landing_page')

    base_employees = User.objects.filter(userprofile__role='employee').select_related('userprofile')
    departments = (
        base_employees.exclude(userprofile__department__isnull=True)
        .exclude(userprofile__department__exact='')
        .values_list('userprofile__department', flat=True)
        .distinct()
        .order_by('userprofile__department')
    )
    employees_qs = base_employees

    search_query = request.GET.get('q', '').strip()
    department_filter = request.GET.get('department', '').strip()

    if search_query:
        employees_qs = employees_qs.filter(
            Q(first_name__icontains=search_query)
            | Q(last_name__icontains=search_query)
            | Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
        )
    if department_filter:
        employees_qs = employees_qs.filter(userprofile__department__iexact=department_filter)

    employees_qs = employees_qs.annotate(
        total_tasks=Count('assigned_tasks', distinct=True),
        pending_tasks=Count('assigned_tasks', filter=Q(assigned_tasks__status='pending'), distinct=True),
        in_progress_tasks=Count('assigned_tasks', filter=Q(assigned_tasks__status='in_progress'), distinct=True),
        completed_tasks=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed'), distinct=True),
    ).order_by('first_name', 'last_name', 'username')
    filtered_count = employees_qs.count()

    paginator = Paginator(employees_qs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')

    context = {
        'page_obj': page_obj,
        'departments': departments,
        'search_query': search_query,
        'department_filter': department_filter,
        'query_string': query_params.urlencode(),
        'total_employees': base_employees.count(),
        'filtered_count': filtered_count,
    }
    return render(request, 'taskapp1/admin_employees.html', context)

@login_required
def admin_add_employee(request):
    """Admin creates employee accounts from a dedicated page."""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('landing_page')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        requested_username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', '').strip()

        if not (requested_username or email):
            messages.error(request, 'Provide at least a username or an email.')
            return redirect('admin_add_employee')
        if not password:
            messages.error(request, 'Password is required.')
            return redirect('admin_add_employee')
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('admin_add_employee')
        if department and len(department) > 50:
            messages.error(request, 'Department must be 50 characters or fewer.')
            return redirect('admin_add_employee')
        if phone and len(phone) > 15:
            messages.error(request, 'Phone must be 15 characters or fewer.')
            return redirect('admin_add_employee')
        if requested_username and User.objects.filter(username=requested_username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('admin_add_employee')
        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email already exists.')
            return redirect('admin_add_employee')

        username = _build_unique_username(requested_username, first_name, last_name, email)

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            UserProfile.objects.create(
                user=user,
                role='employee',
                phone=phone,
                department=department
            )
            messages.success(
                request,
                f'Employee account created successfully. Login username: {username}'
            )
            return redirect('admin_add_employee')
        except Exception:
            messages.error(request, 'Unable to create employee account. Please try again.')
            return redirect('admin_add_employee')

    return render(request, 'taskapp1/admin_add_employee.html')

def custom_logout(request):
    """Logout and redirect to landing page"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing_page')
