import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import text
import os
import json
from io import BytesIO
import csv
from models import *

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:password@mysql-service:3306/testmanagement')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration to handle localhost and 127.0.0.1
app.config['SESSION_COOKIE_DOMAIN'] = None  # Allow cookies on any domain
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_COOKIE_NAME'] = 'test_management_session'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
app.config['UPLOAD_FOLDER'] = 'uploads'

# Session timeout configuration (30 minutes of inactivity)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.config['SESSION_TIMEOUT_MINUTES'] = 30

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add middleware to handle localhost/127.0.0.1 session sharing
@app.before_request
def before_request():
    # Make session permanent to ensure it persists
    session.permanent = True
    
    # Add CORS headers for development
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response

@app.after_request
def after_request(response):
    # Add CORS headers for development
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', '*')
    response.headers.add('Access-Control-Allow-Methods', '*')
    
    # Ensure session cookies work with both localhost and 127.0.0.1
    if 'Set-Cookie' in response.headers:
        # Modify cookie to work with both domains
        cookies = response.headers.getlist('Set-Cookie')
        response.headers.pop('Set-Cookie')
        for cookie in cookies:
            # Remove domain restriction for development
            if 'Domain=' in cookie:
                cookie = cookie.split('Domain=')[0] + cookie.split('Domain=')[1].split(';', 1)[1] if ';' in cookie.split('Domain=')[1] else ''
            response.headers.add('Set-Cookie', cookie)
    
    return response
login_manager.login_message = 'Your session has expired. Please log in again.'
login_manager.login_message_category = 'warning'

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Session timeout functionality
@app.before_request
def check_session_timeout():
    """Check if user session has expired due to inactivity"""
    
    # Skip timeout check for static files and login/logout routes
    if (request.endpoint and 
        (request.endpoint.startswith('static') or 
         request.endpoint in ['login', 'logout', 'signup', 'check_session_status', 'extend_session'])):
        return
    
    # Skip if user is not logged in
    if not current_user.is_authenticated:
        return
    
    # Check if session has last_activity timestamp
    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        timeout_duration = timedelta(minutes=app.config['SESSION_TIMEOUT_MINUTES'])
        
        # Check if session has expired
        if datetime.now() - last_activity > timeout_duration:
            # Clear the session
            session.clear()
            logout_user()
            flash('Your session has expired due to inactivity. Please log in again.', 'warning')
            return redirect(url_for('login'))
    
    # Update last activity timestamp
    session['last_activity'] = datetime.now().isoformat()
    session.permanent = True

@app.route('/check-session-status')
@login_required
def check_session_status():
    """API endpoint to check session status for client-side timeout warnings"""
    if 'last_activity' in session:
        last_activity = datetime.fromisoformat(session['last_activity'])
        timeout_duration = timedelta(minutes=app.config['SESSION_TIMEOUT_MINUTES'])
        time_remaining = timeout_duration - (datetime.now() - last_activity)
        
        return jsonify({
            'authenticated': True,
            'time_remaining_seconds': int(time_remaining.total_seconds()),
            'timeout_minutes': app.config['SESSION_TIMEOUT_MINUTES']
        })
    
    return jsonify({
        'authenticated': False,
        'time_remaining_seconds': 0,
        'timeout_minutes': app.config['SESSION_TIMEOUT_MINUTES']
    })

@app.route('/extend-session', methods=['POST'])
@login_required
def extend_session():
    """API endpoint to extend user session"""
    # Update last activity timestamp to extend session
    session['last_activity'] = datetime.now().isoformat()
    session.permanent = True
    
    return jsonify({
        'success': True,
        'message': 'Session extended successfully',
        'new_timeout_minutes': app.config['SESSION_TIMEOUT_MINUTES']
    })

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact administrator.', 'error')
                return render_template('login.html')
            
            login_user(user)
            
            # Set session as permanent and initialize activity timestamp
            session.permanent = True
            session['last_activity'] = datetime.now().isoformat()
            session['login_time'] = datetime.now().isoformat()
            
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'tester')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('signup.html')
        
        # IMPORTANT: Prevent multiple admin creation
        if role == 'admin':
            existing_admin = User.query.filter_by(role='admin').first()
            if existing_admin:
                flash('Admin already exists. Only one admin is allowed in the system.', 'error')
                return render_template('signup.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        # Set session as permanent and initialize activity timestamp
        session.permanent = True
        session['last_activity'] = datetime.now().isoformat()
        session['login_time'] = datetime.now().isoformat()
        
        flash('Account created successfully', 'success')
        return redirect(url_for('dashboard'))
    
    # Check if admin exists for signup form
    admin_exists = User.query.filter_by(role='admin').first() is not None
    return render_template('signup.html', admin_exists=admin_exists)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_test_cases': TestCase.query.count(),
        'total_executions': TestExecution.query.count(),
        'total_bugs': Bug.query.count(),
        'pass_rate': 0
    }
    
    total_executions = TestExecution.query.count()
    if total_executions > 0:
        passed_executions = TestExecution.query.filter_by(status='Pass').count()
        stats['pass_rate'] = round((passed_executions / total_executions) * 100, 2)
    
    recent_executions = TestExecution.query.order_by(TestExecution.execution_date.desc()).limit(5).all()
    
    return render_template('dashboard.html', stats=stats, recent_executions=recent_executions)

@app.route('/projects')
@login_required
def projects():
    projects = Project.query.all()
    return render_template('projects.html', projects=projects)

