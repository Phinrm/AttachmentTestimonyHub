from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'System Admin'),
        ('MODERATOR', 'Moderator'),              # NEW: can moderate via site, not /admin
        ('COMPANY', 'Company Representative'),
        ('STUDENT', 'Student / General User'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STUDENT')

    def is_company(self):
        return self.role == 'COMPANY'

    def is_admin(self):
        return self.role == 'ADMIN' or self.is_superuser

    def is_moderator(self):
        return self.role == 'MODERATOR'

class CompanyProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company_profile')
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, unique=True)
    industry = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    region = models.CharField(max_length=255, blank=True, help_text="Region or county where the company is based.")
    map_embed_url = models.URLField(
        blank=True,
        help_text="Optional: Google Maps embed URL to show your exact location."
    )   
    contact_person = models.CharField(max_length=255)
    official_email = models.EmailField()
    phone_number = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)

    email_verified = models.BooleanField(default=False)
    admin_approved = models.BooleanField(default=False)
    is_verified_company = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def can_post(self):
        return self.email_verified and self.admin_approved
    @property
    def average_rating(self):
        from .models import CompanyReview  # avoid circular import at top
        avg = CompanyReview.average_for_company(self)
        return avg


def upload_cv_path(instance, filename):
    return f"cvs/{instance.user_id}/{filename}"

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=255, blank=True)
    education_history = models.TextField(blank=True, help_text="List institutions, dates, awards.")
    work_experience = models.TextField(blank=True, help_text="List roles, companies, dates, responsibilities.")
    default_cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to=upload_cv_path, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"StudentProfile({self.user.username})"


class Vacancy(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='vacancies')
    title = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    duration = models.CharField(max_length=255, help_text="e.g. 3 months, Jan - April")
    required_skills = models.TextField()
    requirements = models.TextField(help_text="List all application requirements.")
    application_method = models.CharField(
        max_length=255,
        help_text="e.g. Send CV to hr@example.com or apply via company portal URL."
    )
    application_link = models.URLField(
        blank=True,
        help_text="Optional external portal link."
    )

    positions_available = models.PositiveIntegerField(default=1, help_text="Number of attachment slots available.")
    start_date = models.DateField(null=True, blank=True, help_text="Preferred attachment start date.")
    region = models.CharField(
        max_length=255,
        blank=True,
        help_text="Region for this vacancy (if different from company HQ)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField()

    is_verified_vacancy = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['deadline']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    def clean(self):
        today = timezone.now().date()
        base_date = self.created_at.date() if self.created_at else today

        if self.deadline < base_date:
            raise ValidationError("Deadline cannot be in the past.")

        if self.deadline > base_date + timedelta(days=14):
            raise ValidationError("Deadline cannot be more than 14 days from posting date.")

        if not self.company.can_post:
            raise ValidationError("Company is not verified/approved to post vacancies.")

        if not self.company_id:
            return
        if not self.company.can_post:
            raise ValidationError("Your company is not allowed to post vacancies yet.")

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.deadline < timezone.now().date():
            self.is_active = False
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return self.deadline < timezone.now().date()

    @property
    def verification_badge(self):
        if self.is_verified_vacancy:
            return "✅ Verified Vacancy"
        if self.company.is_verified_company:
            return "✅ From Verified Company"
        if self.company.admin_approved:
            return "ℹ️ Posted by Approved Company"
        return "⚠️ Not Verified"

class JobPost(models.Model):
    JOB_TYPE_CHOICES = (
        ('FULL_TIME', 'Full-time'),
        ('PART_TIME', 'Part-time'),
        ('CONTRACT', 'Contract'),
        ('FREELANCE', 'Freelance'),
        ('INTERN', 'Internship'),
    )
    EXPERIENCE_LEVEL_CHOICES = (
        ('ENTRY', 'Entry-Level'),
        ('MID', 'Mid-Level'),
        ('SENIOR', 'Senior'),
        ('EXEC', 'Executive'),
    )
    WORK_LOCATION_CHOICES = (
        ('ONSITE', 'Onsite'),
        ('REMOTE', 'Remote'),
        ('HYBRID', 'Hybrid'),
    )
    CURRENCIES = (('KES','KES'),('USD','USD'),('EUR','EUR'),('GBP','GBP'))

    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='job_posts')

    title = models.CharField(max_length=255)
    department = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, help_text="City or town")
    region = models.CharField(max_length=255, blank=True)
    work_location_type = models.CharField(max_length=10, choices=WORK_LOCATION_CHOICES, default='ONSITE')

    job_type = models.CharField(max_length=12, choices=JOB_TYPE_CHOICES, default='FULL_TIME')
    experience_level = models.CharField(max_length=6, choices=EXPERIENCE_LEVEL_CHOICES, default='ENTRY')

    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0'))])
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0'))])
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='KES')

    responsibilities = models.TextField(help_text="5–10 bullet points", blank=True)
    benefits = models.TextField(blank=True)

    application_deadline = models.DateField(null=True, blank=True, help_text='Optional; can be longer than 14 days or left blank for open until filled')
    easy_apply = models.BooleanField(default=True)
    standard_apply = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['experience_level']),
            models.Index(fields=['job_type']),
        ]

    def __str__(self):
        return f"{self.title} at {self.company.name}"
    
