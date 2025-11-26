# ===== STANDARD LIBRARY =====
import os
import re
import csv
import random
import string
import logging
from io import StringIO
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

# ===== THIRD PARTY =====
import pytz
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, Response, flash, session
from flask_mail import Mail, Message
from flask_migrate import Migrate
from flask_login import login_user, logout_user, current_user, login_required
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import func
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

# ===== LOCAL IMPORTS =====
from config import Config
from database import db
from auth import init_auth, admin_required, login_required_custom, role_required, get_user_permissions
from models import (
    Style, Fabric, User, FabricVendor, Notion, NotionVendor,
    LaborOperation, CleaningCost, StyleFabric, StyleNotion,
    StyleLabor, Color, StyleColor, Variable, StyleVariable,
    SizeRange, GlobalSetting, StyleImage
)

# ===== LOAD ENVIRONMENT VARIABLES (ONCE!) =====
load_dotenv()


# ===== HELPER FUNCTIONS =====
def validate_password(password):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, "Valid"

# Initialize Mail
mail = Mail()
# Store verification codes
verification_codes = {}

def setup_logging(app):
    """Configure application logging"""
    # Create logs folder if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Main log file - captures everything
    file_handler = RotatingFileHandler(
        'logs/ja_uniforms.log',
        maxBytes=10 * 1024 * 1024,  # 10MB max size
        backupCount=10               # Keep 10 backup files
    )
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Error-only log file - easier to find critical issues
    error_handler = RotatingFileHandler(
        'logs/ja_uniforms_errors.log',
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    error_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(pathname)s:%(lineno)d\n%(message)s\n'
    ))
    error_handler.setLevel(logging.ERROR)
    
    # Add handlers to app
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info('=== J.A. Uniforms Application Started ===')


# Initialize Flask app
app = Flask(__name__)
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)  # 30 days instead of 365
setup_logging(app)
# Rate Limiter - prevents abuse
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
app.config.from_object(Config)

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # ✅ SECURE
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
# =========================================
mail.init_app(app)


# Initialize CSRF protection
csrf = CSRFProtect(app)

init_auth(app)

@app.context_processor
def inject_permissions():
    """Make user permissions available to all templates"""
    if current_user.is_authenticated:
        is_admin = current_user.role == 'admin'
        return {
            'permissions': get_user_permissions(),
            'user_role': current_user.role,
            'can_edit_styles': is_admin,
            'can_delete_styles': is_admin,
            'can_create_styles': is_admin,
            'can_duplicate_styles': is_admin,
            'can_favorite_styles': is_admin,
            'is_admin': is_admin
        }
    return {
        'permissions': get_user_permissions(),
        'user_role': None,
        'can_edit_styles': False,
        'can_delete_styles': False,
        'can_create_styles': False,
        'can_duplicate_styles': False,
        'can_favorite_styles': False,
        'is_admin': False
    }


UPLOAD_FOLDER = 'static/img'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Initialize database with app
db.init_app(app)
migrate = Migrate(app, db)

# ===== HELPER FUNCTIONS (already provided in your document) =====

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def require_admin_for_write():
    """Check if current request is a write operation and require admin"""
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        if not current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
    return None


def send_verification_email(email, code):
    """Send verification code to email"""
    msg = Message(
        'J.A. Uniforms - Email Verification Code',
        recipients=[email]
    )
    msg.body = f'''
Hello,

Your verification code for J.A. Uniforms Pricing Tool is:

{code}

This code will expire in 2 minutes.

If you didn't request this code, please ignore this email.

Best regards,
J.A. Uniforms Team
    '''
    
    msg.html = f'''
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); padding: 30px; border-radius: 10px; text-align: center;">
            <h1 style="color: white; margin: 0;">J.A. Uniforms</h1>
            <p style="color: white; margin: 10px 0 0 0;">Pricing Management System</p>
        </div>
        
        <div style="padding: 30px; background: #f9f9f9; border-radius: 10px; margin-top: 20px;">
            <h2 style="color: #2c3e50;">Email Verification Code</h2>
            <p>Hello,</p>
            <p>Your verification code for J.A. Uniforms Pricing Tool is:</p>
            
            <div style="background: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                <h1 style="color: #3498db; font-size: 36px; letter-spacing: 8px; margin: 0;">{code}</h1>
            </div>
            
            <p style="color: #666; font-size: 14px;">This code will expire in 2 minutes.</p>
            <p style="color: #666; font-size: 14px;">If you didn't request this code, please ignore this email.</p>
        </div>
        
        <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
            <p>© 2025 J.A. Uniforms. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
    '''
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.info(f"Error sending email: {e}")
        return False

# ===== VALIDATION HELPER FUNCTIONS =====

def validate_positive_number(value, field_name, required=True, allow_zero=True):
    """Validate that a value is a positive number"""
    if value is None or value == '':
        if required:
            return None, f"{field_name} is required"
        return 0 if allow_zero else None, None
    
    try:
        num = float(value)
        if num < 0:
            return None, f"{field_name} cannot be negative"
        if not allow_zero and num == 0:
            return None, f"{field_name} must be greater than zero"
        return num, None
    except (ValueError, TypeError):
        return None, f"{field_name} must be a valid number"

def validate_positive_integer(value, field_name, required=True):
    """Validate that a value is a positive integer"""
    if value is None or value == '':
        if required:
            return None, f"{field_name} is required"
        return 0, None
    
    try:
        num = int(float(value))
        if num < 0:
            return None, f"{field_name} cannot be negative"
        return num, None
    except (ValueError, TypeError):
        return None, f"{field_name} must be a valid whole number"
        
def validate_required_string(value, field_name, max_length=200):
    """Validate that a value is a non-empty string"""
    if value is None or str(value).strip() == '':
        return None, f"{field_name} is required"
    
    value = str(value).strip()
    if len(value) > max_length:
        return None, f"{field_name} cannot exceed {max_length} characters"
    
    return value, None

def validate_choice(value, field_name, choices):
    """Validate that a value is one of the allowed choices"""
    if value not in choices:
        return None, f"{field_name} must be one of: {', '.join(choices)}"
    return value, None


def validate_email(email):
    """Validate email format"""
    import re
    if not email:
        return None, "Email is required"
    
    email = email.strip().lower()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return None, "Invalid email format"
    
    return email, None


def validate_required_field(value, field_name):
    """Validate that a required field is not empty"""
    if not value or not str(value).strip():
        return False, f"{field_name} is required"
    return True, str(value).strip()

def validate_percentage(value, field_name):
    """Validate that a percentage is between 0 and 100"""
    try:
        num = float(value)
        if num < 0 or num > 100:
            return False, f"{field_name} must be between 0 and 100"
        return True, num
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"

def validate_string_length(value, field_name, max_length):
    """Validate string length"""
    if len(str(value)) > max_length:
        return False, f"{field_name} too long (max {max_length} characters)"
    return True, str(value)

# ===== END OF VALIDATION HELPERS =====
@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    if request.path.startswith('/api/'):
        return jsonify({
            "ok": False,
            "error": "Too many requests. Please slow down."
        }), 429
    
    flash("Too many requests. Please wait a moment and try again.", "warning")
    return redirect(request.referrer or url_for('index'))

# ===== YOUR ROUTES START HERE =====
# ===== DELETING USERS ======


@app.route('/api/send-verification-code', methods=['POST'])
@limiter.limit("3 per minute")   # ← ADD THIS
@limiter.limit("10 per hour") 
def send_verification_code():
    """API endpoint to send verification code"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'error': 'Email is required'}), 400
    
    # Validate email domain
    if not email.endswith('@jauniforms.com'):
        return jsonify({'success': False, 'error': 'Only company emails are allowed'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=email).first():
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    
    # Generate and store verification code
    code = generate_verification_code()
    verification_codes[email] = {
        'code': code,
        'expires': datetime.now() + timedelta(minutes=2)
    }
    
    # Send email
    if send_verification_email(email, code):
        return jsonify({'success': True, 'message': 'Verification code sent successfully'}), 200
    else:
        return jsonify({'success': False, 'error': 'Failed to send email'}), 500

# Add these routes AFTER your register route

@app.route('/api/verify-code', methods=['POST'])
@limiter.limit("5 per minute")
@csrf.exempt
def verify_code():
    """Verify the email verification code"""
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        
        if email not in verification_codes:
            return jsonify({'success': False, 'error': 'No verification code found'}), 200
        
        stored = verification_codes[email]
        
        # Check if code expired
        if datetime.now() > stored['expires']:
            del verification_codes[email]
            return jsonify({'success': False, 'error': 'Code expired. Please register again'}), 200
        
        # Check if code matches
        if stored['code'] != code:
            return jsonify({'success': False, 'error': 'Invalid verification code'}), 200
        
        # Create user account
        user_data = stored['user_data']
        user = User(
            username=email,
            email=email,
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            full_name=f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
        )
        user.password_hash = user_data['password_hash']

        if email == 'it@jauniforms.com':
            user.role = 'admin'
        else:
            user.role = 'user'

        db.session.add(user)
        db.session.commit()
        
        # Clean up
        del verification_codes[email]
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully',
            'redirect': '/login'
        }), 200
        
    except Exception as e:
        app.logger.info(f"Verification error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Verification failed'}), 200


@app.route('/api/resend-verification-code', methods=['POST'])
@limiter.limit("2 per minute")   # ← ADD THIS
@limiter.limit("5 per hour") 
@csrf.exempt
def resend_verification_code():
    """Resend verification code"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if email not in verification_codes:
            return jsonify({'success': False, 'error': 'No registration found'}), 200
        
        # Generate new code
        new_code = generate_verification_code()
        verification_codes[email]['code'] = new_code
        verification_codes[email]['expires'] = datetime.now() + timedelta(minutes=2)
        
        # Send new email
        if send_verification_email(email, new_code):
            return jsonify({'success': True, 'message': 'New code sent'}), 200
        else:
            return jsonify({'success': False, 'error': 'Error sending email'}), 200
            
    except Exception as e:
        app.logger.info(f"Resend error: {e}")
        return jsonify({'success': False, 'error': 'Failed to resend code'}), 200
    

# ===== AUTHENTICATION ROUTES =====
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute") 
def login():
    # Don't redirect if already logged in - let them see the login page
    # if current_user.is_authenticated:
    #     return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        
        if not email.endswith('@jauniforms.com'):
            flash('Only company emails (@jauniforms.com) are allowed', 'danger')
            return render_template('login.html')
        
        user = User.query.filter_by(username=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            flash(f'Welcome back, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    # Clear all existing flash messages
    session.pop('_flashes', None)
    # Add only logout message
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute") 
def register():
    """Main registration page - single page with modal verification"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('firstName')
            last_name = request.form.get('lastName')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Validation
            if not email or not email.endswith('@jauniforms.com'):
                return jsonify({'success': False, 'error': 'Only company emails (@jauniforms.com) are allowed'}), 200
            
            is_valid, message = validate_password(password)
            if not is_valid:
                return jsonify({'success': False, 'error': message}), 200
            
            if User.query.filter_by(username=email).first():
                return jsonify({'success': False, 'error': 'Email already registered'}), 200
            
            # Store user data temporarily
            verification_codes[email] = {
                'code': generate_verification_code(),
                'expires': datetime.now() + timedelta(minutes=2),
                'user_data': {
                    'first_name': first_name,
                    'last_name': last_name,
                    'password_hash': generate_password_hash(password)  # ✅ Hashed!
                }
            }
            
            # Send verification email
            if send_verification_email(email, verification_codes[email]['code']):
                return jsonify({'success': True, 'message': 'Verification code sent'}), 200
            else:
                return jsonify({'success': False, 'error': 'Error sending email'}), 200
                
        except Exception as e:
            app.logger.info(f"Registration error: {e}")
            return jsonify({'success': False, 'error': 'Registration failed'}), 200
    
    return render_template('register.html')

# ===== USER MANAGEMENT ROUTES (ADMIN ONLY) =====

@app.route('/admin/users')
@admin_required
def manage_users():
    """Admin-only user management page"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/api/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get user details"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name or '',
        'last_name': user.last_name or '',
        'role': user.role,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None
    })

