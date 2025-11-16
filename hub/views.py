from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from .forms import StudentRegistrationForm
from django.contrib.auth import login as auth_login

from .tokens import company_email_token, encode_uid, decode_uid
from django.db.models import Q
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.db import transaction
from django.http import Http404
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import (
    CompanyRegistrationForm, VacancyForm, CompanyReviewForm,
    StudentProfileForm, JobPostForm, JobEasyApplyForm
)
from .models import (
    Vacancy, CompanyProfile, CompanyReview,
    StudentProfile, JobPost, JobApplication
)
from .forms import (
    ApplicationPersonalForm, EducationFormSet, CertificationFormSet,
    EmploymentFormSet, ReferenceFormSet, QuestionFormSet,
    ApplicationCriminalHistoryForm, ApplicationReferralForm, ApplicationEEOForm,
    ApplicationDeclarationsForm
)


User = get_user_model()


def home(request):
    return vacancy_list(request)


def vacancy_list(request):
    """
    Public listing of active, non-expired attachment vacancies
    with search & filters. Used by the home page as well.
    """
    today = timezone.now().date()

    q = request.GET.get('q', '').strip()
    company_name = request.GET.get('company', '').strip()
    verified = request.GET.get('verified', '')

    vacancies = (
        Vacancy.objects.select_related('company')
        .filter(is_active=True, deadline__gte=today)
        .order_by('-created_at')
    )

    if q:
        vacancies = vacancies.filter(
            Q(title__icontains=q) |
            Q(department__icontains=q) |
            Q(location__icontains=q) |
            Q(region__icontains=q) |
            Q(required_skills__icontains=q)
        )

    if company_name:
        vacancies = vacancies.filter(company__name__icontains=company_name)

    # Show only posts from verified companies when checked
    if verified == '1':
        vacancies = vacancies.filter(company__is_verified_company=True)

    # Pagination (12 cards per page)
    paginator = Paginator(vacancies, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'vacancies': page_obj,           # iterate over this in the template
        'page_obj': page_obj,
        'q': q,
        'company_name': company_name,
        'verified': verified,
    }
    return render(request, 'hub/vacancy_list.html', context)

def vacancy_detail(request, pk):
    vacancy = get_object_or_404(Vacancy, pk=pk, is_active=True)
    company = vacancy.company

    # Approved reviews for this company
    reviews = company.reviews.filter(approved=True)[:6]

    # Average rating
    avg_rating = CompanyReview.average_for_company(company)

    review_form = CompanyReviewForm()

    context = {
        'vacancy': vacancy,
        'company': company,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_form': review_form,
    }
    return render(request, 'hub/vacancy_detail.html', context)

def _client_identifier(request):
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    # Fallback to IP (X-Forwarded-For aware if behind proxy later)
    return f"ip:{request.META.get('REMOTE_ADDR', '0.0.0.0')}"

def submit_company_review(request, company_id):
    company = get_object_or_404(CompanyProfile, pk=company_id)

    if request.method == 'POST':
        # Rate limit key: reviewer + company
        ident = _client_identifier(request)
        cache_key = f"review_rl:{ident}:company:{company_id}"
        if cache.get(cache_key):
            messages.error(request, "You are submitting reviews too fast. Please wait a few minutes before trying again.")
            return redirect(request.META.get('HTTP_REFERER', 'vacancy_list'))

        form = CompanyReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.company = company
            # Keep moderated
            review.save()
            # Set throttle (5 minutes = 300 seconds). Adjust as needed.
            cache.set(cache_key, 1, timeout=86400)
            messages.success(request, "Thank you for your review. It will appear once approved.")
        else:
            messages.error(request, "Please correct the errors in the review form.")
    return redirect(request.META.get('HTTP_REFERER', reverse('hub:job_list')))


