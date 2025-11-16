from django import forms
from django.contrib.auth import get_user_model
from .models import CompanyProfile, Vacancy
from .models import StudentProfile, JobPost, JobApplication
from django.contrib.auth.forms import UserCreationForm
from .models import (
    JobApplication, ApplicationPersonal, ApplicationEducation, ApplicationCertification,
    ApplicationEmployment, ApplicationReference, ApplicationQuestion,
    ApplicationCriminalHistory, ApplicationReferral, ApplicationEEO
)
from django.forms import inlineformset_factory, modelformset_factory

User = get_user_model()


class CompanyRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CompanyProfile
        fields = [
            'name', 'registration_number', 'industry', 'location',
            'region', 'contact_person', 'official_email',
            'phone_number', 'website', 'logo', 'map_embed_url'
        ]

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already in use.")
        return email

    def save(self, commit=True):
        user = User(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            role='COMPANY',
            is_active=False,
        )
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()

        company = super().save(commit=False)
        company.user = user
        if commit:
            company.save()
        return company


class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = [
            'title', 'department', 'location', 'region', 'duration',
            'positions_available', 'start_date',
            'required_skills', 'requirements',
            'application_method', 'application_link', 'deadline'
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
        }
        exclude = ("company", "is_verified_vacancy", )

from .models import CompanyReview

class CompanyReviewForm(forms.ModelForm):
    class Meta:
        model = CompanyReview
        fields = ['name', 'rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'full_name', 'phone', 'location',
            'education_history', 'work_experience',
            'default_cover_letter', 'resume'
        ]
        widgets = {
            'education_history': forms.Textarea(attrs={'rows': 4}),
            'work_experience': forms.Textarea(attrs={'rows': 4}),
            'default_cover_letter': forms.Textarea(attrs={'rows': 5}),
        }

class JobPostForm(forms.ModelForm):
    class Meta:
        model = JobPost
        fields = [
            'title','department','location','region','work_location_type',
            'job_type','experience_level',
            'salary_min','salary_max','currency',
            'responsibilities','benefits',
            'application_deadline',
            'easy_apply','standard_apply',
        ]
        widgets = {
            'application_deadline': forms.DateInput(attrs={'type':'date'}),
            'responsibilities': forms.Textarea(attrs={'rows':6, 'placeholder':'• Bullet 1\n• Bullet 2\n• Bullet 3'}),
            'benefits': forms.Textarea(attrs={'rows':4, 'placeholder':'• Health insurance\n• PTO\n• Training budget'}),
        }

class JobEasyApplyForm(forms.ModelForm):
    use_profile_cover = forms.BooleanField(required=False, initial=True, label="Use my saved cover letter")
    class Meta:
        model = JobApplication
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 5})
        }

class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        # IMPORTANT: mark role
        user.role = "STUDENT"
        # Students can log in immediately
        user.is_active = True
        if commit:
            user.save()
        return user        
    
class ApplicationPersonalForm(forms.ModelForm):
    class Meta:
        model = ApplicationPersonal
        fields = ['full_legal_name','previous_names','phone','email','address',
                  'eligible_to_work','start_date','preferred_schedule']
        widgets = {'start_date': forms.DateInput(attrs={'type':'date'})}

EducationFormSet = inlineformset_factory(
    JobApplication, ApplicationEducation,
    fields=['institution','degree_or_diploma','field_of_study','start_year','end_year','graduated'],
    extra=1, can_delete=True
)

CertificationFormSet = inlineformset_factory(
    JobApplication, ApplicationCertification,
    fields=['name','issuer','license_number','valid_through'],
    widgets={'valid_through': forms.DateInput(attrs={'type':'date'})},
    extra=1, can_delete=True
)

EmploymentFormSet = inlineformset_factory(
    JobApplication, ApplicationEmployment,
    fields=['company_name','company_address','company_phone','job_title',
            'start_date','end_date','responsibilities','supervisor_name','reason_for_leaving'],
    widgets={'start_date': forms.DateInput(attrs={'type':'date'}),
             'end_date': forms.DateInput(attrs={'type':'date'})},
    extra=1, can_delete=True
)

ReferenceFormSet = inlineformset_factory(
    JobApplication, ApplicationReference,
    fields=['name','title','phone','email','relationship'],
    extra=2, can_delete=True
)

QuestionFormSet = inlineformset_factory(
    JobApplication, ApplicationQuestion,
    fields=['prompt','answer'],
    extra=2, can_delete=True
)

class ApplicationCriminalHistoryForm(forms.ModelForm):
    class Meta:
        model = ApplicationCriminalHistory
        fields = ['has_unspent_convictions','explanation']

class ApplicationReferralForm(forms.ModelForm):
    class Meta:
        model = ApplicationReferral
        fields = ['source','details']

class ApplicationEEOForm(forms.ModelForm):
    class Meta:
        model = ApplicationEEO
        fields = ['gender','ethnicity','veteran_status']

class ApplicationDeclarationsForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['certify_truth','agree_at_will']    