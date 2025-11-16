# hub/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (
    JobApplication, ApplicationPersonal, ApplicationEducation, ApplicationCertification,
    ApplicationEmployment, ApplicationReference, ApplicationQuestion,
    ApplicationCriminalHistory, ApplicationReferral, ApplicationEEO
)

from .models import (
    CompanyProfile,
    Vacancy,
    CompanyReview,
    StudentProfile,
    JobPost,
    JobApplication,
)

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_active", "is_staff", "is_superuser")
    list_filter  = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email")


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "registration_number", "email_verified", "admin_approved", "is_verified_company")
    list_filter  = ("email_verified", "admin_approved", "is_verified_company")
    search_fields = ("name", "registration_number")
    actions = ["approve_selected", "mark_verified_company"]

    def approve_selected(self, request, queryset):
        queryset.update(admin_approved=True)
    approve_selected.short_description = "Mark selected companies as admin approved"

    def mark_verified_company(self, request, queryset):
        queryset.update(is_verified_company=True)
    mark_verified_company.short_description = "Mark selected companies as verified companies"


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    # Vacancy does have deadline (your views filter on it) and very likely created_at.
    list_display = ("title", "company", "department", "location", "deadline", "is_active", "is_verified_vacancy")
    list_filter  = ("is_active", "is_verified_vacancy", "company__is_verified_company", "department")
    search_fields = ("title", "company__name", "department", "location")
    actions = ["verify_selected", "deactivate_selected"]

    def verify_selected(self, request, queryset):
        queryset.update(is_verified_vacancy=True)
    verify_selected.short_description = "Mark selected vacancies as verified"

    def deactivate_selected(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_selected.short_description = "Deactivate selected vacancies"
    
    class Meta:
        verbose_name_plural = "Vacancies"

# Inline WITHOUT non-existent timestamps
class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    fields = ("student", "status", "resume_snapshot")
    # no readonly_fields/date fields here to avoid checks failing


@admin.register(JobPost)
class JobPostAdmin(admin.ModelAdmin):
    # Use only fields that your views/forms reference consistently
    list_display = (
        "title",
        "company",
        "job_type",
        "experience_level",
        "work_location_type",
        "is_active",
    )
    list_filter = (
        "job_type",
        "experience_level",
        "work_location_type",
        "is_active",
        "company",
    )
    search_fields = ("title", "company__name", "department", "location")
    ordering = ("-id",)  # stable fallback that always exists
    inlines = [JobApplicationInline]


class EducationInline(admin.TabularInline):
    model = ApplicationEducation
    extra = 0

class CertificationInline(admin.TabularInline):
    model = ApplicationCertification
    extra = 0

class EmploymentInline(admin.TabularInline):
    model = ApplicationEmployment
    extra = 0

class ReferenceInline(admin.TabularInline):
    model = ApplicationReference
    extra = 0

class QuestionInline(admin.TabularInline):
    model = ApplicationQuestion
    extra = 0

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("job","student","status","created_at")
    list_filter = ("status","job__company")
    search_fields = ("student__username","job__title")
    inlines = [EducationInline, CertificationInline, EmploymentInline, ReferenceInline, QuestionInline]

admin.site.register(ApplicationPersonal)
admin.site.register(ApplicationCriminalHistory)
admin.site.register(ApplicationReferral)
admin.site.register(ApplicationEEO)

@admin.register(CompanyReview)
class CompanyReviewAdmin(admin.ModelAdmin):
    # Your model (per views) supports company, rating, approved; user may not exist.
    list_display = ("company", "rating", "approved")
    list_filter  = ("approved", "rating", "company")
    search_fields = ("company__name", "comment")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    # Keep this minimal; your views reference resume/default_cover_letter, often phone exists.
    list_display = ("user",)
    search_fields = ("user__username", "user__email")