def company_register(request):
    if request.method == 'POST':
        form = CompanyRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save()
            _send_company_verification_email(request, company)
            messages.success(
                request,
                "Registration received. Please verify your email via the link sent to you."
            )
            return redirect('hub:home')

    else:
        form = CompanyRegistrationForm()
    return render(request, 'hub/company_register.html', {'form': form})


def _send_company_verification_email(request, company: CompanyProfile):
    uid = encode_uid(company.user.pk)
    token = company_email_token.make_token(company.user)
    verify_url = request.build_absolute_uri(
        reverse('hub:verify_company_email', kwargs={'uidb64': uid, 'token': token})
    )
    subject = "Verify your company account"
    message = (
        f"Hello {company.name},\n\n"
        f"Please verify your email by clicking the link below:\n{verify_url}\n\n"
        f"Thank you."
    )
    send_mail(subject, message, None, [company.user.email], fail_silently=True)


def verify_company_email(request, uidb64, token):
    try:
        uid = decode_uid(uidb64)
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and company_email_token.check_token(user, token):
        try:
            company = user.company_profile
        except CompanyProfile.DoesNotExist:
            company = None

        if company:
            user.is_active = True
            user.save()
            company.email_verified = True
            company.save()
            messages.success(request, "Email verified. Wait for admin approval to start posting.")
            return render(request, 'hub/email_verification_success.html')

    messages.error(request, "Invalid or expired verification link.")
    return redirect('hub:home')


def is_verified_company_user(user):
    if not user.is_authenticated:
        return False
    if not getattr(user, 'is_company', lambda: False)():
        return False
    try:
        return user.company_profile.can_post
    except CompanyProfile.DoesNotExist:
        return False


@login_required
@user_passes_test(is_verified_company_user)
def company_dashboard(request):
    company = request.user.company_profile
    vacancies = company.vacancies.all()
    jobs = company.job_posts.all()
    return render(request, "hub/company_dashboard.html", {
        "company": company,
        "vacancies": vacancies,
        "jobs": jobs,
    })

@login_required
@user_passes_test(is_verified_company_user)
def vacancy_create(request):
    company = request.user.company_profile
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        # IMPORTANT: attach company before is_valid(), so model.clean() can use it
        form.instance.company = company
        if form.is_valid():
            vacancy = form.save()
            messages.success(request, "Vacancy posted successfully.")
            return redirect('hub:company_dashboard')
    else:
        form = VacancyForm()
    return render(request, 'hub/vacancy_form.html', {'form': form})

@login_required
@user_passes_test(is_verified_company_user)
def vacancy_edit(request, pk):
    company = request.user.company_profile
    vacancy = get_object_or_404(Vacancy, pk=pk, company=company)
    if request.method == 'POST':
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            form.save()
            messages.success(request, "Vacancy updated.")
            return redirect('hub:company_dashboard')
    else:
        form = VacancyForm(instance=vacancy)
    return render(request, 'hub/vacancy_form.html', {'form': form, 'edit_mode': True})

def about(request):
    return render(request, 'hub/about.html')

def is_moderator(user):
    return user.is_authenticated and getattr(user, 'is_moderator', lambda: False)()

def is_student(user):
    return user.is_authenticated and user.role == 'STUDENT'

def is_company_approved(user):
    try:
        return user.is_authenticated and user.is_company() and user.company_profile.can_post
    except CompanyProfile.DoesNotExist:
        return False

