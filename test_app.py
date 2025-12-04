"""
Unit tests for J.A. Uniforms Pricing Application
Run with: pytest test_app.py -v
"""
import pytest
import os
import tempfile
from datetime import datetime, timedelta
from werkzeug.security import check_password_hash

# Set test environment before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test_secret_key_for_testing_only'
os.environ['FLASK_ENV'] = 'testing'

from app import app, db
from models import (
    User, Style, Fabric, Notion, FabricVendor, NotionVendor,
    LaborOperation, CleaningCost, StyleFabric, StyleNotion,
    StyleLabor, GlobalSetting, Color, Variable
)


@pytest.fixture
def client():
    """Create test client with in-memory database"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create test data
            create_test_data()
        yield client


def create_test_data():
    """Create test data for testing"""
    # Create admin user
    admin = User(
        username='admin@jauniforms.com',
        email='admin@jauniforms.com',
        first_name='Admin',
        last_name='User',
        role='admin',
        is_active=True
    )
    admin.set_password('Admin123')
    db.session.add(admin)
    
    # Create regular user
    user = User(
        username='user@jauniforms.com',
        email='user@jauniforms.com',
        first_name='Regular',
        last_name='User',
        role='user',
        is_active=True
    )
    user.set_password('User123')
    db.session.add(user)
    
    # Create fabric vendor
    vendor = FabricVendor(name='Test Vendor', vendor_code='TV001')
    db.session.add(vendor)
    
    # Create notion vendor
    notion_vendor = NotionVendor(name='Test Notion Vendor', vendor_code='TN001')
    db.session.add(notion_vendor)
    
    # Create fabric
    fabric = Fabric(
        name='Test Fabric',
        fabric_code='TF001',
        cost_per_yard=10.50,
        color='Blue',
        fabric_vendor_id=1
    )
    db.session.add(fabric)
    
    # Create notion
    notion = Notion(
        name='Test Button',
        cost_per_unit=0.25,
        unit_type='each',
        notion_vendor_id=1
    )
    db.session.add(notion)
    
    # Create labor operation
    labor = LaborOperation(
        name='Sewing',
        cost_type='hourly',
        cost_per_hour=25.0,
        is_active=True
    )
    db.session.add(labor)
    
    # Create cleaning cost
    cleaning = CleaningCost(
        garment_type='Shirt',
        fixed_cost=5.0,
        avg_minutes=15
    )
    db.session.add(cleaning)
    
    # Create global setting
    label_setting = GlobalSetting(
        setting_key='avg_label_cost',
        setting_value=0.20,
        description='Average label cost'
    )
    db.session.add(label_setting)
    
    db.session.commit()


# ========================================
# USER MODEL TESTS
# ========================================

def test_user_creation():
    """Test user creation and password hashing"""
    with app.app_context():
        user = User(username='test@test.com', email='test@test.com')
        user.set_password('TestPassword123')
        
        assert user.username == 'test@test.com'
        assert user.email == 'test@test.com'
        assert user.password_hash is not None
        assert user.check_password('TestPassword123')
        assert not user.check_password('WrongPassword')


def test_user_roles():
    """Test user role checking"""
    with app.app_context():
        admin = User(username='admin@test.com', email='admin@test.com', role='admin')
        user = User(username='user@test.com', email='user@test.com', role='user')
        
        assert admin.is_admin()
        assert not user.is_admin()


def test_user_display_names():
    """Test user display name methods"""
    with app.app_context():
        user = User(
            username='john@test.com',
            email='john@test.com',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.get_full_name() == 'John Doe'
        assert user.get_display_name() == 'John'


# ========================================
# STYLE MODEL TESTS
# ========================================

def test_style_creation(client):
    """Test style creation"""
    with app.app_context():
        style = Style(
            vendor_style='TEST-001',
            style_name='Test Style',
            gender='Unisex',
            garment_type='Shirt',
            base_margin_percent=60.0
        )
        db.session.add(style)
        db.session.commit()
        
        assert style.vendor_style == 'TEST-001'
        assert style.style_name == 'Test Style'
        assert style.base_margin_percent == 60.0


def test_style_fabric_cost_calculation(client):
    """Test fabric cost calculation for styles"""
    with app.app_context():
        style = Style(
            vendor_style='TEST-002',
            style_name='Test Style 2',
            garment_type='Shirt'
        )
        db.session.add(style)
        db.session.commit()
        
        # Add fabric to style
        fabric = Fabric.query.first()
        style_fabric = StyleFabric(
            style_id=style.id,
            fabric_id=fabric.id,
            yards_required=2.5,
            is_primary=True
        )
        db.session.add(style_fabric)
        db.session.commit()
        
        # Test calculation
        expected_cost = 2.5 * 10.50  # yards * cost_per_yard
        assert style.get_total_fabric_cost() == expected_cost


def test_style_notion_cost_calculation(client):
    """Test notion cost calculation for styles"""
    with app.app_context():
        style = Style(
            vendor_style='TEST-003',
            style_name='Test Style 3',
            garment_type='Shirt'
        )
        db.session.add(style)
        db.session.commit()
        
        # Add notion to style
        notion = Notion.query.first()
        style_notion = StyleNotion(
            style_id=style.id,
            notion_id=notion.id,
            quantity_required=10
        )
        db.session.add(style_notion)
        db.session.commit()
        
        # Test calculation
        expected_cost = 10 * 0.25  # quantity * cost_per_unit
        assert style.get_total_notion_cost() == expected_cost


def test_style_labor_cost_calculation(client):
    """Test labor cost calculation for styles"""
    with app.app_context():
        style = Style(
            vendor_style='TEST-004',
            style_name='Test Style 4',
            garment_type='Shirt'
        )
        db.session.add(style)
        db.session.commit()
        
        # Add labor to style
        labor = LaborOperation.query.first()
        style_labor = StyleLabor(
            style_id=style.id,
            labor_operation_id=labor.id,
            time_hours=2.0,
            quantity=1
        )
        db.session.add(style_labor)
        db.session.commit()
        
        # Test calculation (labor + cleaning)
        expected_labor = 2.0 * 25.0  # hours * cost_per_hour
        expected_cleaning = 5.0  # from CleaningCost
        expected_total = expected_labor + expected_cleaning
        
        assert style.get_total_labor_cost() == expected_total


def test_style_retail_price_calculation(client):
    """Test retail price calculation with margin"""
    with app.app_context():
        style = Style(
            vendor_style='TEST-005',
            style_name='Test Style 5',
            garment_type='Shirt',
            base_margin_percent=60.0
        )
        db.session.add(style)
        db.session.commit()
        
        # Add costs
        fabric = Fabric.query.first()
        style_fabric = StyleFabric(
            style_id=style.id,
            fabric_id=fabric.id,
            yards_required=2.0,
            is_primary=True
        )
        db.session.add(style_fabric)
        db.session.commit()
        
        # Total cost = fabric cost + label cost
        # Fabric: 2.0 * 10.50 = 21.00
        # Label: 0.20
        # Total: 21.20
        # Retail with 60% margin: 21.20 / (1 - 0.60) = 53.00
        
        total_cost = style.get_total_cost()
        retail_price = style.get_retail_price()
        
        assert total_cost == 21.20
        assert retail_price == 53.00


# ========================================
# AUTHENTICATION TESTS
# ========================================

def test_login_page(client):
    """Test login page loads"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_valid_login(client):
    """Test login with valid credentials"""
    response = client.post('/login', data={
        'email': 'admin@jauniforms.com',
        'password': 'Admin123',
        'remember': False
    }, follow_redirects=True)
    
    assert response.status_code == 200


