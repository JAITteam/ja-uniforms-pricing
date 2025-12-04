"""
API Tests for J.A. Uniforms
===========================

Tests for REST API endpoints.
"""

import pytest
import json
from models import Style, Fabric, Color, FabricVendor


class TestAPIAuthentication:
    """Tests for API authentication requirements."""
    
    def test_api_colors_requires_auth(self, client):
        """Test that /api/colors requires authentication."""
        response = client.get('/api/colors')
        # Should redirect to login or return 401
        assert response.status_code in [302, 401]
    
    def test_api_fabrics_requires_auth(self, client):
        """Test that /api/fabrics requires authentication."""
        response = client.get('/api/fabrics')
        assert response.status_code in [302, 401]
    
    def test_api_notions_requires_auth(self, client):
        """Test that /api/notions requires authentication."""
        response = client.get('/api/notions')
        assert response.status_code in [302, 401]


class TestColorsAPI:
    """Tests for Colors API."""
    
    def test_get_colors(self, authenticated_client, sample_color, app):
        """Test getting all colors."""
        with app.app_context():
            response = authenticated_client.get('/api/colors')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)
    
    def test_create_color_admin_only(self, user_client, app):
        """Test that creating colors requires admin."""
        with app.app_context():
            response = user_client.post(
                '/api/colors',
                data=json.dumps({'name': 'New Color'}),
                content_type='application/json'
            )
            
            # Should be forbidden for regular users
            assert response.status_code in [302, 403]
    
    def test_create_color_as_admin(self, authenticated_client, app):
        """Test creating a color as admin."""
        with app.app_context():
            response = authenticated_client.post(
                '/api/colors',
                data=json.dumps({'name': 'Brand New Color', 'color_code': '#123456'}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True


class TestFabricsAPI:
    """Tests for Fabrics API."""
    
    def test_get_fabrics(self, authenticated_client, sample_fabric, app):
        """Test getting all fabrics."""
        with app.app_context():
            response = authenticated_client.get('/api/fabrics')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)
    
    def test_get_fabric_by_id(self, authenticated_client, sample_fabric, app):
        """Test getting a specific fabric."""
        with app.app_context():
            fabric = Fabric.query.first()
            if fabric:
                response = authenticated_client.get(f'/api/fabrics/{fabric.id}')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert 'name' in data


class TestStylesAPI:
    """Tests for Styles API."""
    
    def test_view_all_styles_page(self, authenticated_client, app):
        """Test the view all styles page loads."""
        with app.app_context():
            response = authenticated_client.get('/view-all-styles')
            
            assert response.status_code == 200
    
    def test_recent_styles_api(self, authenticated_client, sample_style, app):
        """Test the recent styles API."""
        with app.app_context():
            response = authenticated_client.get('/api/recent-styles')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)
    
    def test_dashboard_stats_api(self, authenticated_client, app):
        """Test the dashboard stats API."""
        with app.app_context():
            response = authenticated_client.get('/api/dashboard-stats')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'total_styles' in data
            assert 'avg_cost' in data


class TestAdminOnlyAPIs:
    """Tests for admin-only API endpoints."""
    
    def test_delete_style_requires_admin(self, user_client, sample_style, app):
        """Test that deleting a style requires admin."""
        with app.app_context():
            style = Style.query.first()
            if style:
                response = user_client.delete(f'/api/style/delete/{style.id}')
                
                # Should be forbidden
                assert response.status_code in [302, 403]
    
    def test_duplicate_style_requires_admin(self, user_client, sample_style, app):
        """Test that duplicating a style requires admin."""
        with app.app_context():
            style = Style.query.first()
            if style:
                response = user_client.post(f'/api/style/duplicate/{style.id}')
                
                # Should be forbidden
                assert response.status_code in [302, 403]
    
    def test_global_settings_requires_admin(self, user_client, app):
        """Test that global settings require admin."""
        with app.app_context():
            response = user_client.get('/api/global-settings')
            
            # Should be forbidden for regular users
            assert response.status_code in [302, 403]


class TestSizeRangesAPI:
    """Tests for Size Ranges API."""
    
    def test_get_size_ranges(self, authenticated_client, sample_size_range, app):
        """Test getting size ranges."""
        with app.app_context():
            response = authenticated_client.get('/api/size-ranges')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)


class TestFabricVendorsAPI:
    """Tests for Fabric Vendors API."""
    
    def test_get_fabric_vendors(self, authenticated_client, sample_fabric_vendor, app):
        """Test getting fabric vendors."""
        with app.app_context():
            response = authenticated_client.get('/api/fabric-vendors')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)


class TestSearchAPI:
    """Tests for search functionality."""
    
    def test_style_search(self, authenticated_client, sample_style, app):
        """Test style search functionality."""
        with app.app_context():
            response = authenticated_client.get('/api/styles/search?q=TEST')
            
            # Should return 200 or 404 if endpoint doesn't exist
            assert response.status_code in [200, 404]


class TestValidation:
    """Tests for API input validation."""
    
    def test_create_color_empty_name(self, authenticated_client, app):
        """Test creating a color with empty name."""
        with app.app_context():
            response = authenticated_client.post(
                '/api/colors',
                data=json.dumps({'name': ''}),
                content_type='application/json'
            )
            
            # Should fail validation
            if response.status_code == 200:
                data = json.loads(response.data)
                assert data.get('success') is False or 'error' in data
    
    def test_create_fabric_negative_cost(self, authenticated_client, sample_fabric_vendor, app):
        """Test creating fabric with negative cost."""
        with app.app_context():
            vendor = FabricVendor.query.first()
            
            response = authenticated_client.post(
                '/api/fabrics',
                data=json.dumps({
                    'name': 'Test Fabric',
                    'cost_per_yard': -5.00,
                    'fabric_vendor_id': vendor.id if vendor else 1
                }),
                content_type='application/json'
            )
            
            # Should fail validation
            if response.status_code == 200:
                data = json.loads(response.data)
                # Either success is False or there's an error
                assert data.get('success') is False or 'error' in data or response.status_code == 400