@app.route('/api/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Update user details"""
    app.logger.info(f"💾 PUT user {user_id}")
    try:
        user = User.query.get_or_404(user_id)
        data = request.json
        app.logger.info(f"📦 Data: {data}")
        
        # CRITICAL: Prevent removing the last admin
        if 'role' in data and data['role'] == 'user' and user.role == 'admin':
            # Count total admins
            admin_count = User.query.filter_by(role='admin').count()
            app.logger.info(f"🔍 Current admin count: {admin_count}")
            
            if admin_count <= 1:
                app.logger.error(f"❌ Cannot remove last admin!")
                return jsonify({
                    'success': False, 
                    'error': 'Cannot change the last admin to user. The system must have at least one admin.'
                }), 400
        
        # Update email if provided and check for duplicates
        if 'email' in data and data['email'] != user.email:
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                return jsonify({'success': False, 'error': 'Email already exists'}), 400
            user.email = data['email']
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'role' in data and data['role'] in ['admin', 'user']:
            user.role = data['role']
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if user.first_name and user.last_name:
            user.full_name = f"{user.first_name} {user.last_name}"
        elif user.first_name:
            user.full_name = user.first_name
        
        db.session.commit()
        app.logger.info(f"✅ User {user_id} updated!")
        
        return jsonify({'success': True, 'message': 'User updated successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete user"""
    app.logger.info(f"🗑️ DELETE user {user_id}")
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent deleting yourself
        if user.id == current_user.id:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        # CRITICAL: Prevent deleting the last admin
        if user.role == 'admin':
            admin_count = User.query.filter_by(role='admin').count()
            app.logger.info(f"🔍 Current admin count: {admin_count}")
            
            if admin_count <= 1:
                app.logger.error(f"❌ Cannot delete last admin!")
                return jsonify({
                    'success': False, 
                    'error': 'Cannot delete the last admin. The system must have at least one admin.'
                }), 400
        
        db.session.delete(user)
        db.session.commit()
        app.logger.info(f"✅ User {user_id} deleted!")
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.template_filter('time_ago')
def time_ago_filter(dt):
    """Calculate time ago using system time"""
    if dt is None:
        return 'N/A'
    
    from datetime import datetime
    
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 0:
        return 'Just now'
    elif seconds < 60:
        return 'Just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} min ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    else:
        return dt.strftime('%b %d, %Y')


# ===== MAIN APPLICATION ROUTES =====

@app.route('/')
@login_required
def index():
    """Dashboard with real-time stats"""
    
    # Get real counts
    total_styles = Style.query.count()
    total_fabrics = Fabric.query.count()
    total_notions = Notion.query.count()
    total_fabric_vendors = FabricVendor.query.count()
    total_notion_vendors = NotionVendor.query.count()
    
    # Get recent styles (last 4)
    #ecent_styles = Style.query.order_by(Style.id.desc()).limit(4).all()
    recent_styles = Style.query.order_by(Style.updated_at.desc()).limit(4).all()
    
    # Calculate analytics
    styles = Style.query.all()
    
    # Average cost per style
    if styles:
        total_cost = sum([s.get_total_cost() for s in styles])
        avg_cost = total_cost / len(styles) if len(styles) > 0 else 0
    else:
        avg_cost = 0
    
    # Price range (min-max)
    if styles:
        costs = [s.get_total_cost() for s in styles]
        min_cost = min(costs) if costs else 0
        max_cost = max(costs) if costs else 0
        price_range = f"${min_cost:.0f}-${max_cost:.0f}"
    else:
        price_range = "$0-$0"
    
    # Top fabric (most used)
    from sqlalchemy import func
    top_fabric_query = db.session.query(
        Fabric.name, 
        func.count(StyleFabric.fabric_id).label('count')
    ).join(
        StyleFabric, Fabric.id == StyleFabric.fabric_id
    ).group_by(
        Fabric.name
    ).order_by(
        func.count(StyleFabric.fabric_id).desc()
    ).first()
    
    top_fabric = top_fabric_query[0] if top_fabric_query else "N/A"
    
    return render_template('dashboard.html',
                         total_styles=total_styles,
                         total_fabrics=total_fabrics,
                         total_notions=total_notions,
                         total_fabric_vendors=total_fabric_vendors,
                         total_notion_vendors=total_notion_vendors,
                         recent_styles=recent_styles,
                         avg_cost=avg_cost,
                         price_range=price_range,
                         top_fabric=top_fabric)


@app.route('/style/<vendor_style>')
def view_style(vendor_style):
    style = Style.query.filter_by(vendor_style=vendor_style).first()
    if style:
        return render_template('style_detail.html', style=style)
    return f"<h1>Style '{vendor_style}' not found</h1><a href='/'>Back to Search</a>"

# ===== ADMIN ROUTES (Future expansion) =====
@app.route('/api/recent-styles')
def api_recent_styles():
    styles = Style.query.order_by(Style.updated_at.desc()).limit(5).all()
    return jsonify([{
        'id': s.id,
        'vendor_style': s.vendor_style,
        'style_name': s.style_name,
        'updated_at': s.updated_at.isoformat() if s.updated_at else None
    } for s in styles])

@app.route('/api/dashboard-stats')
def api_dashboard_stats():
    total_styles = Style.query.count()
    styles = Style.query.all()
    avg_cost = sum(s.get_total_cost() for s in styles) / len(styles) if styles else 0
    
    return jsonify({
        'total_styles': total_styles,
        'avg_cost': avg_cost
    })

@app.route('/api/style/<int:style_id>/upload-image', methods=['POST'])
@admin_required 
def upload_style_image(style_id):
    """Upload an image for a style"""
    
    # ===== DEBUG: Print what we received =====
    app.logger.info("="*60)
    app.logger.info(f"📥 UPLOAD REQUEST for style {style_id}")
    app.logger.info(f"📋 request.files keys: {list(request.files.keys())}")
    app.logger.info(f"📋 request.form keys: {list(request.form.keys())}")
    app.logger.info(f"📋 request.content_type: {request.content_type}")
    
    # Print details of all files in request
    for key in request.files:
        f = request.files[key]
        app.logger.info(f"  File '{key}': filename={f.filename}, content_type={f.content_type}")
    
    app.logger.info("="*60)
    # ===== END DEBUG =====
    
    # Check if style exists
    style = Style.query.get_or_404(style_id)
    
    # Check if file is in request
    if 'image' not in request.files:
        app.logger.info("❌ ERROR: 'image' key not found in request.files")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['image']
    
    # Check if filename is empty
    if file.filename == '':
        app.logger.info("❌ ERROR: file.filename is empty")
        return jsonify({'error': 'No file selected'}), 400
    
    app.logger.info(f"✅ File received: {file.filename}")
    
    # Validate and save file
    if file and allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        filename = f"style_{style_id}_{timestamp}_{original_filename}"
        
        app.logger.info(f"💾 Saving as: {filename}")
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save file to disk
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        app.logger.info(f"✅ File saved to: {filepath}")
        
        # Check if this should be the primary image (first image for this style)
        is_primary = StyleImage.query.filter_by(style_id=style_id).count() == 0
        
        # Create database record
        new_image = StyleImage(
            style_id=style_id,
            filename=filename,
            is_primary=is_primary,
            upload_date=datetime.now()
        )
        
        db.session.add(new_image)
        db.session.commit()
        
        app.logger.info(f"✅ Image record created in database, ID: {new_image.id}")
        
        return jsonify({
            'success': True,
            'id': new_image.id,
            'filename': filename,
            'url': f'/static/img/{filename}',
            'is_primary': is_primary
        }), 200
    
    app.logger.error(f"❌ ERROR: File validation failed for {file.filename}")
    return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif'}), 400

@app.route('/api/style/<int:style_id>/images', methods=['GET'])
def get_style_images(style_id):
    """Get all images for a style"""
    # Check if style exists
    style = Style.query.get_or_404(style_id)
    
    # Get all images for this style, ordered by primary first, then by upload date
    images = StyleImage.query.filter_by(
        style_id=style_id
    ).order_by(
        StyleImage.is_primary.desc(),
        StyleImage.upload_date.asc()
    ).all()
    
    # Return image data as JSON
    return jsonify([{
        'id': img.id,
        'url': f'/static/img/{img.filename}',
        'filename': img.filename,
        'is_primary': img.is_primary,
        'upload_date': img.upload_date.isoformat() if img.upload_date else None
    } for img in images]), 200


@app.route('/api/style-image/<int:image_id>', methods=['DELETE'])
@admin_required 
def delete_style_image(image_id):
    """Delete a style image"""
    # Find the image record
    img = StyleImage.query.get_or_404(image_id)
    
    # Delete physical file from disk
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
    
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            app.logger.info(f"Error deleting file: {e}")
            # Continue anyway to remove from database
    
    # Delete database record
    db.session.delete(img)
    db.session.commit()
    
    return jsonify({'success': True}), 200


    
# SIZE RANGE ENDPOINTS
@app.route('/api/size-ranges', methods=['GET', 'POST'])
def api_size_ranges():
    if request.method == 'GET':
        ranges = SizeRange.query.all()
        return jsonify([{
            'id': r.id,
            'name': r.name,
            'regular_sizes': r.regular_sizes,
            'extended_sizes': r.extended_sizes,
            'extended_markup_percent': r.extended_markup_percent
        } for r in ranges])
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validation
            name, error = validate_required_string(data.get('name'), 'Size range name', max_length=50)
            if error:
                return jsonify({'success': False, 'error': error}), 400
            
            regular_sizes, error = validate_required_string(data.get('regular_sizes'), 'Regular sizes', max_length=100)
            if error:
                return jsonify({'success': False, 'error': error}), 400
            
            markup, error = validate_positive_number(data.get('extended_markup_percent', 15), 'Extended markup percent', required=False)
            if error:
                return jsonify({'success': False, 'error': error}), 400
            
            size_range = SizeRange(
                name=name,
                regular_sizes=regular_sizes,
                extended_sizes=data.get('extended_sizes', '').strip() if data.get('extended_sizes') else None,
                extended_markup_percent=markup or 15.0,
                description=data.get('description', '').strip() if data.get('description') else None
            )
            db.session.add(size_range)
            db.session.commit()
            
            return jsonify({'success': True, 'id': size_range.id})
        except Exception as e:
            app.logger.error(f"Error adding size range: {e}")
            return jsonify({'success': False, 'error': 'Failed to add size range'}), 500

@app.route('/api/size-ranges/<int:size_range_id>', methods=['GET', 'PUT', 'DELETE'])
def api_size_range_detail(size_range_id):
    size_range = SizeRange.query.get_or_404(size_range_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': size_range.id,
            'name': size_range.name,
            'regular_sizes': size_range.regular_sizes,
            'extended_sizes': size_range.extended_sizes,
            'extended_markup_percent': size_range.extended_markup_percent,
            'description': size_range.description
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'name' in data:
                name, error = validate_required_string(data.get('name'), 'Size range name', max_length=50)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                size_range.name = name
            
            if 'regular_sizes' in data:
                sizes, error = validate_required_string(data.get('regular_sizes'), 'Regular sizes', max_length=100)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                size_range.regular_sizes = sizes
            
            if 'extended_sizes' in data:
                size_range.extended_sizes = data.get('extended_sizes', '').strip() if data.get('extended_sizes') else None
            
            if 'extended_markup_percent' in data:
                markup, error = validate_positive_number(data.get('extended_markup_percent'), 'Extended markup percent', required=False)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                size_range.extended_markup_percent = markup or 15.0
            
            if 'description' in data:
                size_range.description = data.get('description', '').strip() if data.get('description') else None
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating size range: {e}")
            return jsonify({'success': False, 'error': 'Failed to update size range'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(size_range)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error deleting size range: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete size range'}), 500

# GLOBAL SETTINGS ENDPOINTS
@app.route('/api/global-settings', methods=['GET'])
def get_global_settings():
    settings = GlobalSetting.query.all()
    return jsonify([{
        'id': s.id,
        'setting_key': s.setting_key,
        'setting_value': float(s.setting_value),
        'description': s.description
    } for s in settings])

@app.route('/api/global-settings/<int:setting_id>', methods=['GET', 'PUT'])
@role_required('admin')
def api_global_setting_detail(setting_id):
    setting = GlobalSetting.query.get_or_404(setting_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': setting.id,
            'setting_key': setting.setting_key,
            'setting_value': setting.setting_value,
            'description': setting.description
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'setting_value' in data:
                value, error = validate_positive_number(data.get('setting_value'), 'Setting value', allow_zero=True)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                setting.setting_value = value
            
            if 'description' in data:
                setting.description = data.get('description', '').strip() if data.get('description') else None
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating global setting: {e}")
            return jsonify({'success': False, 'error': 'Failed to update setting'}), 500


@app.route('/import-colors')
@admin_required
def import_colors():
    """One-time import of colors from Excel file"""
    import pandas as pd
    try:
        df = pd.read_excel('V100COLORS.xlsx')
        
        imported = 0
        skipped = 0
        
        for index, row in df.iterrows():
            color_name = str(row['Color']).strip().upper()
            
            if not color_name or color_name == 'NAN':
                continue
                
            # Check if color already exists
            existing = Color.query.filter(func.lower(Color.name) == color_name.lower()).first()
            if existing:
                skipped += 1
                continue
            
            # Create new color
            color = Color(name=color_name)
            db.session.add(color)
            imported += 1
        
        db.session.commit()
        
        return f"""
        <div style="max-width: 600px; margin: 50px auto; padding: 20px; font-family: Arial;">
            <h1>Color Import Complete</h1>
            <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>✓ Imported: {imported} new colors</strong></p>
                <p>⊙ Skipped: {skipped} existing colors</p>
            </div>
            <a href="/master-costs" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Master Costs</a>
            <a href="/admin-panel" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Back to Admin</a>
        </div>
        """
    except Exception as e:
        return f"<h1>Error importing colors:</h1><p>{str(e)}</p>"
    
# COLOR ENDPOINTS
@app.route('/api/colors', methods=['GET', 'POST'])
def api_colors():
    if request.method == 'GET':
        colors = Color.query.order_by(Color.name).all()
        return jsonify([{'id': c.id, 'name': c.name, 'color_code': c.color_code} for c in colors])
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validation
            name, error = validate_required_string(data.get('name'), 'Color name', max_length=100)
            if error:
                return jsonify({'success': False, 'error': error}), 400
            
            # Check for duplicate
            existing = Color.query.filter(func.lower(Color.name) == name.lower()).first()
            if existing:
                return jsonify({'success': False, 'error': 'Color already exists'}), 400
            
            color = Color(
                name=name,
                color_code=data.get('color_code', '').strip() if data.get('color_code') else None
            )
            db.session.add(color)
            db.session.commit()
            
            return jsonify({'success': True, 'id': color.id})
        except Exception as e:
            app.logger.error(f"Error adding color: {e}")
            return jsonify({'success': False, 'error': 'Failed to add color'}), 500

@app.route('/api/colors/<int:color_id>', methods=['GET', 'PUT', 'DELETE'])
def api_color_detail(color_id):
    color = Color.query.get_or_404(color_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': color.id,
            'name': color.name,
            'color_code': color.color_code
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'name' in data:
                name, error = validate_required_string(data.get('name'), 'Color name', max_length=100)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                color.name = name
            
            if 'color_code' in data:
                color.color_code = data.get('color_code', '').strip() if data.get('color_code') else None
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating color: {e}")
            return jsonify({'success': False, 'error': 'Failed to update color'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(color)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error deleting color: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete color'}), 500


# ===== Extended-size + Range helpers (robust) =====

def _normalize_size_token(tok: str) -> str:
    """Normalize a size label to compare safely, e.g. '3x' -> '3XL'."""
    if tok is None:
        return ''
    s = tok.strip().upper().replace(' ', '')
    # Treat '3X' as '3XL'
    if s.endswith('X') and not s.endswith('XL'):
        s = s + 'L'
    return s

_ALPHA_LADDER = ["XXS","XS","S","M","L","XL","2XL","3XL","4XL","5XL","6XL"]

def _expand_alpha_range(a: str, b: str):
    A = _normalize_size_token(a); B = _normalize_size_token(b)
    try:
        ia, ib = _ALPHA_LADDER.index(A), _ALPHA_LADDER.index(B)
    except ValueError:
        return [A, B] if A != B else [A]
    return _ALPHA_LADDER[ia:ib+1] if ia <= ib else list(reversed(_ALPHA_LADDER[ib:ia+1]))

def _expand_numeric_range(a: str, b: str):
    """Expand numeric ranges with step=2."""
    sa, sb = a.strip(), b.strip()
    try:
        ia, ib = int(sa), int(sb)
    except ValueError:
        return [_normalize_size_token(a), _normalize_size_token(b)]

    if sa == "00":
        start, end = (ia, ib) if ia <= ib else (ib, ia)
        tail = [str(n) for n in range(0, end + 1, 2)]
        return ["00"] + tail

    width = max(len(sa), len(sb))
    step = 2
    if ia <= ib:
        seq = range(ia, ib + 1, step)
    else:
        seq = range(ia, ib - 1, -step)

    return [str(n).zfill(width) for n in seq]


def _expand_mixed_token(token: str):
    t = token.strip()
    if not t:
        return []
    if '-' in t:
        left, right = [x.strip() for x in t.split('-', 1)]
        if any(c.isalpha() for c in left+right):
            return _expand_alpha_range(left, right)
        return _expand_numeric_range(left, right)
    s = _normalize_size_token(t)
    return [s] if s else []

def expand_sizes_string(s: str):
    """'XS-XL, 2XL-6XL' or '00-18, 20-30' -> flat list of sizes."""
    if not s:
        return []
    out = []
    for part in s.split(','):
        out.extend(_expand_mixed_token(part))
    # de-dup preserving order
    seen, flat = set(), []
    for x in out:
        if x not in seen:
            seen.add(x); flat.append(x)
    return flat

def is_extended_size_for_range(size_label: str, size_range_obj) -> bool:
    """True if size_label is inside size_range_obj.extended_sizes (supports ranges)."""
    if size_range_obj is None:
        return False
    ext_list = expand_sizes_string(getattr(size_range_obj, 'extended_sizes', '') or '')
    if not ext_list:
        return False
    return _normalize_size_token(size_label) in ext_list


# ===== VALIDATION HELPER =====
def validate_style_for_export(style):
    """
    Validate a single style for export.
    Returns (is_valid: bool, missing: list)
    """
    missing = []
    
    # Check vendor style
    if not style.vendor_style or not style.vendor_style.strip():
        missing.append('Vendor Style')
    
    # Check style name
    if not style.style_name or not style.style_name.strip():
        missing.append('Style Name')
    
    # Check colors - STRICT (must have at least 1)
    has_colors = hasattr(style, 'colors') and style.colors and len(style.colors) > 0
    if not has_colors:
        missing.append('At least ONE Color')
    
    # Check size range - STRICT (must exist AND have sizes)
    if not style.size_range or not style.size_range.strip():
        missing.append('Size Range')
    else:
        # Verify size range actually has sizes defined
        from models import SizeRange
        size_range_obj = SizeRange.query.filter_by(name=style.size_range).first()
        if size_range_obj:
            regular_sizes = expand_sizes_string(getattr(size_range_obj, 'regular_sizes', '') or '')
            extended_sizes = expand_sizes_string(getattr(size_range_obj, 'extended_sizes', '') or '')
            all_sizes = regular_sizes + [s for s in extended_sizes if s not in regular_sizes]
            
            if not all_sizes:
                missing.append('Size Range has NO sizes defined')
        else:
            missing.append('Size Range does not exist in system')
    
    return (len(missing) == 0, missing)


# ===== SINGLE STYLE EXPORT =====
@app.route('/export-sap-single-style', methods=['POST'])
def export_sap_single_style():
    """Export a single style in SAP B1 format - STRICT VALIDATION"""
    try:
        vendor_style = request.form.get('vendor_style')
        if not vendor_style:
            return "No style specified", 400

        style = Style.query.filter_by(vendor_style=vendor_style).first()
        if not style:
            return "Style not found", 404

        # ========================================
        # STRICT VALIDATION
        # ========================================
        is_valid, missing = validate_style_for_export(style)
        
        if not is_valid:
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Export Validation Error</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        padding: 40px;
                        background: #f5f5f5;
                    }}
                    .container {{
                        max-width: 700px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    h1 {{
                        color: #dc3545;
                        margin-bottom: 20px;
                    }}
                    .style-info {{
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 4px;
                        margin-bottom: 20px;
                    }}
                    .error-box {{
                        background: #fff3cd;
                        border-left: 4px solid #ffc107;
                        padding: 15px;
                        margin: 20px 0;
                    }}
                    .missing-item {{
                        color: #856404;
                        margin: 5px 0;
                        padding-left: 20px;
                    }}
                    .missing-item::before {{
                        content: "⚠️ ";
                    }}
                    .back-btn {{
                        display: inline-block;
                        margin-top: 20px;
                        padding: 10px 20px;
                        background: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                    }}
                    .back-btn:hover {{
                        background: #0056b3;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Cannot Export</h1>
                    
                    <div class="style-info">
                        <strong>Style:</strong> {style.vendor_style}<br>
                        <strong>Name:</strong> {style.style_name or 'N/A'}
                    </div>
                    
                    <div class="error-box">
                        <strong>Missing Required Fields:</strong>
                        {''.join(f'<div class="missing-item">{item}</div>' for item in missing)}
                    </div>
                    
                    <p><strong>All fields below are REQUIRED for export:</strong></p>
                    <ul>
                        <li>Vendor Style</li>
                        <li>Style Name</li>
                        <li>At least ONE Color</li>
                        <li>Size Range (with sizes defined)</li>
                    </ul>
                    
                    <a href="/style/new?vendor_style={vendor_style}" class="back-btn">← Edit This Style</a>
                </div>
            </body>
            </html>
            """
            return error_html, 400

        # ========================================
        # EXPORT - NO FALLBACKS
        # ========================================
        output = StringIO()
        writer = csv.writer(output)

        headers = ['Code', 'Name', 'U_COLOR', 'U_SIZE', 'U_VARIABLE',
                   'U_PRICE', 'U_SHIP_COST', 'U_STYLE', 'U_CardCode', 'U_PROD_NAME']
        writer.writerow(headers)
        writer.writerow(headers)

        base_cost = style.get_total_cost()
        from models import SizeRange
        size_range_obj = SizeRange.query.filter_by(name=style.size_range).first()

        extended_pct = (size_range_obj.extended_markup_percent
                        if (size_range_obj and size_range_obj.extended_markup_percent is not None)
                        else 15.0)
        extended_mult = 1.0 + (float(extended_pct) / 100.0)

        regular_list = expand_sizes_string(getattr(size_range_obj, 'regular_sizes', '') or '')
        extended_list = expand_sizes_string(getattr(size_range_obj, 'extended_sizes', '') or '')
        all_sizes = regular_list + [s for s in extended_list if s not in regular_list]
        
        # NO FALLBACK - validation ensures sizes exist
        colors = [sc.color.name.upper() for sc in style.colors]
        
        variables = [sv.variable.name.upper() for sv in style.style_variables] if hasattr(style, 'style_variables') else []
        vendor_code = 'V100'
        if style.style_fabrics and style.style_fabrics[0].fabric.fabric_vendor:
            vendor_code = style.style_fabrics[0].fabric.fabric_vendor.vendor_code

        u_style = style.vendor_style.replace('-', '')
        shipping_cost = style.shipping_cost if hasattr(style, 'shipping_cost') else 0.00

        for color in colors:
            for size in all_sizes:
                if is_extended_size_for_range(size, size_range_obj):
                    price = round(base_cost * extended_mult, 2)
                else:
                    price = round(base_cost, 2)

                if variables:
                    for variable in variables:
                        writer.writerow(['', '', color, size, variable, price, shipping_cost, u_style, vendor_code, style.style_name])
                    writer.writerow(['', '', color, size, '', price, shipping_cost, u_style, vendor_code, style.style_name])
                else:
                    writer.writerow(['', '', color, size, '', price, shipping_cost, u_style, vendor_code, style.style_name])

        output.seek(0)
        filename = f"SAP_{style.vendor_style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(output.getvalue(), mimetype='text/csv',
                        headers={'Content-Disposition': f'attachment; filename={filename}'})

    except Exception as e:
        import traceback
        app.logger.error(traceback.format_exc())
        return f"Error exporting: {str(e)}", 500


# ===== BULK EXPORT =====
@app.route('/export-sap-format', methods=['POST'])
def export_sap_format():
    """Export selected styles in SAP B1 format - STRICT VALIDATION"""
    try:
        import json
        style_ids = json.loads(request.form.get('style_ids', '[]'))
        if not style_ids:
            return "No styles selected", 400

        styles = Style.query.filter(Style.id.in_(style_ids)).all()
        
        # ========================================
        # STRICT VALIDATION - ALL STYLES
        # ========================================
        invalid_styles = []
        
        for style in styles:
            is_valid, missing = validate_style_for_export(style)
            if not is_valid:
                invalid_styles.append({
                    'vendor_style': style.vendor_style or 'UNKNOWN',
                    'style_name': style.style_name or 'UNKNOWN',
                    'missing': missing
                })
        
        # If ANY style is invalid, block export and show errors
        if invalid_styles:
            error_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Export Validation Error</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        padding: 40px;
                        background: #f5f5f5;
                    }
                    .container {
                        max-width: 900px;
                        margin: 0 auto;
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    h1 {
                        color: #dc3545;
                        margin-bottom: 20px;
                    }
                    .summary {
                        background: #fff3cd;
                        border: 2px solid #ffc107;
                        padding: 15px;
                        margin-bottom: 30px;
                        border-radius: 4px;
                        font-weight: bold;
                        text-align: center;
                    }
                    .error-list {
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 4px;
                    }
                    .style-error {
                        margin-bottom: 20px;
                        padding: 15px;
                        border-left: 4px solid #dc3545;
                        background: white;
                    }
                    .vendor-style {
                        font-weight: bold;
                        color: #333;
                        font-size: 1.1em;
                        margin-bottom: 5px;
                    }
                    .style-name {
                        color: #666;
                        font-size: 0.9em;
                        margin-bottom: 10px;
                    }
                    .missing-item {
                        color: #856404;
                        margin: 3px 0;
                        padding-left: 20px;
                    }
                    .missing-item::before {
                        content: "⚠️ ";
                    }
                    .requirements {
                        background: #e7f3ff;
                        border-left: 4px solid #007bff;
                        padding: 15px;
                        margin: 20px 0;
                    }
                    .back-btn {
                        display: inline-block;
                        margin-top: 20px;
                        padding: 12px 24px;
                        background: #007bff;
                        color: white;
                        text-decoration: none;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    .back-btn:hover {
                        background: #0056b3;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Export Blocked - Validation Failed</h1>
                    
                    <div class="summary">
                        {len(invalid_styles)} of {len(styles)} selected style(s) are missing required fields
                    </div>
                    
                    <div class="error-list">
            """
            
            for inv in invalid_styles:
                error_html += f"""
                        <div class="style-error">
                            <div class="vendor-style">{inv['vendor_style']}</div>
                            <div class="style-name">{inv['style_name']}</div>
                            {''.join(f'<div class="missing-item">{item}</div>' for item in inv['missing'])}
                        </div>
                """
            
            error_html += """
                    </div>
                    
                    <div class="requirements">
                        <strong>🔒 All fields below are REQUIRED for export:</strong>
                        <ul>
                            <li><strong>Vendor Style</strong> - Must be filled</li>
                            <li><strong>Style Name</strong> - Must be filled</li>
                            <li><strong>At least ONE Color</strong> - Add colors to the style</li>
                            <li><strong>Size Range</strong> - Must be selected with sizes defined</li>
                        </ul>
                    </div>
                    
                    <p>Please complete ALL required fields for ALL selected styles before exporting.</p>
                    
                    <a href="/view-all-styles" class="back-btn">← Back to All Styles</a>
                </div>
            </body>
            </html>
            """
            
            return error_html, 400
        
        # ========================================
        # ALL VALIDATED - EXPORT (NO FALLBACKS)
        # ========================================
        output = StringIO()
        writer = csv.writer(output)

        headers = ['Code', 'Name', 'U_COLOR', 'U_SIZE', 'U_VARIABLE',
                   'U_PRICE', 'U_SHIP_COST', 'U_STYLE', 'U_CardCode', 'U_PROD_NAME']
        writer.writerow(headers)
        writer.writerow(headers)

        for style in styles:
            base_cost = style.get_total_cost()
            from models import SizeRange
            size_range_obj = SizeRange.query.filter_by(name=style.size_range).first()

            extended_pct = (size_range_obj.extended_markup_percent
                            if (size_range_obj and size_range_obj.extended_markup_percent is not None)
                            else 15.0)
            extended_mult = 1.0 + (float(extended_pct) / 100.0)

            regular_list = expand_sizes_string(getattr(size_range_obj, 'regular_sizes', '') or '')
            extended_list = expand_sizes_string(getattr(size_range_obj, 'extended_sizes', '') or '')
            all_sizes = regular_list + [s for s in extended_list if s not in regular_list]

            # NO FALLBACKS - validation ensures these exist
            colors = [sc.color.name.upper() for sc in style.colors]
            
            variables = [sv.variable.name.upper() for sv in style.style_variables] if hasattr(style, 'style_variables') else []
            vendor_code = 'V100'
            if style.style_fabrics and style.style_fabrics[0].fabric.fabric_vendor:
                vendor_code = style.style_fabrics[0].fabric.fabric_vendor.vendor_code

            u_style = style.vendor_style.replace('-', '')
            shipping_cost = style.shipping_cost if hasattr(style, 'shipping_cost') else 0.00

            for color in colors:
                for size in all_sizes:
                    price = round(base_cost * extended_mult, 2) if is_extended_size_for_range(size, size_range_obj) else round(base_cost, 2)
                    if variables:
                        for variable in variables:
                            writer.writerow(['', '', color, size, variable, price, shipping_cost, u_style, vendor_code, style.style_name])
                        writer.writerow(['', '', color, size, '', price, shipping_cost, u_style, vendor_code, style.style_name])
                    else:
                        writer.writerow(['', '', color, size, '', price, shipping_cost, u_style, vendor_code, style.style_name])

        output.seek(0)
        filename = f"SAP_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(output.getvalue(), mimetype='text/csv',
                        headers={'Content-Disposition': f'attachment; filename={filename}'})

    except Exception as e:
        import traceback
        app.logger.error(traceback.format_exc())
        return f"Error exporting: {str(e)}", 500


@app.route('/view-all-styles')
@role_required('admin', 'user')  # Only admin and user roles allowed
def view_all_styles():
    """View all styles with filters - RBAC enabled (Admin and User only)"""
    styles = Style.query.all()
    
    # Calculate stats
    total_styles = len(styles)
    total_value = sum([s.get_total_cost() for s in styles])
    avg_cost = total_value / total_styles if total_styles > 0 else 0
    
    # Get user permissions for frontend
    permissions = get_user_permissions()
    
    return render_template('view_all_styles.html', 
                         styles=styles,
                         total_styles=total_styles,
                         total_value=total_value,
                         avg_cost=avg_cost,
                         permissions=permissions,
                         current_user=current_user)

@app.route('/api/style/delete/<int:style_id>', methods=['DELETE'])
@admin_required 
def delete_style(style_id):
    """Delete a style and all its relationships"""
    try:
        style = Style.query.get_or_404(style_id)
        
        # Delete style images first (foreign key constraint)
        StyleImage.query.filter_by(style_id=style_id).delete()
        
        # Delete all other relationships
        StyleFabric.query.filter_by(style_id=style_id).delete()
        StyleNotion.query.filter_by(style_id=style_id).delete()
        StyleLabor.query.filter_by(style_id=style_id).delete()
        StyleColor.query.filter_by(style_id=style_id).delete()
        StyleVariable.query.filter_by(style_id=style_id).delete()
        
        # Delete the style
        db.session.delete(style)
        db.session.commit()
        
        return jsonify({"ok": True, "message": "Style deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        app.logger.info(f"Delete error: {error_details}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/style/duplicate/<int:style_id>', methods=['POST'])
@admin_required 
def duplicate_style(style_id):
    """Duplicate a style with all its components"""
    try:
        original = Style.query.get_or_404(style_id)
        
        # Generate unique vendor_style for the copy
        base_vendor_style = original.vendor_style if original.vendor_style else "COPY"
        new_vendor_style = f"{base_vendor_style}-COPY"
        
        # Check if this vendor_style already exists, if so add a number
        counter = 1
        while Style.query.filter_by(vendor_style=new_vendor_style).first():
            new_vendor_style = f"{base_vendor_style}-COPY{counter}"
            counter += 1
        
        # Create new style
        new_style = Style(
            style_name=f"{original.style_name} (Copy)",
            vendor_style=new_vendor_style,
            base_item_number=original.base_item_number,
            variant_code=original.variant_code,
            gender=original.gender,
            garment_type=original.garment_type,
            size_range=original.size_range,
            notes=original.notes,
            base_margin_percent=original.base_margin_percent,
            suggested_price=original.suggested_price
        )
        db.session.add(new_style)
        db.session.flush()
        
        # Copy fabrics - Query directly from StyleFabric table
        style_fabrics = StyleFabric.query.filter_by(style_id=original.id).all()
        for sf in style_fabrics:
            new_sf = StyleFabric(
                style_id=new_style.id,
                fabric_id=sf.fabric_id,
                yards_required=sf.yards_required,
                is_primary=sf.is_primary,
                is_sublimation=sf.is_sublimation
            )
            db.session.add(new_sf)
        
        # Copy notions - Query directly from StyleNotion table
        style_notions = StyleNotion.query.filter_by(style_id=original.id).all()
        for sn in style_notions:
            new_sn = StyleNotion(
                style_id=new_style.id,
                notion_id=sn.notion_id,
                quantity_required=sn.quantity_required
            )
            db.session.add(new_sn)
        
        # Copy labor - Query directly from StyleLabor table
        style_labor = StyleLabor.query.filter_by(style_id=original.id).all()
        for sl in style_labor:
            new_sl = StyleLabor(
                style_id=new_style.id,
                labor_operation_id=sl.labor_operation_id,
                time_hours=sl.time_hours,
                quantity=sl.quantity
            )
            db.session.add(new_sl)
        
        # Copy colors - Query directly from StyleColor table
        style_colors = StyleColor.query.filter_by(style_id=original.id).all()
        for sc in style_colors:
            new_sc = StyleColor(
                style_id=new_style.id,
                color_id=sc.color_id
            )
            db.session.add(new_sc)
        
        # Copy variables - Query directly from StyleVariable table
        style_variables = StyleVariable.query.filter_by(style_id=original.id).all()
        for sv in style_variables:
            new_sv = StyleVariable(
                style_id=new_style.id,
                variable_id=sv.variable_id
            )
            db.session.add(new_sv)
        
        db.session.commit()
        
        return jsonify({
            "ok": True, 
            "new_style_id": new_style.id, 
            "new_vendor_style": new_vendor_style,
            "message": f"Style duplicated as '{new_vendor_style}'"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        app.logger.info(f"Duplicate error: {error_details}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/styles/bulk-delete', methods=['POST'])
@admin_required 
def bulk_delete_styles():
    """Delete multiple styles"""
    try:
        data = request.get_json()
        style_ids = data.get('style_ids', [])
        
        if not style_ids:
            return jsonify({"ok": False, "error": "No styles selected"}), 400
        
        for style_id in style_ids:
            # Delete all relationships in the correct order
            # (Images first, then other relationships, then the style itself)
            
            # Delete style images
            StyleImage.query.filter_by(style_id=style_id).delete()

            # Delete other relationships
            StyleFabric.query.filter_by(style_id=style_id).delete()
            StyleNotion.query.filter_by(style_id=style_id).delete()
            StyleLabor.query.filter_by(style_id=style_id).delete()
            StyleColor.query.filter_by(style_id=style_id).delete()
            StyleVariable.query.filter_by(style_id=style_id).delete()
            
            # Finally, delete the style itself
            style = Style.query.get(style_id)
            if style:
                db.session.delete(style)
        
        db.session.commit()
        
        return jsonify({"ok": True, "message": f"{len(style_ids)} style(s) deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc()
        app.logger.info(f"Bulk delete error: {error_details}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/style/load-for-duplicate/<int:style_id>')
def load_style_for_duplicate(style_id):
    """Load a style's data for duplication"""
    try:
        style = Style.query.get_or_404(style_id)
        
        # Get fabrics
        fabrics = []
        for sf in StyleFabric.query.filter_by(style_id=style.id).all():
            fabric = Fabric.query.get(sf.fabric_id)
            if fabric:
                vendor_name = ""
                if fabric.fabric_vendor_id:
                    vendor = FabricVendor.query.get(fabric.fabric_vendor_id)
                    if vendor:
                        vendor_name = vendor.name
                
                fabrics.append({
                    "name": fabric.name,
                    "vendor": vendor_name,
                    "yards": sf.yards_required,
                    "cost_per_yard": fabric.cost_per_yard,
                    "primary": sf.is_primary,
                    "sublimation": sf.is_sublimation
                })
        
        # Get notions
        notions = []
        for sn in StyleNotion.query.filter_by(style_id=style.id).all():
            notion = Notion.query.get(sn.notion_id)
            if notion:
                vendor_name = ""
                if notion.notion_vendor_id:
                    vendor = NotionVendor.query.get(notion.notion_vendor_id)
                    if vendor:
                        vendor_name = vendor.name
                
                notions.append({
                    "name": notion.name,
                    "vendor": vendor_name,
                    "qty": sn.quantity_required,
                    "cost_per_unit": notion.cost_per_unit
                })
        
        # Get labor
        labor = []
        for sl in StyleLabor.query.filter_by(style_id=style.id).all():
            op = LaborOperation.query.get(sl.labor_operation_id)
            if op:
                labor.append({
                    "name": op.name,
                    "qty_or_hours": sl.time_hours if op.cost_type == 'hourly' else sl.quantity
                })
        
        # Get colors
        colors = []
        for sc in StyleColor.query.filter_by(style_id=style.id).all():
            color = Color.query.get(sc.color_id)
            if color:
                colors.append({
                    "color_id": color.id,
                    "name": color.name
                })
        
        # Get variables
        variables = []
        for sv in StyleVariable.query.filter_by(style_id=style.id).all():
            variable = Variable.query.get(sv.variable_id)
            if variable:
                variables.append({
                    "variable_id": variable.id,
                    "name": variable.name
                })
        
        return jsonify({
            "ok": True,
            "style": {
                "vendor_style": style.vendor_style + "-COPY",  # Suggest a new vendor style
                "style_name": style.style_name + " (Copy)",     # Suggest a new style name
                "base_item_number": style.base_item_number,
                "variant_code": style.variant_code,
                "gender": style.gender,
                "garment_type": style.garment_type,
                "size_range": style.size_range,
                "margin": style.base_margin_percent,
                "suggested_price": style.suggested_price,
                "notes": style.notes,
                "original_vendor_style": style.vendor_style,  # Track original
                "original_style_name": style.style_name        # Track original
            },
            "fabrics": fabrics,
            "notions": notions,
            "labor": labor,
            "colors": colors,
            "variables": variables
        }), 200
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    
@app.route('/api/style/check-vendor-style')
def check_vendor_style():
    """Check if a vendor_style already exists"""
    vendor_style = request.args.get('vendor_style', '').strip()
    
    if not vendor_style:
        return jsonify({"exists": False})
    
    exists = Style.query.filter_by(vendor_style=vendor_style).first() is not None
    
    return jsonify({"exists": exists})


# ===== EDITABLE MASTER COSTS WITH VENDOR MANAGEMENT =====

@app.route('/api/style/<int:style_id>/favorite', methods=['POST'])
@admin_required
def toggle_favorite(style_id):
    """Toggle favorite status"""
    try:
        style = Style.query.get_or_404(style_id)
        data = request.get_json()
        style.is_favorite = data.get('is_favorite', False)
        db.session.commit()
        return jsonify({"ok": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/master-costs')
def master_costs():
    """Display editable master cost lists"""
    fabrics = Fabric.query.order_by(Fabric.name).all()
    notions = Notion.query.order_by(Notion.name).all()
    labor_ops = LaborOperation.query.order_by(LaborOperation.name).all()
    cleaning_costs = CleaningCost.query.order_by(CleaningCost.garment_type).all()
    fabric_vendors = FabricVendor.query.order_by(FabricVendor.name).all()
    notion_vendors = NotionVendor.query.order_by(NotionVendor.name).all()
    colors = Color.query.order_by(Color.name).all()
    variables = Variable.query.order_by(Variable.name).all()
    size_ranges = SizeRange.query.order_by(SizeRange.name).all()
    global_settings = GlobalSetting.query.all()
    
    return render_template('master_costs.html',
                         fabrics=fabrics,
                         notions=notions,
                         labor_costs=labor_ops,  # ← CHANGED THIS LINE
                         cleaning_costs=cleaning_costs,
                         fabric_vendors=fabric_vendors,
                         notion_vendors=notion_vendors,
                         colors=colors,
                         variables=variables,
                         size_ranges=size_ranges,
                         global_settings=global_settings)

# ===== API ENDPOINTS FOR MASTER COSTS =====

# FABRIC VENDOR ENDPOINTS
@app.route('/api/fabric-vendors/<int:vendor_id>', methods=['GET', 'PUT', 'DELETE'])
@role_required('admin')
def api_fabric_vendor_detail(vendor_id):
    vendor = FabricVendor.query.get_or_404(vendor_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': vendor.id,
            'name': vendor.name,
            'vendor_code': vendor.vendor_code
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'name' in data:
                name, error = validate_required_string(data.get('name'), 'Vendor name', max_length=100)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                vendor.name = name
            
            if 'vendor_code' in data:
                vendor.vendor_code = data.get('vendor_code', '').strip() if data.get('vendor_code') else None
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating fabric vendor: {e}")
            return jsonify({'success': False, 'error': 'Failed to update fabric vendor'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(vendor)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error deleting fabric vendor: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete fabric vendor'}), 500

@app.route('/api/fabric-vendors', methods=['POST'])
@role_required('admin')
def api_add_fabric_vendor():
    try:
        data = request.get_json()
        
        # Validation
        name, error = validate_required_string(data.get('name'), 'Vendor name', max_length=100)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        vendor = FabricVendor(
            name=name,
            vendor_code=data.get('vendor_code', '').strip() if data.get('vendor_code') else None
        )
        db.session.add(vendor)
        db.session.commit()
        
        return jsonify({'success': True, 'id': vendor.id})
    except Exception as e:
        app.logger.error(f"Error adding fabric vendor: {e}")
        return jsonify({'success': False, 'error': 'Failed to add fabric vendor'}), 500

# NOTION VENDOR ENDPOINTS
@app.route('/api/notion-vendors/<int:vendor_id>', methods=['GET', 'PUT', 'DELETE'])
@role_required('admin')
def api_notion_vendor_detail(vendor_id):
    vendor = NotionVendor.query.get_or_404(vendor_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': vendor.id,
            'name': vendor.name,
            'vendor_code': vendor.vendor_code
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'name' in data:
                name, error = validate_required_string(data.get('name'), 'Vendor name', max_length=100)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                vendor.name = name
            
            if 'vendor_code' in data:
                vendor.vendor_code = data.get('vendor_code', '').strip() if data.get('vendor_code') else None
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating notion vendor: {e}")
            return jsonify({'success': False, 'error': 'Failed to update notion vendor'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(vendor)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error deleting notion vendor: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete notion vendor'}), 500



@app.route('/api/notion-vendors', methods=['POST'])
@role_required('admin')
def api_add_notion_vendor():
    try:
        data = request.get_json()
        
        # Validation
        name, error = validate_required_string(data.get('name'), 'Vendor name', max_length=100)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        vendor = NotionVendor(
            name=name,
            vendor_code=data.get('vendor_code', '').strip() if data.get('vendor_code') else None
        )
        db.session.add(vendor)
        db.session.commit()
        
        return jsonify({'success': True, 'id': vendor.id})
    except Exception as e:
        app.logger.error(f"Error adding notion vendor: {e}")
        return jsonify({'success': False, 'error': 'Failed to add notion vendor'}), 500

# FABRIC ENDPOINTS   
@app.route('/api/fabrics/<int:fabric_id>', methods=['GET', 'PUT', 'DELETE'])
@role_required('admin')
def api_fabric_detail(fabric_id):
    fabric = Fabric.query.get_or_404(fabric_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': fabric.id,
            'name': fabric.name,
            'cost_per_yard': fabric.cost_per_yard,
            'fabric_vendor_id': fabric.fabric_vendor_id,
            'fabric_code': fabric.fabric_code,
            'color': fabric.color
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            # Validation
            if 'name' in data:
                name, error = validate_required_string(data.get('name'), 'Fabric name', max_length=100)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                fabric.name = name
            
            if 'cost_per_yard' in data:
                cost, error = validate_positive_number(data.get('cost_per_yard'), 'Cost per yard')
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                fabric.cost_per_yard = cost
            
            if 'fabric_vendor_id' in data:
                fabric.fabric_vendor_id = data.get('fabric_vendor_id')
            
            if 'fabric_code' in data:
                fabric.fabric_code = data.get('fabric_code', '').strip() if data.get('fabric_code') else None
            
            if 'color' in data:
                fabric.color = data.get('color', '').strip() if data.get('color') else None
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating fabric: {e}")
            return jsonify({'success': False, 'error': 'Failed to update fabric'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(fabric)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error deleting fabric: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete fabric'}), 500

@app.route('/api/fabrics', methods=['POST'])
@role_required('admin')
def api_add_fabric():
    try:
        data = request.get_json()
        
        # Validation
        name, error = validate_required_string(data.get('name'), 'Fabric name', max_length=100)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        cost, error = validate_positive_number(data.get('cost_per_yard'), 'Cost per yard')
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        vendor_id = data.get('fabric_vendor_id')
        if vendor_id:
            vendor_id, error = validate_positive_integer(vendor_id, 'Vendor ID')
            if error:
                return jsonify({'success': False, 'error': error}), 400
        
        fabric = Fabric(
            name=name,
            cost_per_yard=cost,
            fabric_vendor_id=vendor_id,
            fabric_code=data.get('fabric_code', '').strip() if data.get('fabric_code') else None,
            color=data.get('color', '').strip() if data.get('color') else None
        )
        db.session.add(fabric)
        db.session.commit()
        
        return jsonify({'success': True, 'id': fabric.id})
    except Exception as e:
        app.logger.error(f"Error adding fabric: {e}")
        return jsonify({'success': False, 'error': 'Failed to add fabric'}), 500


# NOTION ENDPOINTS   
@app.route('/api/notions/<int:notion_id>', methods=['GET', 'PUT', 'DELETE'])
@role_required('admin')
def api_notion_detail(notion_id):
    notion = Notion.query.get_or_404(notion_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': notion.id,
            'name': notion.name,
            'cost_per_unit': notion.cost_per_unit,
            'notion_vendor_id': notion.notion_vendor_id,
            'unit_type': notion.unit_type
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'name' in data:
                name, error = validate_required_string(data.get('name'), 'Notion name', max_length=100)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                notion.name = name
            
            if 'cost_per_unit' in data:
                cost, error = validate_positive_number(data.get('cost_per_unit'), 'Cost per unit')
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                notion.cost_per_unit = cost
            
            if 'notion_vendor_id' in data:
                notion.notion_vendor_id = data.get('notion_vendor_id')
            
            if 'unit_type' in data:
                notion.unit_type = data.get('unit_type', 'each')
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating notion: {e}")
            return jsonify({'success': False, 'error': 'Failed to update notion'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(notion)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error deleting notion: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete notion'}), 500

@app.route('/api/notions', methods=['POST'])
@role_required('admin')
def api_add_notion():
    try:
        data = request.get_json()
        
        # Validation
        name, error = validate_required_string(data.get('name'), 'Notion name', max_length=100)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        cost, error = validate_positive_number(data.get('cost_per_unit'), 'Cost per unit')
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        vendor_id = data.get('notion_vendor_id')
        if vendor_id:
            vendor_id, error = validate_positive_integer(vendor_id, 'Vendor ID')
            if error:
                return jsonify({'success': False, 'error': error}), 400
        
        notion = Notion(
            name=name,
            cost_per_unit=cost,
            notion_vendor_id=vendor_id,
            unit_type=data.get('unit_type', 'each')
        )
        db.session.add(notion)
        db.session.commit()
        
        return jsonify({'success': True, 'id': notion.id})
    except Exception as e:
        app.logger.error(f"Error adding notion: {e}")
        return jsonify({'success': False, 'error': 'Failed to add notion'}), 500


# LABOR OPERATION ENDPOINTS
@app.route('/api/labors/<int:labor_id>', methods=['GET', 'PUT', 'DELETE'])
@role_required('admin')
def api_labor_detail(labor_id):
    labor = LaborOperation.query.get_or_404(labor_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': labor.id,
            'name': labor.name,
            'cost_type': labor.cost_type,
            'fixed_cost': labor.fixed_cost,
            'cost_per_hour': labor.cost_per_hour,
            'cost_per_piece': labor.cost_per_piece
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'name' in data:
                name, error = validate_required_string(data.get('name'), 'Labor operation name', max_length=100)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                labor.name = name
            
            if 'cost_type' in data:
                cost_type, error = validate_choice(
                    data.get('cost_type'), 
                    'Cost type', 
                    ['flat_rate', 'hourly', 'per_piece']
                )
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                labor.cost_type = cost_type
            
            if 'fixed_cost' in data:
                cost, error = validate_positive_number(data.get('fixed_cost'), 'Fixed cost', required=False)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                labor.fixed_cost = cost
            
            if 'cost_per_hour' in data:
                cost, error = validate_positive_number(data.get('cost_per_hour'), 'Cost per hour', required=False)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                labor.cost_per_hour = cost
            
            if 'cost_per_piece' in data:
                cost, error = validate_positive_number(data.get('cost_per_piece'), 'Cost per piece', required=False)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                labor.cost_per_piece = cost
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating labor: {e}")
            return jsonify({'success': False, 'error': 'Failed to update labor operation'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(labor)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error deleting labor: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete labor operation'}), 500
        


@app.route('/api/labors', methods=['POST'])
@role_required('admin')
def api_add_labor():
    try:
        data = request.get_json()
        
        # Validation
        name, error = validate_required_string(data.get('name'), 'Labor operation name', max_length=100)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        cost_type, error = validate_choice(
            data.get('cost_type'), 
            'Cost type', 
            ['flat_rate', 'hourly', 'per_piece']
        )
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        # Validate cost based on type
        fixed_cost = None
        cost_per_hour = None
        cost_per_piece = None
        
        if cost_type == 'flat_rate':
            fixed_cost, error = validate_positive_number(data.get('fixed_cost'), 'Fixed cost')
            if error:
                return jsonify({'success': False, 'error': error}), 400
        elif cost_type == 'hourly':
            cost_per_hour, error = validate_positive_number(data.get('cost_per_hour'), 'Cost per hour')
            if error:
                return jsonify({'success': False, 'error': error}), 400
        else:  # per_piece
            cost_per_piece, error = validate_positive_number(data.get('cost_per_piece'), 'Cost per piece')
            if error:
                return jsonify({'success': False, 'error': error}), 400
        
        labor = LaborOperation(
            name=name,
            cost_type=cost_type,
            fixed_cost=fixed_cost,
            cost_per_hour=cost_per_hour,
            cost_per_piece=cost_per_piece
        )
        db.session.add(labor)
        db.session.commit()
        
        return jsonify({'success': True, 'id': labor.id})
    except Exception as e:
        app.logger.error(f"Error adding labor: {e}")
        return jsonify({'success': False, 'error': 'Failed to add labor operation'}), 500


# CLEANING COST ENDPOINTS
@app.route('/api/cleanings/<int:cleaning_id>', methods=['GET', 'PUT', 'DELETE'])
@role_required('admin')
def api_cleaning_detail(cleaning_id):
    cleaning = CleaningCost.query.get_or_404(cleaning_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': cleaning.id,
            'garment_type': cleaning.garment_type,
            'fixed_cost': cleaning.fixed_cost,
            'avg_minutes': cleaning.avg_minutes
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'garment_type' in data:
                garment_type, error = validate_required_string(data.get('garment_type'), 'Garment type', max_length=50)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                cleaning.garment_type = garment_type
            
            if 'fixed_cost' in data:
                cost, error = validate_positive_number(data.get('fixed_cost'), 'Fixed cost')
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                cleaning.fixed_cost = cost
            
            if 'avg_minutes' in data:
                minutes, error = validate_positive_integer(data.get('avg_minutes'), 'Average minutes')
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                cleaning.avg_minutes = minutes
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating cleaning cost: {e}")
            return jsonify({'success': False, 'error': 'Failed to update cleaning cost'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(cleaning)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error deleting cleaning cost: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete cleaning cost'}), 500



@app.get("/api/cleaning-cost")
def get_cleaning_cost():
    """Get cleaning cost for a garment type"""
    garment_type = request.args.get('type', '').strip()
    if not garment_type:
        return jsonify({"error": "type parameter required"}), 400
    
    cc = CleaningCost.query.filter_by(garment_type=garment_type).first()
    if cc:
        return jsonify({
            "garment_type": cc.garment_type,
            "fixed_cost": float(cc.fixed_cost),
            "avg_minutes": cc.avg_minutes
        })
    return jsonify({"error": "Not found"}), 404

@app.route('/api/cleanings', methods=['POST'])
@role_required('admin')
def api_add_cleaning():
    try:
        data = request.get_json()
        
        # Validation
        garment_type, error = validate_required_string(data.get('garment_type'), 'Garment type', max_length=50)
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        fixed_cost, error = validate_positive_number(data.get('fixed_cost'), 'Fixed cost')
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        avg_minutes, error = validate_positive_integer(data.get('avg_minutes'), 'Average minutes')
        if error:
            return jsonify({'success': False, 'error': error}), 400
        
        cleaning = CleaningCost(
            garment_type=garment_type,
            fixed_cost=fixed_cost,
            avg_minutes=avg_minutes
        )
        db.session.add(cleaning)
        db.session.commit()
        
        return jsonify({'success': True, 'id': cleaning.id})
    except Exception as e:
        app.logger.error(f"Error adding cleaning cost: {e}")
        return jsonify({'success': False, 'error': 'Failed to add cleaning cost'}), 500
# ===== PLACEHOLDER ROUTES FOR FUTURE FEATURES =====
@app.route("/style/new")
@login_required
@admin_required  
def style_wizard():
    # Get all master data for dropdowns
    fabric_vendors = FabricVendor.query.order_by(FabricVendor.name).all()
    notion_vendors = NotionVendor.query.order_by(NotionVendor.name).all()
    fabrics = Fabric.query.order_by(Fabric.name).all()
    notions = Notion.query.order_by(Notion.name).all()
    # Get labor operations in the order you want them displayed
    labor_ops=[]
    fusion = LaborOperation.query.filter_by(name='FUSION').first()
    if fusion: labor_ops.append(fusion)
    marker = LaborOperation.query.filter_by(name='Marker+Cut').first()
    if marker: labor_ops.append(marker)
    sewing = LaborOperation.query.filter_by(name='Sewing').first()
    if sewing: labor_ops.append(sewing)
    button = LaborOperation.query.filter_by(name='Button/Snap/Grommet').first()
    if button: labor_ops.append(button)
    garment_types = [cc.garment_type for cc in CleaningCost.query.order_by(CleaningCost.garment_type).all()]
    size_ranges = SizeRange.query.order_by(SizeRange.name).all()
    label_cost_setting = GlobalSetting.query.filter_by(setting_key='avg_label_cost').first()
    shipping_cost_setting = GlobalSetting.query.filter_by(setting_key='shipping_cost').first()
    default_label_cost = label_cost_setting.setting_value if label_cost_setting else 0.20
    default_shipping_cost = shipping_cost_setting.setting_value if shipping_cost_setting else 0.00
    
    return render_template("style_wizard.html", 
                          fabric_vendors=fabric_vendors,
                          notion_vendors=notion_vendors,
                          fabrics=fabrics,
                          notions=notions,
                          labor_ops=labor_ops,
                          garment_types=garment_types,
                          size_ranges=size_ranges,
                          default_label_cost=default_label_cost,
                          default_shipping_cost=default_shipping_cost)

@app.route("/style/view")
@role_required('admin', 'user')  # Both can view
def style_view():
    """View style details (read-only for users)"""
    vendor_style = request.args.get('vendor_style', '')
    style_id = request.args.get('id')
    
    # ✅ FETCH THE STYLE!
    style = None
    if vendor_style:
        style = Style.query.filter_by(vendor_style=vendor_style).first()
    elif style_id:
        style = Style.query.get(style_id)
    
    if not style:
        flash('Style not found.', 'danger')
        return redirect(url_for('view_all_styles'))
    
    # Get all master data for display
    fabric_vendors = FabricVendor.query.order_by(FabricVendor.name).all()
    notion_vendors = NotionVendor.query.order_by(NotionVendor.name).all()
    fabrics = Fabric.query.order_by(Fabric.name).all()
    notions = Notion.query.order_by(Notion.name).all()
    
    labor_ops = []
    fusion = LaborOperation.query.filter_by(name='FUSION').first()
    if fusion: labor_ops.append(fusion)
    marker = LaborOperation.query.filter_by(name='Marker+Cut').first()
    if marker: labor_ops.append(marker)
    sewing = LaborOperation.query.filter_by(name='Sewing').first()
    if sewing: labor_ops.append(sewing)
    button = LaborOperation.query.filter_by(name='Button/Snap/Grommet').first()
    if button: labor_ops.append(button)
    
    garment_types = [cc.garment_type for cc in CleaningCost.query.order_by(CleaningCost.garment_type).all()]
    size_ranges = SizeRange.query.order_by(SizeRange.name).all()
    
    label_cost_setting = GlobalSetting.query.filter_by(setting_key='avg_label_cost').first()
    shipping_cost_setting = GlobalSetting.query.filter_by(setting_key='shipping_cost').first()
    default_label_cost = label_cost_setting.setting_value if label_cost_setting else 0.20
    default_shipping_cost = shipping_cost_setting.setting_value if shipping_cost_setting else 0.00
    
    # Get permissions
    permissions = get_user_permissions()
    
    return render_template("style_wizard.html",
                          style=style,  # ✅ PASS THE STYLE!
                          fabric_vendors=fabric_vendors,
                          notion_vendors=notion_vendors,
                          fabrics=fabrics,
                          notions=notions,
                          labor_ops=labor_ops,
                          garment_types=garment_types,
                          size_ranges=size_ranges,
                          default_label_cost=default_label_cost,
                          default_shipping_cost=default_shipping_cost,
                          permissions=permissions,
                          view_mode=not permissions['can_edit'])

@app.get("/api/style/by-name")
def api_style_by_name():
    """
    Read-only lookup by exact style_name (case-insensitive).
    Returns basics, first fabric + first notion, labor rows, and cleaning suggestion.
    """
    name = (request.args.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400

    style = Style.query.filter(func.lower(Style.style_name) == name.lower()).first()
    if not style:
        return jsonify({"found": False}), 404

    # first fabric (if any)
    frow = (
        db.session.query(StyleFabric, Fabric)
        .join(Fabric, StyleFabric.fabric_id == Fabric.id)
        .filter(StyleFabric.style_id == style.id)
        .order_by(StyleFabric.id.asc())
        .first()
    )
    fabric_payload = None
    if frow:
        sf, f = frow
        vendor_name = f.fabric_vendor.name if f.fabric_vendor else None
        fabric_payload = {
            "vendor": vendor_name,
            "name": f.name,
            "cost_per_yard": float(f.cost_per_yard or 0),
            "yards": float(sf.yards_required or 0),
            "primary": bool(sf.is_primary or False),
        }

    # first notion (if any)
    nrow = (
        db.session.query(StyleNotion, Notion)
        .join(Notion, StyleNotion.notion_id == Notion.id)
        .filter(StyleNotion.style_id == style.id)
        .order_by(StyleNotion.id.asc())
        .first()
    )
    notion_payload = None
    if nrow:
        sn, n = nrow
        vendor_name = n.notion_vendor.name if n.notion_vendor else None
        notion_payload = {
            "vendor": vendor_name,
            "name": n.name,
            "cost_per_unit": float(n.cost_per_unit or 0),
            "qty": float(sn.quantity_required or 0),
        }

    # labor list (ordered)
    labor_rows = (
        db.session.query(StyleLabor, LaborOperation)
        .join(LaborOperation, StyleLabor.labor_operation_id == LaborOperation.id)
        .filter(StyleLabor.style_id == style.id)
        .order_by(StyleLabor.id.asc())
        .all()
    )
    labor_payload = []
    for sl, op in labor_rows:
        # Get the correct rate based on cost_type
        rate = 0
        if op.cost_type == 'flat_rate':
            rate = float(op.fixed_cost or 0)
        elif op.cost_type == 'hourly':
            rate = float(op.cost_per_hour or 0)
        elif op.cost_type == 'per_piece':
            rate = float(op.cost_per_piece or 0)
        
        # Get quantity or hours - check both time_hours and quantity
        qty_or_hours = float(sl.time_hours or 0) if sl.time_hours else float(sl.quantity or 0)
        
        labor_payload.append({
            "name": op.name,
            "cost_type": op.cost_type or "flat_rate",
            "rate": rate,
            "qty_or_hours": qty_or_hours,
        })

    # cleaning suggestion by garment_type
    cleaning_payload = None
    if style.garment_type:
        cc = CleaningCost.query.filter_by(garment_type=style.garment_type).first()
        if cc:
            cleaning_payload = {
                "type": cc.garment_type,
                "cost": float(cc.fixed_cost or 0),
                "minutes": float(cc.avg_minutes or 0),
            }

    return jsonify({
        "found": True,
        "style": {
            "vendor_style": style.vendor_style,
            "base_item_number": style.base_item_number,
            "variant_code": style.variant_code,
            "style_name": style.style_name,
            "gender": style.gender,
            "garment_type": style.garment_type,
            "size_range": style.size_range,
        },
        "fabric": fabric_payload,
        "notion": notion_payload,
        "labor": labor_payload,
        "avg_label_cost": 0.20,
        "shipping_cost": 0.00,
        "cleaning": cleaning_payload,
    }), 200

# VARIABLE ENDPOINTS
@app.route('/api/variables', methods=['GET', 'POST'])
def api_variables():
    if request.method == 'GET':
        variables = Variable.query.order_by(Variable.name).all()
        return jsonify([{'id': v.id, 'name': v.name} for v in variables])
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validation
            name, error = validate_required_string(data.get('name'), 'Variable name', max_length=100)
            if error:
                return jsonify({'success': False, 'error': error}), 400
            
            # Check for duplicate
            existing = Variable.query.filter(func.lower(Variable.name) == name.lower()).first()
            if existing:
                return jsonify({'success': False, 'error': 'Variable already exists'}), 400
            
            variable = Variable(name=name)
            db.session.add(variable)
            db.session.commit()
            
            return jsonify({'success': True, 'id': variable.id})
        except Exception as e:
            app.logger.error(f"Error adding variable: {e}")
            return jsonify({'success': False, 'error': 'Failed to add variable'}), 500

@app.route('/api/variables/<int:variable_id>', methods=['GET', 'PUT', 'DELETE'])
def api_variable_detail(variable_id):
    variable = Variable.query.get_or_404(variable_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': variable.id,
            'name': variable.name
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'name' in data:
                name, error = validate_required_string(data.get('name'), 'Variable name', max_length=100)
                if error:
                    return jsonify({'success': False, 'error': error}), 400
                variable.name = name
            
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error updating variable: {e}")
            return jsonify({'success': False, 'error': 'Failed to update variable'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(variable)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            app.logger.error(f"Error deleting variable: {e}")
            return jsonify({'success': False, 'error': 'Failed to delete variable'}), 500
    
@app.route('/api/styles/search', methods=['GET'])
def search_styles():
    """Search styles by vendor_style or style_name"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
    
    # Search in both vendor_style and style_name
    styles = Style.query.filter(
        db.or_(
            Style.vendor_style.ilike(f'%{query}%'),
            Style.style_name.ilike(f'%{query}%')
        )
    ).order_by(Style.vendor_style).limit(20).all()
    
    return jsonify([{
        'vendor_style': s.vendor_style,
        'style_name': s.style_name
    } for s in styles])

@app.get("/api/style/by-vendor-style")
def api_style_by_vendor_style():
    """Load style by vendor_style code"""
    vendor_style = (request.args.get("vendor_style") or "").strip()
    if not vendor_style:
        return jsonify({"error": "vendor_style required"}), 400

    style = Style.query.filter_by(vendor_style=vendor_style).first()
    if not style:
        return jsonify({"found": False}), 404

    # Get ALL fabrics - UPDATE THIS SECTION
    fabric_rows = (
        db.session.query(StyleFabric, Fabric)
        .join(Fabric, StyleFabric.fabric_id == Fabric.id)
        .filter(StyleFabric.style_id == style.id)
        .order_by(StyleFabric.id.asc())
        .all()
    )
    fabrics_payload = []
    for sf, f in fabric_rows:
        vendor_name = f.fabric_vendor.name if f.fabric_vendor else None
        fabrics_payload.append({
            "vendor": vendor_name,
            "vendor_id": f.fabric_vendor_id,
            "name": f.name,
            "fabric_id": f.id,
            "cost_per_yard": float(f.cost_per_yard or 0),
            "yards": float(sf.yards_required or 0),
            "sublimation": bool(sf.is_sublimation or False),  # ADD THIS LINE
        })

    # Get ALL notions
    notion_rows = (
        db.session.query(StyleNotion, Notion)
        .join(Notion, StyleNotion.notion_id == Notion.id)
        .filter(StyleNotion.style_id == style.id)
        .order_by(StyleNotion.id.asc())
        .all()
    )
    notions_payload = []
    for sn, n in notion_rows:
        vendor_name = n.notion_vendor.name if n.notion_vendor else None
        notions_payload.append({
            "vendor": vendor_name,
            "vendor_id": n.notion_vendor_id,
            "name": n.name,
            "notion_id": n.id,
            "cost_per_unit": float(n.cost_per_unit or 0),
            "qty": float(sn.quantity_required or 0),
        })

    # Labor
    labor_rows = (
        db.session.query(StyleLabor, LaborOperation)
        .join(LaborOperation, StyleLabor.labor_operation_id == LaborOperation.id)
        .filter(StyleLabor.style_id == style.id)
        .order_by(StyleLabor.id.asc())
        .all()
    )
    labor_payload = []
    for sl, op in labor_rows:
        rate = 0
        if op.cost_type == 'flat_rate':
            rate = float(op.fixed_cost or 0)
        elif op.cost_type == 'hourly':
            rate = float(op.cost_per_hour or 0)
        elif op.cost_type == 'per_piece':
            rate = float(op.cost_per_piece or 0)
        
        qty_or_hours = float(sl.time_hours or 0) if sl.time_hours else float(sl.quantity or 0)
        
        labor_payload.append({
            "name": op.name,
            "rate": rate,
            "qty_or_hours": qty_or_hours,
        })

    # Cleaning
    cleaning_payload = None
    if style.garment_type:
        cc = CleaningCost.query.filter_by(garment_type=style.garment_type).first()
        if cc:
            cleaning_payload = {
                "cost": float(cc.fixed_cost or 0),
            }

    # Colors - NEW SECTION
    colors_payload = []
    color_rows = (
        db.session.query(StyleColor, Color)
        .join(Color, StyleColor.color_id == Color.id)
        .filter(StyleColor.style_id == style.id)
        .order_by(Color.name.asc())
        .all()
    )
    for sc, color in color_rows:
        colors_payload.append({
            "color_id": color.id,
            "name": color.name
        })
    
    # Variables - NEW SECTION - ADD THIS ENTIRE BLOCK
    variables_payload = []
    variable_rows = (
        db.session.query(StyleVariable, Variable)
        .join(Variable, StyleVariable.variable_id == Variable.id)
        .filter(StyleVariable.style_id == style.id)
        .order_by(Variable.name.asc())
        .all()
    )
    for sv, variable in variable_rows:
        variables_payload.append({
            "variable_id": variable.id,
            "name": variable.name
        })
    # Load from global settings instead of style record
    label_setting = GlobalSetting.query.filter_by(setting_key='avg_label_cost').first()
    shipping_setting = GlobalSetting.query.filter_by(setting_key='shipping_cost').first()

    return jsonify({
        "found": True,
        "style": {
            "id": style.id,
            "vendor_style": style.vendor_style,
            "base_item_number": style.base_item_number,
            "variant_code": style.variant_code,
            "style_name": style.style_name,
            "gender": style.gender,
            "garment_type": style.garment_type,
            "size_range": style.size_range,
            "margin": float(style.base_margin_percent or 60.0),  # NEW
            "label_cost": float(label_setting.setting_value) if label_setting else 0.20,
            "shipping_cost": float(shipping_setting.setting_value) if shipping_setting else 0.00,
            "suggested_price": float(style.suggested_price or 0) if style.suggested_price else None,  # NEW
            "notes": style.notes or '', 
        },
        "fabrics": fabrics_payload,
        "notions": notions_payload,
        "labor": labor_payload,
        "cleaning": cleaning_payload,
        "colors": colors_payload,
        "variables": variables_payload,  # NEW
}), 200


# ===== ENHANCED /api/style/save WITH FULL VALIDATION =====
# Replace your existing api_style_save function (starting at line ~2890)
# with this validated version

@app.post("/api/style/save")
@admin_required 
def api_style_save():
    """
    Save or update a Style with comprehensive validation.
    Prevents duplicates, invalid data, and ensures data integrity.
    """
    
    try:
        data = request.get_json(silent=True) or {}
        s = data.get("style") or {}
        
        # ===== STEP 1: VALIDATE REQUIRED FIELDS =====
        valid, style_name = validate_required_field(s.get("style_name"), "Style Name")
        if not valid:
            return jsonify({"error": style_name}), 400
        
        vendor_style = (s.get("vendor_style") or "").strip()
        
        # Validate vendor_style if provided
        if vendor_style:
            valid, vendor_style = validate_string_length(vendor_style, "Vendor Style", 50)
            if not valid:
                return jsonify({"error": vendor_style}), 400
        
        # Validate style_name length
        valid, style_name = validate_string_length(style_name, "Style Name", 200)
        if not valid:
            return jsonify({"error": style_name}), 400
       
        # ===== STEP 2: CHECK FOR DUPLICATES =====
        style_id = s.get("style_id")

        # If style_id exists and is a number, this is an UPDATE
        if style_id and isinstance(style_id, (int, float)) and style_id > 0:
            # UPDATING EXISTING STYLE
            existing_style = Style.query.get(int(style_id))
            if not existing_style:
                return jsonify({"error": "Style not found"}), 404
            is_new = False
        else:
            # CREATING NEW STYLE - check for duplicates
            if vendor_style:
                duplicate = Style.query.filter_by(vendor_style=vendor_style).first()
                if duplicate:
                    return jsonify({"error": f"Style '{vendor_style}' already exists! Search and load it to edit."}), 400
            
            duplicate_name = Style.query.filter(
                func.lower(Style.style_name) == style_name.lower()
            ).first()
            if duplicate_name:
                return jsonify({"error": f"Style name '{style_name}' already exists!"}), 400
            
            existing_style = Style()
            is_new = True

        style = existing_style
                
        # ===== STEP 3: VALIDATE NUMERIC FIELDS =====
        # Validate margin
        margin = s.get("margin", 60.0)
        valid, margin = validate_percentage(margin, "Margin")
        if not valid:
            return jsonify({"error": margin}), 400
        
        # Validate suggested price
        suggested_price = s.get("suggested_price")
        if suggested_price:
            valid, suggested_price = validate_positive_number(suggested_price, "Suggested Price", allow_zero=True)
            if not valid:
                return jsonify({"error": suggested_price}), 400
        else:
            suggested_price = None
        
        # ===== STEP 4: VALIDATE FABRIC DATA =====
        fabrics_data = data.get("fabrics") or []
        for idx, f in enumerate(fabrics_data):
            if f.get("name"):
                yards = f.get("yards", 0)
                if yards:
                    valid, yards_val = validate_positive_number(yards, f"Fabric #{idx+1} yards", allow_zero=False)
                    if not valid:
                        return jsonify({"error": yards_val}), 400
                    f["yards"] = yards_val  # Update with validated value
        
        # ===== STEP 5: VALIDATE NOTION DATA =====
        notions_data = data.get("notions") or []
        for idx, n in enumerate(notions_data):
            if n.get("name"):
                qty = n.get("qty", 0)
                if qty:
                    valid, qty_val = validate_positive_number(qty, f"Notion #{idx+1} quantity", allow_zero=False)
                    if not valid:
                        return jsonify({"error": qty_val}), 400
                    n["qty"] = qty_val  # Update with validated value
        
        # ===== STEP 6: UPDATE STYLE FIELDS =====
        style.style_name = style_name
        style.vendor_style = vendor_style if vendor_style else None
        style.base_item_number = (s.get("base_item_number") or None)
        style.variant_code = (s.get("variant_code") or None)
        style.gender = (s.get("gender") or None)
        style.garment_type = (s.get("garment_type") or None)
        style.size_range = (s.get("size_range") or None)
        style.notes = (s.get("notes") or None)
        style.base_margin_percent = margin
        style.suggested_price = suggested_price
        
        db.session.add(style)
        db.session.flush()
        
        # ===== STEP 7: REPLACE EXISTING RELATIONSHIPS =====
        StyleFabric.query.filter_by(style_id=style.id).delete()
        StyleNotion.query.filter_by(style_id=style.id).delete()
        StyleLabor.query.filter_by(style_id=style.id).delete()
        StyleColor.query.filter_by(style_id=style.id).delete()
        StyleVariable.query.filter_by(style_id=style.id).delete()
        db.session.flush()
        
        # ===== STEP 8: ADD FABRICS =====
        for f in fabrics_data:
            if f.get("name"):
                fabric_name = (f["name"] or "").strip()
                vendor_name = (f.get("vendor") or "").strip()
                
                fabric = Fabric.query.filter(
                    func.lower(Fabric.name) == fabric_name.lower()
                ).first()
                
                if not fabric:
                    vendor = None
                    if vendor_name:
                        vendor = FabricVendor.query.filter(
                            func.lower(FabricVendor.name) == vendor_name.lower()
                        ).first()
                        if not vendor:
                            vendor = FabricVendor(
                                name=vendor_name, 
                                vendor_code=vendor_name[:10].upper()
                            )
                            db.session.add(vendor)
                            db.session.flush()
                    
                    fabric = Fabric(
                        name=fabric_name,
                        cost_per_yard=float(f.get("cost_per_yard") or 0),
                        fabric_vendor_id=vendor.id if vendor else None
                    )
                    db.session.add(fabric)
                    db.session.flush()
                
                sf = StyleFabric(
                    style_id=style.id,
                    fabric_id=fabric.id,
                    yards_required=float(f.get("yards") or 0),
                    is_primary=bool(f.get("primary") or False),
                    is_sublimation=bool(f.get("sublimation") or False)
                )
                db.session.add(sf)
        
        # ===== STEP 9: ADD NOTIONS =====
        for n in notions_data:
            if n.get("name"):
                notion_name = (n["name"] or "").strip()
                vendor_name = (n.get("vendor") or "").strip()
                
                notion = Notion.query.filter(
                    func.lower(Notion.name) == notion_name.lower()
                ).first()
                
                if not notion:
                    vendor = None
                    if vendor_name:
                        vendor = NotionVendor.query.filter(
                            func.lower(NotionVendor.name) == vendor_name.lower()
                        ).first()
                        if not vendor:
                            vendor = NotionVendor(
                                name=vendor_name, 
                                vendor_code=vendor_name[:10].upper()
                            )
                            db.session.add(vendor)
                            db.session.flush()
                    
                    notion = Notion(
                        name=notion_name,
                        cost_per_unit=float(n.get("cost_per_unit") or 0),
                        unit_type='each',
                        notion_vendor_id=vendor.id if vendor else None
                    )
                    db.session.add(notion)
                    db.session.flush()
                
                sn = StyleNotion(
                    style_id=style.id,
                    notion_id=notion.id,
                    quantity_required=float(n.get("qty") or 0)
                )
                db.session.add(sn)
        
        # ===== STEP 10: ADD LABOR =====
        for l in data.get("labor") or []:
            if not l.get("name"):
                continue
            
            op = LaborOperation.query.filter(
                func.lower(LaborOperation.name) == l["name"].strip().lower()
            ).first()
            
            if not op:
                continue
            
            qty_or_hours = float(l.get("qty_or_hours") or 0)
            
            # Validate labor hours/quantity
            if qty_or_hours < 0:
                return jsonify({"error": f"Labor {l['name']} cannot have negative hours/quantity"}), 400
            
            if op.cost_type == 'hourly':
                sl = StyleLabor(
                    style_id=style.id,
                    labor_operation_id=op.id,
                    time_hours=qty_or_hours,
                    quantity=1
                )
            else:
                sl = StyleLabor(
                    style_id=style.id,
                    labor_operation_id=op.id,
                    time_hours=0,
                    quantity=int(qty_or_hours) if qty_or_hours else 1
                )
            db.session.add(sl)
        
        # ===== STEP 11: ADD COLORS =====
        for c in data.get("colors") or []:
            if c.get("name"):
                color_name = (c["name"] or "").strip()
                color = Color.query.filter(
                    func.lower(Color.name) == color_name.lower()
                ).first()
                
                if not color:
                    color = Color(name=color_name)
                    db.session.add(color)
                    db.session.flush()
                
                sc = StyleColor(style_id=style.id, color_id=color.id)
                db.session.add(sc)
        
        # ===== STEP 12: ADD VARIABLES =====
        for v in data.get("variables") or []:
            if v.get("name"):
                var_name = (v["name"] or "").strip()
                variable = Variable.query.filter(
                    func.lower(Variable.name) == var_name.lower()
                ).first()
                
                if not variable:
                    variable = Variable(name=var_name)
                    db.session.add(variable)
                    db.session.flush()
                
                sv = StyleVariable(style_id=style.id, variable_id=variable.id)
                db.session.add(sv)
        
        # ===== STEP 13: COMMIT ALL CHANGES =====
        db.session.commit()
        #Return appropriate message
        if is_new:
            message = "✅ New style created successfully!"
        else:
            message = "✅ Style updated successfully!"
        
        return jsonify({
            "ok": True,
            "new": is_new,
            "style_id": style.id,
            "message": message
        }), 200
    
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Save failed: {str(e)}"}), 500

# ===== END OF ENHANCED api_style_save =====
    
@app.get("/api/style/search")
def api_style_search():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify([])
    rows = (Style.query
            .filter(Style.style_name.ilike(f"%{q}%"))
            .order_by(Style.style_name.asc())
            .limit(20).all())
    return jsonify([r.style_name for r in rows])




@app.route('/import-excel', methods=['GET', 'POST'])
@admin_required
def import_excel():
    if request.method == 'GET':
        return """
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
            <h1>Import Excel Data</h1>
            <form method="POST" enctype="multipart/form-data">
                <div style="margin: 20px 0;">
                    <label>Select Excel File:</label><br>
                    <input type="file" name="excel_file" accept=".xlsx,.xls" required style="margin: 10px 0;">
                </div>
                <button type="submit" style="background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px;">Import Uniforms</button>
                <a href="/admin-panel" style="margin-left: 10px; background-color: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Cancel</a>
            </form>
        </div>
        """
    
    if 'excel_file' not in request.files:
        return "No file selected"
    
    file = request.files['excel_file']
    if file.filename == '':
        return "No file selected"
    
    try:
        # Read Excel file
        df = pd.read_excel(file)
        
        imported_count = 0
        errors = []
        current_style = None
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Check if this is a style header (row with Item#)
                if pd.notna(row.iloc[0]) and str(row.iloc[0]).replace('.', '').isdigit():
                    # This is a new uniform style
                    item_number = str(int(float(row.iloc[0])))  # Convert to clean integer string
                    style_name = str(row.iloc[1]) if pd.notna(row.iloc[1]) else f"Style {item_number}"
                    variant = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
                    
                    # Create vendor_style (your lookup key)
                    if variant and variant != "nan":
                        vendor_style = f"{item_number}-{variant}"
                    else:
                        vendor_style = item_number
                    
                    # Check if style already exists
                    existing_style = Style.query.filter_by(vendor_style=vendor_style).first()
                    if existing_style:
                        current_style = existing_style
                        continue
                    
                    # Determine gender from style name
                    gender = "UNISEX"
                    if "Mens" in style_name or "MENS" in style_name:
                        gender = "MENS"
                    elif "Ladies" in style_name or "LADIES" in style_name:
                        gender = "LADIES"
                    
                    # Create new style
                    current_style = Style(
                        vendor_style=vendor_style,
                        base_item_number=item_number,
                        variant_code=variant if variant != "nan" else None,
                        style_name=style_name,
                        gender=gender,
                        garment_type="IMPORTED",  # Default
                        size_range="XS-4XL"      # Default
                    )
                    db.session.add(current_style)
                    db.session.flush()  # Get the ID
                    imported_count += 1
                    
                # Check if this is a fabric row (under MATERIALS section)
                elif pd.notna(row.iloc[0]) and "Fabric" in str(row.iloc[0]) and current_style:
                    fabric_name = str(row.iloc[1]) if pd.notna(row.iloc[1]) else "Unknown Fabric"
                    cost_per_yard = float(row.iloc[2]) if pd.notna(row.iloc[2]) else 0.0
                    yards_required = float(row.iloc[3]) if pd.notna(row.iloc[3]) else 0.0
                    
                    # Find or create fabric
                    fabric = Fabric.query.filter_by(name=fabric_name).first()
                    if not fabric:
                        # Create imported vendor if needed
                        vendor = FabricVendor.query.filter_by(name="IMPORTED").first()
                        if not vendor:
                            vendor = FabricVendor(name="IMPORTED", vendor_code="IMP")
                            db.session.add(vendor)
                            db.session.flush()
                        
                        fabric = Fabric(
                            name=fabric_name,
                            cost_per_yard=cost_per_yard,
                            fabric_vendor_id=vendor.id
                        )
                        db.session.add(fabric)
                        db.session.flush()
                    
                    # Create style-fabric relationship
                    style_fabric = StyleFabric(
                        style_id=current_style.id,
                        fabric_id=fabric.id,
                        yards_required=yards_required
                    )
                    db.session.add(style_fabric)
                    
            except Exception as e:
                errors.append(f"Row {index}: {str(e)}")
                continue
        
        # Commit all changes
        db.session.commit()
        
        # Return results
        result_html = f"""
        <div style="max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
            <h1>Import Results</h1>
            <div style="background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Import Completed!</h3>
                <p><strong>{imported_count} uniform styles imported successfully</strong></p>
            </div>
        """
        
        if errors:
            result_html += f"""
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>Warnings ({len(errors)} issues):</h3>
                <ul>
            """
            for error in errors[:5]:  # Show first 5 errors
                result_html += f"<li>{error}</li>"
            if len(errors) > 5:
                result_html += f"<li>... and {len(errors) - 5} more issues</li>"
            result_html += "</ul></div>"
        
        result_html += """
            <div style="margin: 30px 0;">
                <a href="/view-all-styles" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Imported Styles</a>
                <a href="/import-excel" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Import More Files</a>
                <a href="/admin-panel" style="background-color: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Back to Admin</a>
            </div>
        </div>
        """
        
        return result_html
        
    except Exception as e:
        return f"<h1>Import Error:</h1><p>{str(e)}</p><a href='/import-excel'>Try Again</a>"
    

# ===== APPLICATION STARTUP =====
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Get debug mode from environment variable (defaults to False)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Safety check: Never allow debug in production
    if debug_mode and os.environ.get('FLASK_ENV') == 'production':
        raise ValueError("❌ CRITICAL: Cannot run with debug=True in production!")
    
    # Show warning if debug is enabled
    if debug_mode:
        app.logger.info("\n" + "="*70)
        app.logger.info("⚠️  WARNING: Running in DEBUG mode!")
        app.logger.info("⚠️  This is for development only - NEVER use in production!")
        app.logger.info("⚠️  Set FLASK_DEBUG=False in .env for production")
        app.logger.info("="*70 + "\n")
    
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)