@app.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    if request.method == 'POST':
        project = Project(
            name=request.form['name'],
            description=request.form['description'],
            created_by=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully')
        return redirect(url_for('projects'))
    
    return render_template('create_project.html')

@app.route('/test-suites')
@login_required
def test_suites():
    suites = TestSuite.query.all()
    projects = Project.query.all()
    return render_template('test_suites.html', suites=suites, projects=projects)

@app.route('/test-suites/create', methods=['GET', 'POST'])
@login_required
def create_test_suite():
    if request.method == 'POST':
        suite = TestSuite(
            name=request.form['name'],
            description=request.form['description'],
            project_id=request.form['project_id']
        )
        db.session.add(suite)
        db.session.commit()
        flash('Test suite created successfully')
        return redirect(url_for('test_suites'))
    
    projects = Project.query.all()
    return render_template('create_test_suite.html', projects=projects)

@app.route('/test-cases')
@login_required
def test_cases():
    cases = TestCase.query.all()
    return render_template('test_cases.html', cases=cases)

@app.route('/test-cases/create', methods=['GET', 'POST'])
@login_required
def create_test_case():
    if request.method == 'POST':
        test_case = TestCase(
            title=request.form['title'],
            description=request.form['description'],
            preconditions=request.form['preconditions'],
            test_steps=request.form['test_steps'],
            expected_result=request.form['expected_result'],
            test_data=request.form['test_data'],
            priority=request.form['priority'],
            suite_id=request.form['suite_id'],
            created_by=current_user.id
        )
        db.session.add(test_case)
        db.session.commit()
        flash('Test case created successfully')
        
        # If suite_id was provided, redirect back to the suite's test cases page
        if request.form.get('suite_id'):
            return redirect(url_for('test_suite_test_cases', suite_id=request.form['suite_id']))
        else:
            return redirect(url_for('test_cases'))
    
    suites = TestSuite.query.all()
    # Get the pre-selected suite_id from URL parameters
    selected_suite_id = request.args.get('suite_id', type=int)
    return render_template('create_test_case.html', suites=suites, selected_suite_id=selected_suite_id)

@app.route('/test-cases/<int:case_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_test_case(case_id):
    test_case = TestCase.query.get_or_404(case_id)
    
    if request.method == 'POST':
        test_case.title = request.form['title']
        test_case.description = request.form['description']
        test_case.preconditions = request.form['preconditions']
        test_case.test_steps = request.form['test_steps']
        test_case.expected_result = request.form['expected_result']
        test_case.test_data = request.form['test_data']
        test_case.priority = request.form['priority']
        test_case.suite_id = request.form['suite_id']
        test_case.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Test case updated successfully')
        return redirect(url_for('test_cases'))
    
    suites = TestSuite.query.all()
    return render_template('edit_test_case.html', test_case=test_case, suites=suites)

@app.route('/test-cases/<int:case_id>/delete', methods=['POST'])
@login_required
def delete_test_case(case_id):
    try:
        test_case = TestCase.query.get_or_404(case_id)
        db.session.delete(test_case)
        db.session.commit()
        
        # Check if it's an AJAX request
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': True, 'message': 'Test case deleted successfully'})
        else:
            flash('Test case deleted successfully')
            return redirect(url_for('test_cases'))
    except Exception as e:
        if request.headers.get('Content-Type') == 'application/json':
            return jsonify({'success': False, 'message': str(e)})
        else:
            flash(f'Error deleting test case: {str(e)}', 'error')
            return redirect(url_for('test_cases'))

@app.route('/test-cases/<int:case_id>/execute', methods=['GET', 'POST'])
@login_required
def execute_test_case(case_id):
    test_case = TestCase.query.get_or_404(case_id)
    
    if request.method == 'POST':
        execution = TestExecution(
            test_case_id=case_id,
            executed_by=current_user.id,
            status=request.form['status'],
            actual_result=request.form['actual_result'],
            comments=request.form['comments'],
            environment=request.form['environment']
        )
        db.session.add(execution)
        db.session.commit()
        
        if request.form['status'] == 'Fail' and request.form.get('create_bug'):
            bug = Bug(
                title=f"Bug from test case: {test_case.title}",
                description=request.form['actual_result'],
                test_case_id=case_id,
                reported_by=current_user.id
            )
            db.session.add(bug)
            db.session.commit()
        
        flash('Test execution recorded successfully')
        return redirect(url_for('test_cases'))
    
    return render_template('execute_test_case.html', test_case=test_case)

@app.route('/bugs')
@login_required
def bugs():
    bugs = Bug.query.all()
    return render_template('bugs.html', bugs=bugs)

@app.route('/reports')
@login_required
def reports():
    if current_user.role not in ['manager', 'admin']:
        flash('Access denied')
        return redirect(url_for('dashboard'))
    
    # Generate report data
    total_cases = TestCase.query.count()
    total_executions = TestExecution.query.count()
    passed = TestExecution.query.filter_by(status='Pass').count()
    failed = TestExecution.query.filter_by(status='Fail').count()
    blocked = TestExecution.query.filter_by(status='Blocked').count()
    
    pass_rate = (passed / total_executions * 100) if total_executions > 0 else 0
    
    report_data = {
        'total_cases': total_cases,
        'total_executions': total_executions,
        'passed': passed,
        'failed': failed,
        'blocked': blocked,
        'pass_rate': round(pass_rate, 2)
    }
    
    return render_template('reports.html', report_data=report_data)

@app.route('/admin')
@login_required
def admin():
    # Only admin can access admin panel
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    user_stats = {
        'total_users': len(users),
        'active_users': len([u for u in users if u.is_active]),
        'admins': len([u for u in users if u.role == 'admin']),
        'managers': len([u for u in users if u.role == 'manager']),
        'developers': len([u for u in users if u.role == 'developer']),
        'testers': len([u for u in users if u.role == 'tester'])
    }
    return render_template('admin.html', users=users, user_stats=user_stats)

@app.route('/admin/create-user', methods=['GET', 'POST'])
@login_required
def admin_create_user():
    # Only admin can create users
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        # Prevent creating multiple admins
        if role == 'admin':
            flash('Cannot create another admin. Only one admin is allowed.', 'error')
            return render_template('admin_create_user.html')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('admin_create_user.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('admin_create_user.html')
        
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        flash(f'{role.title()} account created successfully', 'success')
        return redirect(url_for('admin'))
    
    return render_template('admin_create_user.html')

@app.route('/projects/<int:project_id>/test-cases')
@login_required
def project_test_cases(project_id):
    project = Project.query.get_or_404(project_id)
    test_cases = TestCase.query.filter_by(project_id=project_id).all()
    test_suites = TestSuite.query.filter_by(project_id=project_id).all()
    return render_template('project_test_cases.html', project=project, test_cases=test_cases, test_suites=test_suites)

@app.route('/projects/<int:project_id>/reports')
@login_required
def project_reports(project_id):
    project = Project.query.get_or_404(project_id)
    
    # Get project statistics
    total_test_cases = TestCase.query.filter_by(project_id=project_id).count()
    total_executions = TestExecution.query.join(TestCase).filter(TestCase.project_id == project_id).count()
    passed_executions = TestExecution.query.join(TestCase).filter(
        TestCase.project_id == project_id, 
        TestExecution.status == 'Pass'
    ).count()
    failed_executions = TestExecution.query.join(TestCase).filter(
        TestCase.project_id == project_id, 
        TestExecution.status == 'Fail'
    ).count()
    total_bugs = Bug.query.join(TestCase).filter(TestCase.project_id == project_id).count()
    total_requirements = Requirement.query.filter_by(project_id=project_id).count()
    
    stats = {
        'total_test_cases': total_test_cases,
        'total_executions': total_executions,
        'passed_executions': passed_executions,
        'failed_executions': failed_executions,
        'total_bugs': total_bugs,
        'total_requirements': total_requirements,
        'pass_rate': (passed_executions / total_executions * 100) if total_executions > 0 else 0
    }
    
    return render_template('project_reports.html', project=project, stats=stats)

@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project.name = request.form['name']
        project.description = request.form['description']
        project.status = request.form.get('status', 'Active')
        db.session.commit()
        flash('Project updated successfully', 'success')
        return redirect(url_for('projects'))
    
    return render_template('edit_project.html', project=project)

@app.route('/projects/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_projects():
    try:
        # Check if user has permission
        if current_user.role not in ['admin', 'manager']:
            return jsonify({'success': False, 'message': 'Access denied. Only admin and manager can bulk delete projects.'})
        
        data = request.get_json()
        project_ids = data.get('project_ids', [])
        
        if not project_ids:
            return jsonify({'success': False, 'message': 'No projects selected'})
        
        deleted_count = 0
        for project_id in project_ids:
            project = Project.query.get(project_id)
            if project:
                # Allow admin/manager or project creator to delete
                if current_user.role in ['admin', 'manager'] or project.created_by == current_user.id:
                    db.session.delete(project)
                    deleted_count += 1
        
        db.session.commit()
        return jsonify({'success': True, 'deleted_count': deleted_count, 'message': f'Successfully deleted {deleted_count} project(s)'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting projects: {str(e)}'})

@app.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    try:
        # Check if user has permission (admin, manager, or project owner)
        project = Project.query.get_or_404(project_id)
        
        # Allow admin, manager, or project creator to delete
        if current_user.role not in ['admin', 'manager'] and project.created_by != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied. Only admin, manager, or project creator can delete projects.'})
        
        # FIXED: Enhanced deletion logic with proper order to handle foreign key constraints
        
        # 1. First, get all test cases for this project
        test_case_ids = [tc[0] for tc in db.session.execute(
            text("SELECT id FROM test_case WHERE project_id = :project_id"), 
            {'project_id': project_id}
        ).fetchall()]
        
        # 2. Delete test executions (they reference test cases)
        for test_case_id in test_case_ids:
            try:
                db.session.execute(text("DELETE FROM test_execution WHERE test_case_id = :test_case_id"), 
                                 {'test_case_id': test_case_id})
            except:
                pass  # Handle missing columns gracefully
        
        # 3. Delete bugs (they reference test cases)
        for test_case_id in test_case_ids:
            try:
                db.session.execute(text("DELETE FROM bug WHERE test_case_id = :test_case_id"), 
                                 {'test_case_id': test_case_id})
            except:
                pass
        
        # 4. Delete assignments (they might reference test cases or project)
        try:
            db.session.execute(text("DELETE FROM assignment WHERE project_id = :project_id"), 
                             {'project_id': project_id})
        except:
            # Fallback - delete assignments related to test cases
            for test_case_id in test_case_ids:
                try:
                    db.session.execute(text("DELETE FROM assignment WHERE test_case_id = :test_case_id"), 
                                     {'test_case_id': test_case_id})
                except:
                    pass
        
        # 5. Delete requirements (they reference project)
        try:
            db.session.execute(text("DELETE FROM requirement WHERE project_id = :project_id"), 
                             {'project_id': project_id})
        except:
            pass  # Requirements table might not exist
        
        # 6. Delete test cases (they reference project and test suites)
        try:
            db.session.execute(text("DELETE FROM test_case WHERE project_id = :project_id"), 
                             {'project_id': project_id})
        except:
            pass
        
        # 7. CRITICAL: Delete test suites BEFORE deleting project (they reference project)
        try:
            db.session.execute(text("DELETE FROM test_suite WHERE project_id = :project_id"), 
                             {'project_id': project_id})
        except Exception as e:
            print(f"Error deleting test suites: {e}")
            pass
        
        # 8. Finally delete the project (no more foreign key references should exist)
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Project and all related data deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Project deletion error: {e}")  # For debugging
        return jsonify({'success': False, 'message': f'Error deleting project: {str(e)}'})

@app.route('/test-suites/<int:suite_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_test_suite(suite_id):
    suite = TestSuite.query.get_or_404(suite_id)
    
    if request.method == 'POST':
        suite.name = request.form['name']
        suite.description = request.form['description']
        suite.project_id = request.form['project_id']
        db.session.commit()
        flash('Test suite updated successfully', 'success')
        return redirect(url_for('test_suites'))
    
    projects = Project.query.all()
    return render_template('edit_test_suite.html', suite=suite, projects=projects)

@app.route('/test-suites/<int:suite_id>/delete', methods=['POST'])
@login_required
def delete_test_suite(suite_id):
    try:
        suite = TestSuite.query.get_or_404(suite_id)
        db.session.delete(suite)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Test suite deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/test-suites/<int:suite_id>/test-cases')
@login_required
def test_suite_test_cases(suite_id):
    """Show test cases for a specific test suite"""
    suite = TestSuite.query.get_or_404(suite_id)
    
    # Get test cases that belong to this suite (checking both suite_id and test_suite_id fields)
    test_cases = TestCase.query.filter(
        db.or_(TestCase.suite_id == suite_id, TestCase.test_suite_id == suite_id)
    ).all()
    
    # Get all test suites for the dropdown (in case user wants to move test cases)
    all_suites = TestSuite.query.filter_by(project_id=suite.project_id).all()
    
    return render_template('test_suite_test_cases.html', 
                         suite=suite, 
                         test_cases=test_cases, 
                         all_suites=all_suites)

@app.route('/test-cases/<int:case_id>/duplicate', methods=['POST'])
@login_required
def duplicate_test_case(case_id):
    try:
        original_case = TestCase.query.get_or_404(case_id)
        
        new_case = TestCase(
            title=f"Copy of {original_case.title}",
            description=original_case.description,
            steps=original_case.steps,
            expected_result=original_case.expected_result,
            priority=original_case.priority,
            type=original_case.type,
            project_id=original_case.project_id,
            test_suite_id=original_case.test_suite_id,
            created_by=current_user.id
        )
        
        db.session.add(new_case)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Test case duplicated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/test-cases/<int:case_id>/delete', methods=['POST'])
@login_required
def delete_test_case_ajax(case_id):
    try:
        test_case = TestCase.query.get_or_404(case_id)
        db.session.delete(test_case)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Test case deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/cleanup-admins', methods=['POST'])
@login_required
def cleanup_admins():
    # Only admin can cleanup
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied'})
    
    try:
        # Get all admin users
        admin_users = User.query.filter_by(role='admin').all()
        
        if len(admin_users) <= 1:
            return jsonify({'success': True, 'message': 'Only one admin exists, no cleanup needed'})
        
        # Keep the current admin and delete others
        for admin in admin_users:
            if admin.id != current_user.id:
                db.session.delete(admin)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Cleaned up {len(admin_users) - 1} extra admin accounts'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    # Only admin can toggle user status
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('You cannot deactivate your own admin account', 'error')
        return redirect(url_for('admin'))
    
    # Prevent deactivating the only admin
    if user.role == 'admin':
        flash('Cannot deactivate the admin account', 'error')
        return redirect(url_for('admin'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}', 'success')
    return redirect(url_for('admin'))

# Additional routes
@app.route('/requirements')
@login_required
def requirements():
    requirements = Requirement.query.all()
    projects = Project.query.all()
    return render_template('requirements.html', requirements=requirements, projects=projects)

@app.route('/requirements/create', methods=['GET', 'POST'])
@login_required
def create_requirement():
    if request.method == 'POST':
        requirement = Requirement(
            title=request.form['title'],
            description=request.form['description'],
            type=request.form['type'],
            priority=request.form['priority'],
            project_id=request.form['project_id'],
            created_by=current_user.id
        )
        db.session.add(requirement)
        db.session.commit()
        flash('Requirement created successfully', 'success')
        return redirect(url_for('requirements'))
    
    projects = Project.query.all()
    return render_template('create_requirement.html', projects=projects)

@app.route('/bugs/<int:bug_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_bug(bug_id):
    bug = Bug.query.get_or_404(bug_id)
    
    if request.method == 'POST':
        bug.title = request.form['title']
        bug.description = request.form['description']
        bug.severity = request.form['severity']
        bug.priority = request.form['priority']
        bug.status = request.form['status']
        bug.type = request.form['type']
        db.session.commit()
        flash('Bug updated successfully', 'success')
        return redirect(url_for('bugs'))
    
    test_cases = TestCase.query.all()
    return render_template('edit_bug.html', bug=bug, test_cases=test_cases)

@app.route('/bugs/<int:bug_id>/update-status', methods=['POST'])
@login_required
def update_bug_status(bug_id):
    try:
        data = request.get_json()
        bug = Bug.query.get_or_404(bug_id)
        bug.status = data.get('status')
        db.session.commit()
        
        # Add comment if provided
        if data.get('comments'):
            comment = Comment(
                content=data.get('comments'),
                bug_id=bug_id,
                created_by=current_user.id
            )
            db.session.add(comment)
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Bug status updated successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/bugs/<int:bug_id>/delete', methods=['POST'])
@login_required
def delete_bug(bug_id):
    try:
        bug = Bug.query.get_or_404(bug_id)
        db.session.delete(bug)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Bug deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/assignments/<int:assignment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    
    if request.method == 'POST':
        assignment.title = request.form['title']
        assignment.description = request.form['description']
        assignment.priority = request.form['priority']
        assignment.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d') if request.form['due_date'] else None
        db.session.commit()
        flash('Assignment updated successfully', 'success')
        return redirect(url_for('assignments'))
    
    users = User.query.filter_by(is_active=True).all()
    return render_template('edit_assignment.html', assignment=assignment, users=users)

@app.route('/assignments/<int:assignment_id>/complete', methods=['POST'])
@login_required
def complete_assignment(assignment_id):
    try:
        assignment = Assignment.query.get_or_404(assignment_id)
        assignment.status = 'Completed'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Assignment marked as complete'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/requirements/<int:req_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_requirement(req_id):
    requirement = Requirement.query.get_or_404(req_id)
    
    if request.method == 'POST':
        requirement.title = request.form['title']
        requirement.description = request.form['description']
        requirement.type = request.form['type']
        requirement.priority = request.form['priority']
        requirement.project_id = request.form['project_id']
        db.session.commit()
        flash('Requirement updated successfully', 'success')
        return redirect(url_for('requirements'))
    
    projects = Project.query.all()
    return render_template('edit_requirement.html', requirement=requirement, projects=projects)

@app.route('/test-executions')
@login_required
def test_executions():
    executions = TestExecution.query.order_by(TestExecution.execution_date.desc()).all()
    return render_template('test_executions.html', executions=executions)

@app.route('/assignments')
@login_required
def assignments():
    if current_user.role not in ['manager', 'admin']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    assignments = Assignment.query.all()
    users = User.query.filter_by(is_active=True).all()
    return render_template('assignments.html', assignments=assignments, users=users)

@app.route('/assignments/create', methods=['GET', 'POST'])
@login_required
def create_assignment():
    if current_user.role not in ['manager', 'admin']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        assignment = Assignment(
            title=request.form['title'],
            description=request.form['description'],
            type=request.form['type'],
            assigned_to=request.form['assigned_to'],
            assigned_by=current_user.id,
            due_date=datetime.strptime(request.form['due_date'], '%Y-%m-%d') if request.form['due_date'] else None,
            priority=request.form['priority'],
            test_case_id=request.form.get('test_case_id') if request.form.get('test_case_id') else None,
            bug_id=request.form.get('bug_id') if request.form.get('bug_id') else None
        )
        db.session.add(assignment)
        db.session.commit()
        
        # Create notification
        notification = Notification(
            title='New Assignment',
            message=f'You have been assigned: {assignment.title}',
            type='info',
            user_id=assignment.assigned_to
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Assignment created successfully', 'success')
        return redirect(url_for('assignments'))
    
    users = User.query.filter_by(is_active=True).all()
    test_cases = TestCase.query.all()
    bugs = Bug.query.all()
    return render_template('create_assignment.html', users=users, test_cases=test_cases, bugs=bugs)

@app.route('/api/add-execution-comment', methods=['POST'])
@login_required
def add_execution_comment():
    try:
        data = request.get_json()
        execution_id = data.get('execution_id')
        comment_text = data.get('comment')
        
        if not execution_id or not comment_text:
            return jsonify({'success': False, 'message': 'Missing required data'})
        
        comment = Comment(
            content=comment_text,
            test_execution_id=execution_id,
            created_by=current_user.id
        )
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Comment added successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/bugs/create', methods=['GET', 'POST'])
@login_required
def create_bug():
    if request.method == 'POST':
        bug = Bug(
            title=request.form['title'],
            description=request.form['description'],
            severity=request.form['severity'],
            priority=request.form['priority'],
            type=request.form.get('type', 'Functional'),
            test_case_id=request.form.get('test_case_id') if request.form.get('test_case_id') else None,
            steps_to_reproduce=request.form.get('steps_to_reproduce'),
            expected_result=request.form.get('expected_result'),
            actual_result=request.form.get('actual_result'),
            environment=request.form.get('environment'),
            status='Open',
            reported_by=current_user.id
        )
        db.session.add(bug)
        db.session.commit()
        flash('Bug reported successfully', 'success')
        return redirect(url_for('bugs'))
    
    execution_id = request.args.get('execution_id')
    test_cases = TestCase.query.all()
    return render_template('create_bug.html', execution_id=execution_id, test_cases=test_cases)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied. Only admin can delete users.'})
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent admin from deleting themselves
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'You cannot delete your own account.'})
        
        # Enhanced deletion logic to handle legacy data and missing foreign keys
        
        # 1. Delete test executions created by this user (handle missing executed_by column)
        try:
            db.session.execute(text("DELETE FROM test_execution WHERE executed_by = :user_id"), 
                             {'user_id': user_id})
        except:
            # Column might not exist in legacy data, skip
            pass
        
        # 2. Delete bugs reported by this user (handle missing reported_by column)
        try:
            db.session.execute(text("DELETE FROM bug WHERE reported_by = :user_id"), 
                             {'user_id': user_id})
        except:
            # Column might not exist in legacy data, skip
            pass
        
        # 3. Delete assignments assigned to this user
        try:
            db.session.execute(text("DELETE FROM assignment WHERE assigned_to = :user_id"), 
                             {'user_id': user_id})
        except:
            # Handle legacy data without proper foreign keys
            pass
        
        # 4. Delete assignments created by this user (handle missing created_by column)
        try:
            db.session.execute(text("DELETE FROM assignment WHERE created_by = :user_id"), 
                             {'user_id': user_id})
        except:
            # Column might not exist in legacy data, skip
            pass
        
        # 5. Update test cases assigned to this user (set to NULL) - handle missing columns
        try:
            db.session.execute(text("UPDATE test_case SET assigned_to = NULL WHERE assigned_to = :user_id"), 
                             {'user_id': user_id})
        except:
            # Column might not exist in legacy data, skip
            pass
        
        # 6. Update test cases created by this user (set to NULL) - handle missing columns
        try:
            db.session.execute(text("UPDATE test_case SET created_by = NULL WHERE created_by = :user_id"), 
                             {'user_id': user_id})
        except:
            # Column might not exist in legacy data, skip
            pass
        
        # 7. Update projects created by this user (set to NULL) - handle missing columns
        try:
            db.session.execute(text("UPDATE project SET created_by = NULL WHERE created_by = :user_id"), 
                             {'user_id': user_id})
        except:
            # Column might not exist in legacy data, skip
            pass
        
        # 8. Handle any other legacy references
        try:
            # Update any other tables that might reference this user
            db.session.execute(text("UPDATE bug SET assigned_to = NULL WHERE assigned_to = :user_id"), 
                             {'user_id': user_id})
        except:
            pass
        
        # 9. Finally delete the user
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'User "{user.username}" and all related data deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting user: {str(e)}'})

@app.route('/admin/users/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_users():
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Access denied. Only admin can delete users.'})
    
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        if not user_ids:
            return jsonify({'success': False, 'message': 'No users selected'})
        
        # Prevent admin from deleting themselves
        if current_user.id in user_ids:
            return jsonify({'success': False, 'message': 'You cannot delete your own account.'})
        
        deleted_count = 0
        errors = []
        
        for user_id in user_ids:
            try:
                user = User.query.get(user_id)
                if user and user.id != current_user.id:
                    # Enhanced deletion logic to handle legacy data
                    
                    # Delete related records with error handling for missing columns
                    try:
                        db.session.execute(text("DELETE FROM test_execution WHERE executed_by = :user_id"), 
                                         {'user_id': user_id})
                    except:
                        pass
                    
                    try:
                        db.session.execute(text("DELETE FROM bug WHERE reported_by = :user_id"), 
                                         {'user_id': user_id})
                    except:
                        pass
                    
                    try:
                        db.session.execute(text("DELETE FROM assignment WHERE assigned_to = :user_id"), 
                                         {'user_id': user_id})
                    except:
                        pass
                    
                    try:
                        db.session.execute(text("DELETE FROM assignment WHERE created_by = :user_id"), 
                                         {'user_id': user_id})
                    except:
                        pass
                    
                    try:
                        db.session.execute(text("UPDATE test_case SET assigned_to = NULL WHERE assigned_to = :user_id"), 
                                         {'user_id': user_id})
                    except:
                        pass
                    
                    try:
                        db.session.execute(text("UPDATE test_case SET created_by = NULL WHERE created_by = :user_id"), 
                                         {'user_id': user_id})
                    except:
                        pass
                    
                    try:
                        db.session.execute(text("UPDATE project SET created_by = NULL WHERE created_by = :user_id"), 
                                         {'user_id': user_id})
                    except:
                        pass
                    
                    try:
                        db.session.execute(text("UPDATE bug SET assigned_to = NULL WHERE assigned_to = :user_id"), 
                                         {'user_id': user_id})
                    except:
                        pass
                    
                    db.session.delete(user)
                    deleted_count += 1
            except Exception as e:
                errors.append(f"Error deleting user {user_id}: {str(e)}")
        
        db.session.commit()
        
        if errors:
            return jsonify({
                'success': True, 
                'deleted_count': deleted_count, 
                'message': f'Successfully deleted {deleted_count} user(s). Some errors occurred: {"; ".join(errors[:3])}'
            })
        else:
            return jsonify({
                'success': True, 
                'deleted_count': deleted_count, 
                'message': f'Successfully deleted {deleted_count} user(s)'
            })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting users: {str(e)}'})

@app.route('/test-executions/<int:execution_id>/delete', methods=['POST'])
@login_required
def delete_test_execution(execution_id):
    try:
        execution = TestExecution.query.get_or_404(execution_id)
        
        # Check permissions - admin, manager, or execution creator can delete
        if current_user.role not in ['admin', 'manager'] and execution.executed_by != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied. Only admin, manager, or execution creator can delete test executions.'})
        
        db.session.delete(execution)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Test execution deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting test execution: {str(e)}'})

@app.route('/test-executions/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_test_executions():
    try:
        data = request.get_json()
        execution_ids = data.get('execution_ids', [])
        
        if not execution_ids:
            return jsonify({'success': False, 'message': 'No test executions selected'})
        
        deleted_count = 0
        for execution_id in execution_ids:
            try:
                execution = TestExecution.query.get(execution_id)
                if execution and (current_user.role in ['admin', 'manager'] or execution.executed_by == current_user.id):
                    db.session.delete(execution)
                    deleted_count += 1
            except:
                pass
        
        db.session.commit()
        return jsonify({'success': True, 'deleted_count': deleted_count, 'message': f'Successfully deleted {deleted_count} test execution(s)'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting test executions: {str(e)}'})

@app.route('/requirements/<int:requirement_id>/delete', methods=['POST'])
@login_required
def delete_requirement(requirement_id):
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        
        # Check permissions - admin, manager, or requirement creator can delete
        if current_user.role not in ['admin', 'manager'] and requirement.created_by != current_user.id:
            return jsonify({'success': False, 'message': 'Access denied. Only admin, manager, or requirement creator can delete requirements.'})
        
        # Delete related test cases first
        try:
            db.session.execute(text("DELETE FROM test_case WHERE requirement_id = :requirement_id"), 
                             {'requirement_id': requirement_id})
        except:
            pass
        
        db.session.delete(requirement)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Requirement deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting requirement: {str(e)}'})

@app.route('/requirements/<int:requirement_id>/view', methods=['GET'])
@login_required
def view_requirement(requirement_id):
    """Get requirement details for viewing"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        project = Project.query.get(requirement.project_id) if requirement.project_id else None
        creator = User.query.get(requirement.created_by) if requirement.created_by else None
        
        # Get linked test cases
        linked_test_cases = TestCase.query.filter_by(requirement_id=requirement_id).all()
        
        requirement_data = {
            'id': requirement.id,
            'title': requirement.title,
            'description': requirement.description,
            'type': requirement.type,
            'priority': requirement.priority,
            'status': requirement.status,
            'project_name': project.name if project else 'No Project',
            'created_by': creator.username if creator else 'Unknown',
            'created_at': requirement.created_at.strftime('%Y-%m-%d %H:%M:%S') if requirement.created_at else '',
            'linked_test_cases': [
                {
                    'id': tc.id,
                    'title': tc.title,
                    'priority': tc.priority
                } for tc in linked_test_cases
            ]
        }
        
        return jsonify({'success': True, 'requirement': requirement_data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching requirement: {str(e)}'})

@app.route('/requirements/<int:requirement_id>/test-cases', methods=['GET'])
@login_required
def get_available_test_cases(requirement_id):
    """Get available test cases for linking to requirement"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        
        # Get all test cases from the same project
        if requirement.project_id:
            available_test_cases = TestCase.query.filter_by(project_id=requirement.project_id).all()
        else:
            available_test_cases = TestCase.query.all()
        
        # Get currently linked test cases
        linked_test_case_ids = [tc.id for tc in TestCase.query.filter_by(requirement_id=requirement_id).all()]
        
        test_cases_data = [
            {
                'id': tc.id,
                'title': tc.title,
                'priority': tc.priority,
                'is_linked': tc.id in linked_test_case_ids
            } for tc in available_test_cases
        ]
        
        return jsonify({'success': True, 'test_cases': test_cases_data})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching test cases: {str(e)}'})

@app.route('/requirements/<int:requirement_id>/link-test-cases', methods=['POST'])
@login_required
def link_test_cases_to_requirement(requirement_id):
    """Link test cases to requirement"""
    try:
        requirement = Requirement.query.get_or_404(requirement_id)
        data = request.get_json()
        test_case_ids = data.get('test_case_ids', [])
        
        # First, unlink all existing test cases
        TestCase.query.filter_by(requirement_id=requirement_id).update({'requirement_id': None})
        
        # Link selected test cases
        linked_count = 0
        for tc_id in test_case_ids:
            test_case = TestCase.query.get(tc_id)
            if test_case:
                test_case.requirement_id = requirement_id
                linked_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Successfully linked {linked_count} test case(s) to requirement',
            'linked_count': linked_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error linking test cases: {str(e)}'})

@app.route('/switch-host')
def switch_host():
    """Helper route to switch between localhost and 127.0.0.1"""
    current_host = request.host
    if 'localhost' in current_host:
        new_host = current_host.replace('localhost', '127.0.0.1')
    else:
        new_host = current_host.replace('127.0.0.1', 'localhost')
    
    return redirect(f"http://{new_host}{request.path}")

@app.route('/debug/session')
def debug_session():
    """Debug route to check session status"""
    return {
        'authenticated': current_user.is_authenticated,
        'username': current_user.username if current_user.is_authenticated else None,
        'role': current_user.role if current_user.is_authenticated else None,
        'session_keys': list(session.keys()),
        'host': request.host,
        'url': request.url,
        'remote_addr': request.remote_addr
    }

@app.route('/requirements/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_requirements():
    try:
        data = request.get_json()
        requirement_ids = data.get('requirement_ids', [])
        
        if not requirement_ids:
            return jsonify({'success': False, 'message': 'No requirements selected'})
        
        deleted_count = 0
        for requirement_id in requirement_ids:
            try:
                requirement = Requirement.query.get(requirement_id)
                if requirement and (current_user.role in ['admin', 'manager'] or requirement.created_by == current_user.id):
                    # Delete related test cases first
                    try:
                        db.session.execute(text("DELETE FROM test_case WHERE requirement_id = :requirement_id"), 
                                         {'requirement_id': requirement_id})
                    except:
                        pass
                    
                    db.session.delete(requirement)
                    deleted_count += 1
            except:
                pass
        
        db.session.commit()
        return jsonify({'success': True, 'deleted_count': deleted_count, 'message': f'Successfully deleted {deleted_count} requirement(s)'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting requirements: {str(e)}'})

@app.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
def delete_assignment(assignment_id):
    try:
        assignment = Assignment.query.get_or_404(assignment_id)
        
        # Check permissions - admin, manager, assignment creator, or assigned user can delete
        if (current_user.role not in ['admin', 'manager'] and 
            assignment.created_by != current_user.id and 
            assignment.assigned_to != current_user.id):
            return jsonify({'success': False, 'message': 'Access denied. Only admin, manager, assignment creator, or assigned user can delete assignments.'})
        
        db.session.delete(assignment)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Assignment deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting assignment: {str(e)}'})

@app.route('/assignments/bulk-delete', methods=['POST'])
@login_required
def bulk_delete_assignments():
    try:
        data = request.get_json()
        assignment_ids = data.get('assignment_ids', [])
        
        if not assignment_ids:
            return jsonify({'success': False, 'message': 'No assignments selected'})
        
        deleted_count = 0
        for assignment_id in assignment_ids:
            try:
                assignment = Assignment.query.get(assignment_id)
                if assignment and (current_user.role in ['admin', 'manager'] or 
                                 assignment.created_by == current_user.id or 
                                 assignment.assigned_to == current_user.id):
                    db.session.delete(assignment)
                    deleted_count += 1
            except:
                pass
        
        db.session.commit()
        return jsonify({'success': True, 'deleted_count': deleted_count, 'message': f'Successfully deleted {deleted_count} assignment(s)'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting assignments: {str(e)}'})

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.email = request.form['email']
        current_user.phone = request.form.get('phone', '')
        current_user.department = request.form.get('department', '')
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html')

@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('edit_profile'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('edit_profile'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('edit_profile'))
    
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Password changed successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/profile/enable-2fa', methods=['POST'])
@login_required
def enable_2fa():
    import secrets
    import pyotp
    
    if current_user.two_factor_enabled:
        flash('Two-factor authentication is already enabled', 'info')
        return redirect(url_for('edit_profile'))
    
    # Generate a secret key for 2FA
    secret = pyotp.random_base32()
    current_user.two_factor_secret = secret
    current_user.two_factor_enabled = True
    db.session.commit()
    
    # Generate QR code URL
    totp = pyotp.TOTP(secret)
    qr_url = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="TestPro"
    )
    
    flash('Two-factor authentication enabled successfully', 'success')
    return jsonify({
        'success': True,
        'secret': secret,
        'qr_url': qr_url,
        'message': 'Please scan the QR code with your authenticator app'
    })

@app.route('/profile/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    current_user.two_factor_enabled = False
    current_user.two_factor_secret = None
    db.session.commit()
    flash('Two-factor authentication disabled', 'success')
    return redirect(url_for('edit_profile'))

@app.route('/profile/upload-photo', methods=['POST'])
@login_required
def upload_profile_photo():
    if 'photo' not in request.files:
        flash('No photo selected', 'error')
        return redirect(url_for('edit_profile'))
    
    file = request.files['photo']
    if file.filename == '':
        flash('No photo selected', 'error')
        return redirect(url_for('edit_profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"profile_{current_user.id}_{int(datetime.now().timestamp())}.{file.filename.rsplit('.', 1)[1].lower()}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        current_user.profile_picture = filename
        db.session.commit()
        flash('Profile photo updated successfully', 'success')
    else:
        flash('Invalid file type. Please upload an image file.', 'error')
    
    return redirect(url_for('edit_profile'))

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/settings/general', methods=['POST'])
@login_required
def update_general_settings():
    current_user.language = request.form.get('language', 'en')
    current_user.timezone = request.form.get('timezone', 'UTC')
    current_user.date_format = request.form.get('date_format', 'MM/DD/YYYY')
    current_user.items_per_page = int(request.form.get('items_per_page', 25))
    
    db.session.commit()
    flash('General settings updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/notifications', methods=['POST'])
@login_required
def update_notification_settings():
    current_user.email_notifications = 'email_notifications' in request.form
    current_user.test_failure_alerts = 'test_failure_alerts' in request.form
    current_user.assignment_notifications = 'assignment_notifications' in request.form
    current_user.bug_update_notifications = 'bug_update_notifications' in request.form
    
    db.session.commit()
    flash('Notification settings updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/security', methods=['POST'])
@login_required
def update_security_settings():
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    
    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('settings'))
    
    if len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('settings'))
    
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Password updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/settings/preferences', methods=['POST'])
@login_required
def update_preferences():
    current_user.theme = request.form.get('theme', 'light')
    current_user.compact_view = 'compact_view' in request.form
    current_user.animations_enabled = 'animations_enabled' in request.form
    
    db.session.commit()
    flash('Display preferences updated successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

# Dashboard API routes
@app.route('/api/export-data')
@login_required
def export_data():
    # Create CSV export of test data
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['Test Case ID', 'Title', 'Status', 'Priority', 'Created Date'])
    
    # Write test case data
    test_cases = TestCase.query.all()
    for case in test_cases:
        writer.writerow([case.id, case.title, case.status, case.priority, case.created_at.strftime('%Y-%m-%d')])
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='test_cases_export.csv'
    )

@app.route('/api/quick-add', methods=['POST'])
@login_required
def quick_add():
    item_type = request.json.get('type')
    
    if item_type == 'test_case':
        # Create a quick test case
        test_case = TestCase(
            title=f"Quick Test Case - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Quick test case created from dashboard",
            test_steps="1. Define test steps\n2. Execute test\n3. Verify results",
            expected_result="Expected result to be defined",
            created_by=current_user.id,
            suite_id=1 if TestSuite.query.first() else None
        )
        db.session.add(test_case)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Quick test case created', 'id': test_case.id})
    
    elif item_type == 'project':
        # Create a quick project
        project = Project(
            name=f"Quick Project - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            description="Quick project created from dashboard",
            created_by=current_user.id
        )
        db.session.add(project)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Quick project created', 'id': project.id})
    
    return jsonify({'success': False, 'message': 'Invalid item type'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