@login_required
@user_passes_test(is_moderator)
def moderator_dashboard(request):
    unapproved_companies = CompanyProfile.objects.filter(admin_approved=False, email_verified=True)
    pending_reviews = CompanyReview.objects.filter(approved=False)[:20]
    pending_jobs = JobPost.objects.filter(is_active=True)[:20]  # simple surface; you can add flags later

    if request.method == 'POST':
        action = request.POST.get('action')
        obj_type = request.POST.get('type')
        obj_id = request.POST.get('id')
        if action and obj_type and obj_id:
            if obj_type == 'company':
                obj = CompanyProfile.objects.filter(id=obj_id).first()
                if obj:
                    if action == 'approve': obj.admin_approved = True
                    if action == 'verify': obj.is_verified_company = True
                    obj.save()
                    messages.success(request, "Company updated.")
            elif obj_type == 'review':
                obj = CompanyReview.objects.filter(id=obj_id).first()
                if obj:
                    if action == 'approve': obj.approved = True
                    if action == 'reject': obj.delete()
                    else: obj.save()
                    messages.success(request, "Review moderated.")
            elif obj_type == 'job':
                obj = JobPost.objects.filter(id=obj_id).first()
                if obj:
                    if action == 'deactivate':
                        obj.is_active = False
                        obj.save()
                        messages.success(request, "Job deactivated.")
    return render(request, 'hub/moderator_dashboard.html', {
        'unapproved_companies': unapproved_companies,
        'pending_reviews': pending_reviews,
        'pending_jobs': pending_jobs,
    })

def job_list(request):
    # Toggle: jobs vs attachments by query param `mode=jobs|attachments`
    mode = request.GET.get('mode', 'jobs')
    q = request.GET.get('q', '')
    company_name = request.GET.get('company', '')
    exp = request.GET.get('exp', '')  # ENTRY/MID/SENIOR/EXEC
    jtype = request.GET.get('type', '')  # FULL_TIME, etc.
    remote = request.GET.get('remote', '')  # '1' for Remote only
    salary_min = request.GET.get('smin', '')
    salary_max = request.GET.get('smax', '')

    context = {'mode': mode, 'q': q, 'company_name': company_name, 'exp': exp, 'type': jtype, 'remote': remote, 'smin': salary_min, 'smax': salary_max}

    if mode == 'attachments':
        return vacancy_list(request)  # reuse your existing function

    # Jobs mode
    jobs = JobPost.objects.filter(is_active=True)
    if q:
        jobs = jobs.filter(Q(title__icontains=q) | Q(department__icontains=q))
    if company_name:
        jobs = jobs.filter(company__name__icontains=company_name)
    if exp:
        jobs = jobs.filter(experience_level=exp)
    if jtype:
        jobs = jobs.filter(job_type=jtype)
    if remote == '1':
        jobs = jobs.filter(work_location_type='REMOTE')
    if salary_min:
        jobs = jobs.filter(salary_min__gte=salary_min)
    if salary_max:
        jobs = jobs.filter(Q(salary_max__lte=salary_max) | Q(salary_max__isnull=True))

    context['jobs'] = jobs
    return render(request, 'hub/job_list.html', context)

def job_detail(request, pk):
    job = get_object_or_404(JobPost, pk=pk, is_active=True)
    company = job.company
    avg_rating = CompanyReview.average_for_company(company)
    return render(request, 'hub/job_detail.html', {
        'job': job, 'company': company, 'avg_rating': avg_rating
    })

@login_required
@user_passes_test(is_student)
def job_easy_apply(request, pk):
    job = get_object_or_404(JobPost, pk=pk, is_active=True)
    if not job.easy_apply:
        raise Http404("Easy Apply is disabled for this job.")
    student = request.user
    profile = getattr(student, 'student_profile', None)

    if request.method == 'POST':
        form = JobEasyApplyForm(request.POST)
        if form.is_valid():
            # prevent duplicate
            if JobApplication.objects.filter(job=job, student=student).exists():
                messages.info(request, "You have already applied to this job.")
                return redirect('hub:job_detail', pk=pk)

            app = form.save(commit=False)
            app.job = job
            app.student = student

            # use saved cover letter
            if form.cleaned_data.get('use_profile_cover') and profile and profile.default_cover_letter:
                app.cover_letter = profile.default_cover_letter if not app.cover_letter else app.cover_letter

            # optional snapshot of current resume
            if profile and profile.resume and not app.resume_snapshot:
                app.resume_snapshot = profile.resume

            app.save()
            messages.success(request, "Application submitted.")
            return redirect('hub:student_dashboard')
    else:
        initial_cover = profile.default_cover_letter if profile else ''
        form = JobEasyApplyForm(initial={'cover_letter': initial_cover, 'use_profile_cover': True})
    return render(request, 'hub/job_apply.html', {'job': job, 'form': form})

