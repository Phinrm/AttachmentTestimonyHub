
# AttachmentTestimonyHub
=======
# Industrial Attachment Hub (Django)

## Features

- Company registration with:
  - Email verification
  - Admin approval
  - Verified company badge
- Only approved & verified companies can post vacancies
- Vacancies:
  - Require key details (title, department, skills, requirements, application method)
  - Deadline max 14 days from posting
  - Auto-marked inactive if expired
  - Show verification badges
- Public:
  - Can view all active vacancies without login
  - Search, filter, see verification status
  - Contact companies directly (system does not intermediate applications)
- Admin:
  - Approves companies
  - Marks companies as verified
  - Verifies/deactivates vacancies

## How to Run (Local)

1. Ensure you have **Python 3.10+** installed.

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate    # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Apply migrations:

   ```bash
   python manage.py migrate
   ```

5. Create a superuser (System Admin):

   ```bash
   python manage.py createsuperuser
   ```

6. Run the development server:

   ```bash
   python manage.py runserver
   ```

7. Open in your browser:

   - Public vacancies: `http://127.0.0.1:8000/`
   - Company registration: `http://127.0.0.1:8000/company/register/`
   - Company login: `http://127.0.0.1:8000/auth/login/`
   - Admin: `http://127.0.0.1:8000/admin/`

## Workflow

### For Companies

1. Register at `/company/register/`.
2. Check the console where `runserver` is running for the email verification link (dev mode).
3. Click the link to verify email.
4. Admin logs into `/admin/` and:
   - Approves `CompanyProfile` (admin_approved = True)
   - Optionally marks company as `is_verified_company = True`.
5. Once both email_verified + admin_approved are True, the company can:
   - Login at `/auth/login/`
   - Access dashboard at `/company/dashboard/`
   - Create vacancies at `/company/vacancy/new/`.

### For Students / Public

- Visit `/` or `/vacancies/` to see all active vacancies.
- See badges:
  - ✅ Verified Vacancy
  - ✅ From Verified Company
  - ℹ️ Posted by Approved Company
  - ⚠️ Not Verified
- Use application method or email link on vacancy detail page to reach company directly.

### For Admin

- Use `/admin/`:
  - Approve companies
  - Mark companies as verified
  - Verify/deactivate vacancies

## Notes

- Email sending uses Django console backend in development; configure SMTP for production.
- Adjust `ALLOWED_HOSTS`, `SECRET_KEY`, and database settings before deployment.

