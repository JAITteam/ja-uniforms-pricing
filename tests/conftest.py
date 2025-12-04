"""
Test Configuration for J.A. Uniforms
=====================================

This file contains pytest fixtures used across all tests.
"""

import pytest
import os
import sys

# Add the parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from database import db
from models import (
    User, Style, Fabric, FabricVendor, Notion, NotionVendor,
    LaborOperation, CleaningCost, Color, Variable, SizeRange,
    GlobalSetting
)


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    # Set testing configuration
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'LOGIN_DISABLED': False,
        'SERVER_NAME': 'localhost.localdomain',
        'SECRET_KEY': 'test-secret-key-for-testing-only',
        'MAIL_SUPPRESS_SEND': True,
    })
    
    # Create all tables
    with flask_app.app_context():
        db.create_all()
        
        # Create default global settings
        label_setting = GlobalSetting(
            setting_key='avg_label_cost',
            setting_value=0.20,
            description='Average label cost per garment'
        )
        db.session.add(label_setting)
        db.session.commit()
    
    yield flask_app
    
    # Cleanup
    with flask_app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        # Check if user already exists
        existing = User.query.filter_by(email='admin@jauniforms.com').first()
        if existing:
            return existing
        
        user = User(
            username='admin@jauniforms.com',
            email='admin@jauniforms.com',
            first_name='Admin',
            last_name='User',
            role='admin',
            is_active=True
        )
        user.set_password('AdminPass123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def regular_user(app):
    """Create a regular user for testing."""
    with app.app_context():
        # Check if user already exists
        existing = User.query.filter_by(email='user@jauniforms.com').first()
        if existing:
            return existing
        
        user = User(
            username='user@jauniforms.com',
            email='user@jauniforms.com',
            first_name='Regular',
            last_name='User',
            role='user',
            is_active=True
        )
        user.set_password('UserPass123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_fabric_vendor(app):
    """Create a sample fabric vendor."""
    with app.app_context():
        vendor = FabricVendor(
            name='Test Fabric Vendor',
            vendor_code='TFV01'
        )
        db.session.add(vendor)
        db.session.commit()
        return vendor


@pytest.fixture
def sample_fabric(app, sample_fabric_vendor):
    """Create a sample fabric."""
    with app.app_context():
        # Re-query the vendor to ensure it's attached to this session
        vendor = FabricVendor.query.filter_by(vendor_code='TFV01').first()
        
        fabric = Fabric(
            name='Test Polyester',
            fabric_code='TP001',
            cost_per_yard=5.50,
            color='Blue',
            fabric_vendor_id=vendor.id
        )
        db.session.add(fabric)
        db.session.commit()
        return fabric


@pytest.fixture
def sample_notion_vendor(app):
    """Create a sample notion vendor."""
    with app.app_context():
        vendor = NotionVendor(
            name='Test Notion Vendor',
            vendor_code='TNV01'
        )
        db.session.add(vendor)
        db.session.commit()
        return vendor


@pytest.fixture
def sample_notion(app, sample_notion_vendor):
    """Create a sample notion."""
    with app.app_context():
        # Re-query the vendor
        vendor = NotionVendor.query.filter_by(vendor_code='TNV01').first()
        
        notion = Notion(
            name='Test Button',
            cost_per_unit=0.10,
            unit_type='each',
            notion_vendor_id=vendor.id
        )
        db.session.add(notion)
        db.session.commit()
        return notion


@pytest.fixture
def sample_labor_operation(app):
    """Create a sample labor operation."""
    with app.app_context():
        operation = LaborOperation(
            name='Test Sewing',
            cost_type='hourly',
            cost_per_hour=15.00,
            is_active=True
        )
        db.session.add(operation)
        db.session.commit()
        return operation


@pytest.fixture
def sample_color(app):
    """Create a sample color."""
    with app.app_context():
        color = Color(
            name='Navy Blue',
            color_code='#000080'
        )
        db.session.add(color)
        db.session.commit()
        return color


@pytest.fixture
def sample_size_range(app):
    """Create a sample size range."""
    with app.app_context():
        size_range = SizeRange(
            name='Standard Adult',
            regular_sizes='XS, S, M, L, XL',
            extended_sizes='2XL, 3XL, 4XL',
            extended_markup_percent=15.0,
            description='Standard adult size range'
        )
        db.session.add(size_range)
        db.session.commit()
        return size_range


@pytest.fixture
def sample_style(app, sample_fabric, sample_size_range):
    """Create a sample style."""
    with app.app_context():
        # Re-query related objects
        size_range = SizeRange.query.filter_by(name='Standard Adult').first()
        
        style = Style(
            vendor_style='TEST-001',
            style_name='Test Polo Shirt',
            gender='UNISEX',
            garment_type='POLO',
            size_range=size_range.name if size_range else 'XS-4XL',
            base_margin_percent=60.0,
            notes='Test style for unit testing'
        )
        db.session.add(style)
        db.session.commit()
        return style


@pytest.fixture
def authenticated_client(client, admin_user, app):
    """Create a test client that's already logged in as admin."""
    with app.app_context():
        with client.session_transaction() as sess:
            # Simulate login
            sess['user_id'] = admin_user.id
            sess['_fresh'] = True
        
        # Actually log in
        client.post('/login', data={
            'username': 'admin@jauniforms.com',
            'password': 'AdminPass123'
        }, follow_redirects=True)
    
    return client


@pytest.fixture
def user_client(client, regular_user, app):
    """Create a test client logged in as regular user."""
    with app.app_context():
        client.post('/login', data={
            'username': 'user@jauniforms.com',
            'password': 'UserPass123'
        }, follow_redirects=True)
    
    return client