@login_required
@user_passes_test(is_student)
def student_profile(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('hub:student_profile')
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, 'hub/student_profile.html', {'form': form})

@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    apps = JobApplication.objects.filter(student=request.user).select_related('job','job__company')
    return render(request, 'hub/student_dashboard.html', {'applications': apps})

@login_required
@user_passes_test(is_company_approved)
def job_create(request):
    company = request.user.company_profile
    if request.method == 'POST':
        form = JobPostForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.save()
            messages.success(request, "Job posted successfully.")
            return redirect('hub:company_job_applicants', pk=job.pk)
    else:
        form = JobPostForm()
    return render(request, 'hub/job_form.html', {'form': form})

@login_required
@user_passes_test(is_company_approved)
def company_job_applicants(request, pk):
    job = get_object_or_404(
        JobPost,
        pk=pk,
        company=request.user.company_profile
    )

    status = request.GET.get('status', '')
    q = request.GET.get('q', '')

    # Pull applications + student + student_profile in one go
    apps = (
        job.applications
        .select_related('student', 'student__student_profile')
        .all()
    )

    if status:
        apps = apps.filter(status=status)
    if q:
        apps = apps.filter(
            Q(student__username__icontains=q) |
            Q(student__email__icontains=q) |
            Q(cover_letter__icontains=q)
        )

    return render(request, 'hub/company_job_applicants.html', {
        'job': job,
        'applications': apps,
        'status': status,
        'q': q,
        'status_choices': JobApplication.STATUS_CHOICES,   # 👈 NEW
    })

@login_required
@user_passes_test(is_company_approved)
def update_application_status(request, app_id):
    app = get_object_or_404(JobApplication, id=app_id, job__company=request.user.company_profile)
    new_status = request.POST.get('status')
    if new_status in dict(JobApplication.STATUS_CHOICES):
        app.status = new_status
        app.save()
        # Optional: email response
        try:
            send_mail(
                subject=f"Update on your application for {app.job.title}",
                message=f"Your application status is now: {app.get_status_display()}",
                from_email=None,
                recipient_list=[app.student.email],
                fail_silently=True
            )
        except Exception:
            pass
        messages.success(request, "Status updated and notification sent.")
    return redirect('hub:company_job_applicants', pk=app.job.pk)

def company_profile(request, company_id):
    company = get_object_or_404(CompanyProfile, id=company_id)
    tab = request.GET.get('tab', 'attachments')  # 'attachments' | 'jobs'

    # Attachments: active vacancies
  
    today = timezone.now().date()
    attachments = company.vacancies.filter(is_active=True, deadline__gte=today)

    # Jobs: active job posts
    jobs = company.job_posts.filter(is_active=True)

    avg_rating = CompanyReview.average_for_company(company)
    reviews = company.reviews.filter(approved=True)[:6]

    return render(request, 'hub/company_profile.html', {
        'company': company,
        'tab': tab,
        'attachments': attachments,
        'jobs': jobs,
        'avg_rating': avg_rating,
        'reviews': reviews,
    })

# --- make student_register honor ?next= so it returns to the apply page ---
def student_register(request):
    next_url = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            StudentProfile.objects.get_or_create(user=user)
            auth_login(request, user)

            # Safe-redirect back to where they were going (e.g., /jobs/12/apply/standard/)
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            messages.success(request, "Welcome! Your student account is ready.")
            return redirect("hub:student_dashboard")
    else:
        form = StudentRegistrationForm()

    return render(request, "hub/student_register.html", {"form": form, "next": next_url})