class JobApplication(models.Model):
    STATUS_CHOICES = (
        ('APPLIED','Applied'),
        ('UNDER_REVIEW','Under Review'),
        ('INTERVIEW','Interviewing'),
        ('REJECTED','Rejected'),
        ('HIRED','Hired'),
    )
    job = models.ForeignKey('hub.JobPost', on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_applications')
    cover_letter = models.TextField(blank=True)
    resume_snapshot = models.FileField(upload_to='app_resumes/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPLIED')
    created_at = models.DateTimeField(auto_now_add=True)

    # NEW — declarations
    certify_truth = models.BooleanField(default=False)
    agree_at_will = models.BooleanField(default=False)

    class Meta:
        unique_together = ('job','student')
        ordering = ['-created_at']

# --- Personal & contact / eligibility / availability ---
class ApplicationPersonal(models.Model):
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name='personal')
    full_legal_name = models.CharField(max_length=255)
    previous_names = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    eligible_to_work = models.BooleanField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    preferred_schedule = models.CharField(max_length=255, blank=True)

# --- Education (repeatable) ---
class ApplicationEducation(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=255)
    degree_or_diploma = models.CharField(max_length=255, blank=True)
    field_of_study = models.CharField(max_length=255, blank=True)
    start_year = models.CharField(max_length=10, blank=True)
    end_year = models.CharField(max_length=10, blank=True)
    graduated = models.BooleanField(default=False)

class ApplicationCertification(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=255)
    issuer = models.CharField(max_length=255, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    valid_through = models.DateField(null=True, blank=True)

# --- Employment history (repeatable) ---
class ApplicationEmployment(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='employments')
    company_name = models.CharField(max_length=255)
    company_address = models.CharField(max_length=255, blank=True)
    company_phone = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    responsibilities = models.TextField(blank=True)
    supervisor_name = models.CharField(max_length=255, blank=True)
    reason_for_leaving = models.CharField(max_length=255, blank=True)

# --- References (repeatable) ---
class ApplicationReference(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='references')
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    relationship = models.CharField(max_length=255, blank=True)

# --- Custom Q&A / legal / EEO ---
class ApplicationQuestion(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='questions')
    prompt = models.CharField(max_length=255)
    answer = models.TextField()

class ApplicationCriminalHistory(models.Model):
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name='criminal_history')
    has_unspent_convictions = models.BooleanField(null=True, blank=True)
    explanation = models.TextField(blank=True)

class ApplicationReferral(models.Model):
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name='referral')
    source = models.CharField(max_length=255, blank=True)  # e.g., 'Job board', 'Referral'
    details = models.CharField(max_length=255, blank=True)

class ApplicationEEO(models.Model):
    """Voluntary; kept separate from decisioning."""
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name='eeo')
    gender = models.CharField(max_length=50, blank=True)
    ethnicity = models.CharField(max_length=100, blank=True)
    veteran_status = models.CharField(max_length=100, blank=True)

class CompanyReview(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=150)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)  # Admin moderation

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.company.name} ({self.rating}/5)"

    @staticmethod
    def average_for_company(company):
        qs = CompanyReview.objects.filter(company=company, approved=True)
        if not qs.exists():
            return None
        return round(qs.aggregate(models.Avg('rating'))['rating__avg'], 1)
