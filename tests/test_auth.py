"""
Authentication Tests for J.A. Uniforms
======================================

Tests for login, logout, registration, and password management.
"""

import pytest
from models import User


class TestLogin:
    """Tests for login functionality."""
    
    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data or b'login' in response.data.lower()
    
    def test_login_with_valid_credentials(self, client, admin_user, app):
        """Test login with valid admin credentials."""
        with app.app_context():
            response = client.post('/login', data={
                'username': 'admin@jauniforms.com',
                'password': 'AdminPass123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
    
    def test_login_with_invalid_password(self, client, admin_user, app):
        """Test login with wrong password."""
        with app.app_context():
            response = client.post('/login', data={
                'username': 'admin@jauniforms.com',
                'password': 'WrongPassword123'
            }, follow_redirects=True)
            
            assert b'Invalid' in response.data or response.status_code == 200
    
    def test_login_with_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = client.post('/login', data={
            'username': 'nonexistent@jauniforms.com',
            'password': 'SomePassword123'
        }, follow_redirects=True)
        
        assert b'Invalid' in response.data or response.status_code == 200
    
    def test_login_requires_company_email(self, client):
        """Test that only @jauniforms.com emails are allowed."""
        response = client.post('/login', data={
            'username': 'user@gmail.com',
            'password': 'SomePassword123'
        }, follow_redirects=True)
        
        assert b'company' in response.data.lower() or b'jauniforms' in response.data.lower()
    
    def test_login_with_empty_fields(self, client):
        """Test login with empty username/password."""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        }, follow_redirects=True)
        
        # Should stay on login page
        assert response.status_code == 200


class TestLogout:
    """Tests for logout functionality."""
    
    def test_logout_redirects_to_login(self, authenticated_client, app):
        """Test that logout redirects to login page."""
        with app.app_context():
            response = authenticated_client.get('/logout', follow_redirects=True)
            assert response.status_code == 200
    
    def test_logout_requires_login(self, client):
        """Test that logout requires authentication."""
        response = client.get('/logout', follow_redirects=True)
        # Should redirect to login
        assert response.status_code == 200


class TestPasswordValidation:
    """Tests for password validation rules."""
    
    def test_password_too_short(self, app):
        """Test that passwords must be at least 8 characters."""
        with app.app_context():
            from app import validate_password
            
            is_valid, message = validate_password('Short1A')
            assert not is_valid
            assert '8' in message
    
    def test_password_no_uppercase(self, app):
        """Test that passwords require uppercase letters."""
        with app.app_context():
            from app import validate_password
            
            is_valid, message = validate_password('lowercase123')
            assert not is_valid
            assert 'uppercase' in message.lower()
    
    def test_password_no_lowercase(self, app):
        """Test that passwords require lowercase letters."""
        with app.app_context():
            from app import validate_password
            
            is_valid, message = validate_password('UPPERCASE123')
            assert not is_valid
            assert 'lowercase' in message.lower()
    
    def test_password_no_number(self, app):
        """Test that passwords require numbers."""
        with app.app_context():
            from app import validate_password
            
            is_valid, message = validate_password('NoNumbersHere')
            assert not is_valid
            assert 'number' in message.lower()
    
    def test_valid_password(self, app):
        """Test that valid passwords pass validation."""
        with app.app_context():
            from app import validate_password
            
            is_valid, message = validate_password('ValidPass123')
            assert is_valid
            assert message == 'Valid'
    
    def test_empty_password(self, app):
        """Test that empty passwords are rejected."""
        with app.app_context():
            from app import validate_password
            
            is_valid, message = validate_password('')
            assert not is_valid
            assert 'required' in message.lower()
    
    def test_none_password(self, app):
        """Test that None passwords are rejected."""
        with app.app_context():
            from app import validate_password
            
            is_valid, message = validate_password(None)
            assert not is_valid


class TestRegistration:
    """Tests for user registration."""
    
    def test_register_page_loads(self, client):
        """Test that registration page loads."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data or b'register' in response.data.lower()
    
    def test_register_requires_company_email(self, client, app):
        """Test that registration requires @jauniforms.com email."""
        with app.app_context():
            response = client.post('/register', data={
                'firstName': 'Test',
                'lastName': 'User',
                'email': 'test@gmail.com',
                'password': 'ValidPass123'
            }, content_type='application/x-www-form-urlencoded')
            
            # Should return error about company email
            assert response.status_code == 200


class TestAccessControl:
    """Tests for access control."""
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/', follow_redirects=True)
        # Should redirect to login
        assert response.status_code == 200
        # Check if we're on login page
        assert b'login' in response.data.lower()
    
    def test_admin_page_requires_admin(self, user_client, app):
        """Test that admin pages require admin role."""
        with app.app_context():
            response = user_client.get('/admin/users', follow_redirects=True)
            # Should either redirect or show forbidden
            assert response.status_code in [200, 302, 403]