@login_required
@user_passes_test(is_verified_company_user)
def company_dashboard(request):
    company = request.user.company_profile
    vacancies = company.vacancies.all()
    jobs = company.job_posts.all()  # <-- add this
    return render(request, "hub/company_dashboard.html", {
        "company": company,
        "vacancies": vacancies,
        "jobs": jobs,  # <-- and pass it
    })

@login_required
@user_passes_test(is_student)
@transaction.atomic
def job_apply_standard(request, pk):
    job = get_object_or_404(JobPost, pk=pk, is_active=True)
    if not job.standard_apply:
        raise Http404("Standard Apply is disabled for this job.")
    student = request.user

    # create shell application if missing (so formsets have a parent)
    application, _ = JobApplication.objects.get_or_create(job=job, student=student)

    if request.method == "POST":
        personal_form = ApplicationPersonalForm(request.POST, instance=getattr(application, 'personal', None))
        edu_fs = EducationFormSet(request.POST, instance=application, prefix='edu')
        cert_fs = CertificationFormSet(request.POST, instance=application, prefix='cert')
        emp_fs = EmploymentFormSet(request.POST, instance=application, prefix='emp')
        ref_fs = ReferenceFormSet(request.POST, instance=application, prefix='ref')
        q_fs = QuestionFormSet(request.POST, instance=application, prefix='q')
        crim_form = ApplicationCriminalHistoryForm(request.POST, instance=getattr(application, 'criminal_history', None))
        refsrc_form = ApplicationReferralForm(request.POST, instance=getattr(application, 'referral', None))
        eeo_form = ApplicationEEOForm(request.POST, instance=getattr(application, 'eeo', None))
        decl_form = ApplicationDeclarationsForm(request.POST, instance=application)

        forms_valid = all([
            personal_form.is_valid(), edu_fs.is_valid(), cert_fs.is_valid(),
            emp_fs.is_valid(), ref_fs.is_valid(), q_fs.is_valid(),
            crim_form.is_valid(), refsrc_form.is_valid(), eeo_form.is_valid(),
            decl_form.is_valid()
        ])
        if forms_valid:
            personal = personal_form.save(commit=False); personal.application = application; personal.save()
            edu_fs.save(); cert_fs.save(); emp_fs.save(); ref_fs.save(); q_fs.save()
            ch = crim_form.save(commit=False); ch.application = application; ch.save()
            rs = refsrc_form.save(commit=False); rs.application = application; rs.save()
            eeo = eeo_form.save(commit=False); eeo.application = application; eeo.save()
            decl_form.save()
            messages.success(request, "Your application has been submitted.")
            return redirect('hub:student_dashboard')
    else:
        personal_form = ApplicationPersonalForm(instance=getattr(application, 'personal', None))
        edu_fs = EducationFormSet(instance=application, prefix='edu')
        cert_fs = CertificationFormSet(instance=application, prefix='cert')
        emp_fs = EmploymentFormSet(instance=application, prefix='emp')
        ref_fs = ReferenceFormSet(instance=application, prefix='ref')
        q_fs = QuestionFormSet(instance=application, prefix='q')
        crim_form = ApplicationCriminalHistoryForm(instance=getattr(application, 'criminal_history', None))
        refsrc_form = ApplicationReferralForm(instance=getattr(application, 'referral', None))
        eeo_form = ApplicationEEOForm(instance=getattr(application, 'eeo', None))
        decl_form = ApplicationDeclarationsForm(instance=application)

    return render(request, 'hub/job_apply_standard.html', {
        'job': job,
        'personal_form': personal_form,
        'edu_fs': edu_fs, 'cert_fs': cert_fs, 'emp_fs': emp_fs,
        'ref_fs': ref_fs, 'q_fs': q_fs,
        'crim_form': crim_form, 'refsrc_form': refsrc_form,
        'eeo_form': eeo_form, 'decl_form': decl_form
    })