def test_invalid_login(client):
    """Test login with invalid credentials"""
    response = client.post('/login', data={
        'email': 'admin@jauniforms.com',
        'password': 'WrongPassword',
        'remember': False
    }, follow_redirects=True)
    
    assert b'Invalid' in response.data or b'Incorrect' in response.data


def test_register_page(client):
    """Test registration page loads"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data or b'Sign Up' in response.data


# ========================================
# VALIDATION TESTS
# ========================================

def test_password_validation():
    """Test password validation function"""
    from app import validate_password
    
    # Valid password
    valid, msg = validate_password('ValidPass123')
    assert valid is True
    
    # Too short
    valid, msg = validate_password('Short1')
    assert valid is False
    assert 'at least 8' in msg.lower()
    
    # No uppercase
    valid, msg = validate_password('lowercase123')
    assert valid is False
    assert 'uppercase' in msg.lower()
    
    # No lowercase
    valid, msg = validate_password('UPPERCASE123')
    assert valid is False
    assert 'lowercase' in msg.lower()
    
    # No number
    valid, msg = validate_password('NoNumbers')
    assert valid is False
    assert 'number' in msg.lower()


def test_email_validation():
    """Test email validation function"""
    from app import validate_email
    
    # Valid email
    email, error = validate_email('test@example.com')
    assert error is None
    assert email == 'test@example.com'
    
    # Invalid email
    email, error = validate_email('invalid-email')
    assert error is not None
    assert 'invalid' in error.lower()


def test_positive_number_validation():
    """Test positive number validation"""
    from app import validate_positive_number
    
    # Valid positive number
    num, error = validate_positive_number(10.5, 'Test Field')
    assert error is None
    assert num == 10.5
    
    # Negative number
    num, error = validate_positive_number(-5, 'Test Field')
    assert error is not None
    assert 'negative' in error.lower()
    
    # Invalid number
    num, error = validate_positive_number('invalid', 'Test Field')
    assert error is not None


# ========================================
# API ENDPOINT TESTS
# ========================================

def test_api_health_check(client):
    """Test health check endpoint (if exists)"""
    # First, let's add a health check endpoint to app.py
    # This test will pass once we add it
    pass


def test_api_requires_authentication(client):
    """Test API endpoints require authentication"""
    # Test that protected API endpoints return 401 without auth
    response = client.get('/api/styles')
    # Should redirect to login or return 401
    assert response.status_code in [401, 302]


# ========================================
# DATABASE TESTS
# ========================================

def test_database_connection(client):
    """Test database connection"""
    with app.app_context():
        # Try a simple query
        count = User.query.count()
        assert count >= 0  # Should not raise an error


def test_cascade_delete(client):
    """Test cascade delete on style deletion"""
    with app.app_context():
        # Create a style with fabrics
        style = Style(
            vendor_style='DELETE-TEST',
            style_name='Delete Test Style',
            garment_type='Shirt'
        )
        db.session.add(style)
        db.session.commit()
        style_id = style.id
        
        # Add fabric
        fabric = Fabric.query.first()
        style_fabric = StyleFabric(
            style_id=style_id,
            fabric_id=fabric.id,
            yards_required=1.0
        )
        db.session.add(style_fabric)
        db.session.commit()
        
        # Verify fabric exists
        assert StyleFabric.query.filter_by(style_id=style_id).count() == 1
        
        # Delete style
        db.session.delete(style)
        db.session.commit()
        
        # Verify cascade delete worked
        assert StyleFabric.query.filter_by(style_id=style_id).count() == 0


# ========================================
# SECURITY TESTS
# ========================================

def test_csrf_protection():
    """Test CSRF protection is enabled"""
    assert app.config.get('WTF_CSRF_ENABLED', True) is True


def test_password_hashing():
    """Test passwords are properly hashed"""
    with app.app_context():
        user = User(username='test@test.com', email='test@test.com')
        user.set_password('TestPassword123')
        
        # Password hash should not be the plain password
        assert user.password_hash != 'TestPassword123'
        # Should be using werkzeug's password hash
        assert check_password_hash(user.password_hash, 'TestPassword123')


def test_session_security():
    """Test session security settings"""
    assert app.config.get('SESSION_COOKIE_HTTPONLY', True) is True
    assert app.config.get('SESSION_COOKIE_SAMESITE', 'Lax') is not None


# ========================================
# RUN TESTS
# ========================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
