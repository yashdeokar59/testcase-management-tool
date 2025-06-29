from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='tester')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    profile_picture = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    
    # New fields for settings and preferences
    language = db.Column(db.String(10), default='en')
    timezone = db.Column(db.String(50), default='UTC')
    date_format = db.Column(db.String(20), default='MM/DD/YYYY')
    items_per_page = db.Column(db.Integer, default=25)
    theme = db.Column(db.String(20), default='light')
    email_notifications = db.Column(db.Boolean, default=True)
    test_failure_alerts = db.Column(db.Boolean, default=True)
    assignment_notifications = db.Column(db.Boolean, default=True)
    bug_update_notifications = db.Column(db.Boolean, default=True)
    compact_view = db.Column(db.Boolean, default=False)
    animations_enabled = db.Column(db.Boolean, default=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))

class UserSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_token = db.Column(db.String(255), unique=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    used = db.Column(db.Boolean, default=False)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='Active')
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class TestSuite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    parent_suite_id = db.Column(db.Integer, db.ForeignKey('test_suite.id'))

class Requirement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50), default='Functional')
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(20), default='Draft')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    preconditions = db.Column(db.Text)
    test_steps = db.Column(db.Text)
    steps = db.Column(db.Text)  # Alternative field name used in some places
    expected_result = db.Column(db.Text)
    test_data = db.Column(db.Text)
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(20), default='Active')
    type = db.Column(db.String(50), default='Manual')
    automation_status = db.Column(db.String(20), default='Not Automated')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    suite_id = db.Column(db.Integer, db.ForeignKey('test_suite.id'))
    test_suite_id = db.Column(db.Integer, db.ForeignKey('test_suite.id'))  # Alternative field name
    requirement_id = db.Column(db.Integer, db.ForeignKey('requirement.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    estimated_time = db.Column(db.Integer)  # in minutes

class TestExecution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'))
    executed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20))
    actual_result = db.Column(db.Text)
    comments = db.Column(db.Text)
    execution_date = db.Column(db.DateTime, default=datetime.utcnow)
    environment = db.Column(db.String(50))
    build_version = db.Column(db.String(50))
    execution_time = db.Column(db.Integer)  # in minutes
    test_cycle_id = db.Column(db.Integer, db.ForeignKey('test_cycle.id'))

class TestCycle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Planning')
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bug(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    severity = db.Column(db.String(20), default='Medium')
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(20), default='Open')
    type = db.Column(db.String(50), default='Functional')
    environment = db.Column(db.String(50))
    build_version = db.Column(db.String(50))
    steps_to_reproduce = db.Column(db.Text)
    expected_result = db.Column(db.Text)
    actual_result = db.Column(db.Text)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'))
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'))
    bug_id = db.Column(db.Integer, db.ForeignKey('bug.id'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'))
    bug_id = db.Column(db.Integer, db.ForeignKey('bug.id'))
    test_execution_id = db.Column(db.Integer, db.ForeignKey('test_execution.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50))  # test_case, bug, test_cycle
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Assigned')
    priority = db.Column(db.String(20), default='Medium')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'))
    bug_id = db.Column(db.Integer, db.ForeignKey('bug.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text)
    type = db.Column(db.String(50))  # info, warning, error, success
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TestEnvironment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(255))
    status = db.Column(db.String(20), default='Active')
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
