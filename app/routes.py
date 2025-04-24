from flask import render_template, request, redirect, url_for, flash, session, send_file
from flask_caching import Cache
from .services.auth_service import AuthService
from .services.testimony_service import TestimonyService
from .services.chat_service import ChatService
from .utils.report_generator import ReportGenerator
import csv
import io
from datetime import datetime

def init_routes(app, cache):
    auth = AuthService()
    testimony_service = TestimonyService()
    chat_service = ChatService()
    report_gen = ReportGenerator()

    @app.route('/')
    @cache.cached(timeout=60)
    def home():
        return render_template('home.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if auth.login(username, password):
                session['username'] = username
                return redirect(url_for('dashboard'))
            flash('Invalid credentials')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            data = {
                'full_name': request.form['full_name'],
                'age': request.form['age'],
                'dob': request.form['dob'],
                'course': request.form['course'],
                'year': request.form['year'],
                'email': request.form['email'],
                'university': request.form['university'],
                'username': request.form['username'],
                'password': request.form['password']
            }
            if auth.signup(**data):
                flash('Registration successful! Please log in.')
                return redirect(url_for('login'))
            flash('Username or email already exists')
        return render_template('register.html')

    @app.route('/forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            email = request.form['email']
            if auth.reset_password(email):
                flash('Password reset link sent to your email.')
                return redirect(url_for('login'))
            flash('Email not found')
        return render_template('login.html', forgot=True)

    @app.route('/dashboard')
    @cache.cached(timeout=60)
    def dashboard():
        if 'username' not in session:
            return redirect(url_for('login'))
        user_data = auth.get_user_data(session['username'])
        return render_template('dashboard.html', user=user_data)

    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        if 'username' not in session:
            return redirect(url_for('login'))
        user_data = auth.get_user_data(session['username'])
        if request.method == 'POST':
            if 'update' in request.form:
                auth.update_profile(session['username'], request.form['email'])
                flash('Profile updated!')
            elif 'delete' in request.form:
                auth.delete_account(session['username'])
                session.pop('username', None)
                flash('Account deleted!')
                return redirect(url_for('home'))
        return render_template('profile.html', user=user_data)

    @app.route('/testimonies', methods=['GET', 'POST'])
    def testimonies():
        if request.method == 'POST':
            if 'username' not in session:
                flash('Please log in to submit a testimony.')
                return redirect(url_for('login'))
            data = {
                'username': session['username'],
                'full_name': request.form['full_name'],
                'company': request.form['company'],
                'company_email': request.form['company_email'],
                'university': request.form['university'],
                'start_date': request.form['start_date'],
                'end_date': request.form['end_date'],
                'department': request.form['department'],
                'rating': request.form['rating'],
                'notes': request.form['notes']
            }
            testimony_service.submit_testimony(**data)
            flash('Testimony submitted!')
        testimonies = testimony_service.get_all_testimonies()
        return render_template('testimonies.html', testimonies=testimonies)

    @app.route('/search', methods=['GET'])
    def search():
        query = request.args.get('q', '')
        testimonies = testimony_service.search_testimonies(query)
        return render_template('testimonies.html', testimonies=testimonies, query=query)

    @app.route('/help', methods=['GET', 'POST'])
    def help():
        if 'username' not in session:
            return redirect(url_for('login'))
        chat_history = session.get('chat_history', [])
        if request.method == 'POST':
            message = request.form['message']
            response = chat_service.get_response(message)
            chat_history.append(('You', message))
            chat_history.append(('Assistant', response))
            session['chat_history'] = chat_history
        return render_template('help.html', chat_history=chat_history)

    @app.route('/logout')
    def logout():
        session.pop('username', None)
        session.pop('chat_history', None)
        return redirect(url_for('home'))

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if username == 'admin' and password == 'admin123':
                session['admin'] = True
                conn = testimony_service.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                               ('admin', 'admin_login', 'Admin logged in'))
                conn.commit()
                conn.close()
                return redirect(url_for('admin_dashboard'))
            flash('Invalid admin credentials')
        return render_template('admin/login.html')

    @app.route('/admin/dashboard')
    @cache.cached(timeout=60)
    def admin_dashboard():
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return render_template('admin/dashboard.html')

    @app.route('/admin/users', methods=['GET', 'POST'])
    def manage_users():
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        if request.method == 'POST':
            if 'add' in request.form:
                data = {k: request.form[k] for k in ['full_name', 'age', 'dob', 'course', 'year', 'email', 'university', 'username', 'password']}
                auth.signup(**data)
                flash('User added!')
            elif 'modify' in request.form:
                user_id = request.form['user_id']
                data = {k: request.form[k] for k in ['full_name', 'age', 'dob', 'course', 'year', 'email', 'university', 'username', 'password']}
                auth.admin_update_user(user_id, **data)
                flash('User updated!')
            elif 'delete' in request.form:
                auth.admin_delete_user(request.form['user_id'])
                flash('User deleted!')
        users = auth.get_all_users()
        return render_template('admin/manage_users.html', users=users)

    @app.route('/admin/testimonies', methods=['GET', 'POST'])
    def manage_testimonies():
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        if request.method == 'POST':
            if 'add' in request.form:
                data = {k: request.form[k] for k in ['username', 'full_name', 'company', 'company_email', 'university', 'start_date', 'end_date', 'department', 'rating', 'notes']}
                testimony_service.submit_testimony(**data)
                flash('Testimony added!')
            elif 'modify' in request.form:
                testimony_id = request.form['testimony_id']
                data = {k: request.form[k] for k in ['username', 'full_name', 'company', 'company_email', 'university', 'start_date', 'end_date', 'department', 'rating', 'notes']}
                testimony_service.admin_update_testimony(testimony_id, **data)
                flash('Testimony updated!')
            elif 'delete' in request.form:
                testimony_service.admin_delete_testimony(request.form['testimony_id'])
                flash('Testimony deleted!')
        testimonies = testimony_service.get_all_testimonies()
        return render_template('admin/manage_testimonies.html', testimonies=testimonies)

    @app.route('/admin/download/users')
    def download_users():
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        users = auth.get_all_users()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Full Name', 'Email', 'Username'])
        for user in users:
            writer.writerow(user)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'users_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/admin/download/testimonies')
    def download_testimonies():
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        testimonies = testimony_service.get_all_testimonies()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Username', 'Full Name', 'Company', 'Company Email', 'University', 'Start Date', 'End Date', 'Department', 'Rating', 'Notes', 'Timestamp'])
        for t in testimonies:
            writer.writerow(t)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'testimonies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/admin/download/logs')
    def download_logs():
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        logs = testimony_service.get_all_logs()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Username', 'Action', 'Details', 'Timestamp'])
        for log in logs:
            writer.writerow(log)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/admin/download/all')
    def download_all():
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        users = auth.get_all_users()
        testimonies = testimony_service.get_all_testimonies()
        logs = testimony_service.get_all_logs()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Users'])
        writer.writerow(['ID', 'Full Name', 'Email', 'Username'])
        for user in users:
            writer.writerow(user)
        writer.writerow([])
        writer.writerow(['Testimonies'])
        writer.writerow(['ID', 'Username', 'Full Name', 'Company', 'Company Email', 'University', 'Start Date', 'End Date', 'Department', 'Rating', 'Notes', 'Timestamp'])
        for t in testimonies:
            writer.writerow(t)
        writer.writerow([])
        writer.writerow(['Logs'])
        writer.writerow(['ID', 'Username', 'Action', 'Details', 'Timestamp'])
        for log in logs:
            writer.writerow(log)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'all_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/admin/logout')
    def admin_logout():
        if 'admin' in session:
            conn = testimony_service.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO logs (username, action, details) VALUES (?, ?, ?)",
                           ('admin', 'admin_logout', 'Admin logged out'))
            conn.commit()
            conn.close()
        session.pop('admin', None)
        return redirect(url_for('admin_login'))