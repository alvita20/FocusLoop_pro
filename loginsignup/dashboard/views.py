from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Complaint, LeaveRecord
from base.models import Students
from datetime import date
from django.db.models import Q



# ------------------------------
# Dashboard router: redirect based on role
# ------------------------------

def dashboard_router(request):
    user = request.user

    if hasattr(user, 'teacher'):
        return redirect('dashboard:teacher_home')

    if hasattr(user, 'student'):
        return redirect('dashboard:student_home')

    return redirect('base:welcome')


# ------------------------------
# Student home/dashboard
# ------------------------------
def student_home_view(request):
    student = request.user.student

    leave_count = LeaveRecord.objects.filter(student=student).count()
    complaint_count = Complaint.objects.filter(student=student).count()

    complaints = Complaint.objects.filter(student=student)

    return render(request, 'dashboard/student_home.html', {
        "student": student,
        "leave_count": leave_count,
        "complaint_count": complaint_count,
        "complaints": complaints,   # 🔴 THIS WAS MISSING
    })



# ------------------------------
# Teacher home/dashboard
# ------------------------------

def teacher_home_view(request):
    teacher = request.user.teacher
    complaints = Complaint.objects.all().order_by("-created_at")
    leave_count = LeaveRecord.objects.filter(student__student_class=teacher.class_assigned).count()
    complaint_count = Complaint.objects.count()  # Or filter by class/section

    return render(request, 'dashboard/teacher_home.html', {
        "teacher": teacher,
        "leave_count": leave_count,
        "complaint_count": complaint_count,

        "complaints": complaints,
    })

# ------------------------------
# Student complaints
# ------------------------------
@login_required(login_url='login')
def student_complain_view(request):
    student = request.user.student

    if request.method == 'POST':

        anonymous = request.POST.get("anonymous")

        if anonymous:
            student_obj = None
        else:
            student_obj = request.user.student

        Complaint.objects.create(
            student=student_obj,
            title=request.POST.get('complaint_title'),
            category=request.POST.get('complaint_category'),
            description=request.POST.get('complaint_detail') or '',
            status='Pending'
        )

        return redirect('dashboard:student_complain')


    complaints = Complaint.objects.filter(
        Q(student=student) | Q(student=None)
    ).order_by("-created_at")

    return render(request, 'dashboard/student_complain.html', {
        'student': student,
        'complaints': complaints
    })



# ------------------------------
# Student leave requests
# ------------------------------
@login_required(login_url='login')
def student_leave_view(request):
    student = request.user.student

    if request.method == "POST":
        LeaveRecord.objects.create(
            student=student,
            leave_type=request.POST.get("leave_type"),
            start_date=request.POST.get("start_date"),
            end_date=request.POST.get("end_date"),
            reason=request.POST.get("reason"),
            status="Pending"
        )
        return redirect('dashboard:student_leave')

    leave_applications = LeaveRecord.objects.filter(student=student).order_by("-created_at")

    return render(request, 'dashboard/student_leave.html', {
        "student": student,
        "leave_applications": leave_applications
    })



# ------------------------------
# Teacher: update complaint status
# ------------------------------
@login_required(login_url='login')
def update_complaint_status(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ["Pending", "In Progress", "Resolved"]:
            complaint.status = new_status
            complaint.save()

    return redirect('dashboard:teacher_complain')

#------------------------------
# Teacher: leave applications view
#------------------------------
@login_required
def teacher_leave_view(request):
    teacher = request.user.teacher
    # Filter leave applications for students in the teacher's class
    leave_applications = LeaveRecord.objects.filter(
        student__student_class=teacher.class_assigned
    ).order_by('-created_at')
    
    return render(request, 'dashboard/teacher_leave.html', {
        'teacher': teacher,
        'leave_applications': leave_applications
    })


@login_required
def update_leave_status(request, leave_id):
    leave = get_object_or_404(LeaveRecord, id=leave_id)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ["Approved", "Rejected"]:
            leave.status = new_status
            leave.save()
    return redirect('dashboard:teacher_leave_requests')

@login_required
def teacher_complain_view(request):
    teacher = request.user.teacher

    complaints = Complaint.objects.filter(
        status__in=["Pending", "In Progress"]
    ).order_by("-created_at")

    return render(request, 'dashboard/teacher_complain.html', {
        'complaints': complaints,
        'teacher': teacher,
        'section': teacher.class_assigned
    })

