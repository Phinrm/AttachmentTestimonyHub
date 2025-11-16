# hub/urls.py
from django.urls import path
from . import views

app_name = "hub"

urlpatterns = [
    # Home / attachments
    path("", views.home, name="home"),
    path("attachments/", views.vacancy_list, name="vacancy_list"),
    path("attachments/<int:pk>/", views.vacancy_detail, name="vacancy_detail"),

    # Company register / verify / public profile
    path("companies/register/", views.company_register, name="company_register"),
    path("companies/verify/<uidb64>/<token>/", views.verify_company_email, name="verify_company_email"),
    path("companies/<int:company_id>/", views.company_profile, name="company_profile"),

    # ⭐ THIS is the missing route causing NoReverseMatch
    path(
        "companies/<int:company_id>/reviews/submit/",
        views.submit_company_review,
        name="submit_company_review",
    ),

    # Company dashboards & attachment vacancies
    path("company/dashboard/", views.company_dashboard, name="company_dashboard"),
    path("company/vacancies/new/", views.vacancy_create, name="vacancy_create"),
    path("company/vacancies/<int:pk>/edit/", views.vacancy_edit, name="vacancy_edit"),

    # Moderator
    path("moderator/dashboard/", views.moderator_dashboard, name="moderator_dashboard"),

    # Jobs (standard + easy apply)
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/apply/easy/", views.job_easy_apply, name="job_easy_apply"),
    path("jobs/<int:pk>/apply/full/", views.job_apply_standard, name="job_apply_standard"),

    # Student flows
    path("student/register/", views.student_register, name="student_register"),
    path("student/profile/", views.student_profile, name="student_profile"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),

    # Company job posting + applicants
    path("company/jobs/new/", views.job_create, name="job_create"),
    path(
        "company/jobs/<int:pk>/applicants/",
        views.company_job_applicants,
        name="company_job_applicants",
    ),
    path(
        "company/applications/<int:app_id>/status/",
        views.update_application_status,
        name="update_application_status",
    ),

    # Static page
    path("about/", views.about, name="about"),
]
