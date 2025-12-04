"""
Model Tests for J.A. Uniforms
=============================

Tests for database models and their methods.
"""

import pytest
from models import (
    User, Style, Fabric, FabricVendor, Notion, NotionVendor,
    LaborOperation, Color, Variable, SizeRange, GlobalSetting,
    StyleFabric, StyleNotion, StyleLabor
)
from database import db


class TestUserModel:
    """Tests for User model."""
    
    def test_user_creation(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                username='newuser@jauniforms.com',
                email='newuser@jauniforms.com',
                first_name='New',
                last_name='User',
                role='user'
            )
            user.set_password('TestPass123')
            
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'newuser@jauniforms.com'
            assert user.role == 'user'
    
    def test_password_hashing(self, app):
        """Test that passwords are properly hashed."""
        with app.app_context():
            user = User(username='test@jauniforms.com', email='test@jauniforms.com')
            user.set_password('mypassword')
            
            # Password should be hashed, not plain text
            assert user.password_hash != 'mypassword'
            # Should be able to verify correct password
            assert user.check_password('mypassword')
            # Should reject wrong password
            assert not user.check_password('wrongpassword')
    
    def test_is_admin(self, app):
        """Test admin role checking."""
        with app.app_context():
            admin = User(username='admin@test.com', email='admin@test.com', role='admin')
            user = User(username='user@test.com', email='user@test.com', role='user')
            
            assert admin.is_admin() is True
            assert user.is_admin() is False
    
    def test_get_display_name_with_first_name(self, app):
        """Test display name with first name set."""
        with app.app_context():
            user = User(
                username='john@jauniforms.com',
                email='john@jauniforms.com',
                first_name='John'
            )
            assert user.get_display_name() == 'John'
    
    def test_get_display_name_without_first_name(self, app):
        """Test display name falling back to email prefix."""
        with app.app_context():
            user = User(
                username='jane.doe@jauniforms.com',
                email='jane.doe@jauniforms.com'
            )
            # Should use email prefix
            assert 'jane' in user.get_display_name().lower()
    
    def test_get_full_name(self, app):
        """Test full name generation."""
        with app.app_context():
            user = User(
                username='john@jauniforms.com',
                email='john@jauniforms.com',
                first_name='John',
                last_name='Doe'
            )
            assert user.get_full_name() == 'John Doe'


class TestStyleModel:
    """Tests for Style model."""
    
    def test_style_creation(self, app):
        """Test creating a new style."""
        with app.app_context():
            style = Style(
                vendor_style='STYLE-001',
                style_name='Test Polo',
                gender='MENS',
                garment_type='POLO',
                size_range='XS-4XL',
                base_margin_percent=60.0
            )
            db.session.add(style)
            db.session.commit()
            
            assert style.id is not None
            assert style.vendor_style == 'STYLE-001'
            assert style.base_margin_percent == 60.0
    
    def test_style_unique_vendor_style(self, app):
        """Test that vendor_style must be unique."""
        with app.app_context():
            style1 = Style(
                vendor_style='UNIQUE-001',
                style_name='First Style'
            )
            db.session.add(style1)
            db.session.commit()
            
            style2 = Style(
                vendor_style='UNIQUE-001',  # Same as style1
                style_name='Second Style'
            )
            db.session.add(style2)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_style_fabric_relationship(self, app, sample_fabric):
        """Test style-fabric relationship."""
        with app.app_context():
            # Create style
            style = Style(
                vendor_style='FAB-TEST-001',
                style_name='Fabric Test Style'
            )
            db.session.add(style)
            db.session.commit()
            
            # Re-query fabric
            fabric = Fabric.query.first()
            
            # Create relationship
            style_fabric = StyleFabric(
                style_id=style.id,
                fabric_id=fabric.id,
                yards_required=2.5,
                is_primary=True
            )
            db.session.add(style_fabric)
            db.session.commit()
            
            # Verify relationship
            style = Style.query.filter_by(vendor_style='FAB-TEST-001').first()
            assert len(style.style_fabrics) == 1
            assert style.style_fabrics[0].yards_required == 2.5
    
    def test_get_total_fabric_cost(self, app, sample_fabric):
        """Test fabric cost calculation."""
        with app.app_context():
            # Create style
            style = Style(
                vendor_style='COST-TEST-001',
                style_name='Cost Test Style'
            )
            db.session.add(style)
            db.session.commit()
            
            # Re-query fabric (cost = 5.50 per yard)
            fabric = Fabric.query.first()
            
            # Add fabric (2 yards @ $5.50 = $11.00)
            style_fabric = StyleFabric(
                style_id=style.id,
                fabric_id=fabric.id,
                yards_required=2.0,
                is_primary=True,
                is_sublimation=False
            )
            db.session.add(style_fabric)
            db.session.commit()
            
            style = Style.query.filter_by(vendor_style='COST-TEST-001').first()
            assert style.get_total_fabric_cost() == 11.00


class TestFabricModel:
    """Tests for Fabric model."""
    
    def test_fabric_creation(self, app, sample_fabric_vendor):
        """Test creating a fabric."""
        with app.app_context():
            vendor = FabricVendor.query.first()
            
            fabric = Fabric(
                name='Cotton Blend',
                fabric_code='CB001',
                cost_per_yard=4.25,
                color='White',
                fabric_vendor_id=vendor.id
            )
            db.session.add(fabric)
            db.session.commit()
            
            assert fabric.id is not None
            assert fabric.cost_per_yard == 4.25
    
    def test_fabric_vendor_relationship(self, app, sample_fabric):
        """Test fabric-vendor relationship."""
        with app.app_context():
            fabric = Fabric.query.first()
            
            assert fabric.fabric_vendor is not None
            assert fabric.fabric_vendor.vendor_code == 'TFV01'


class TestLaborOperationModel:
    """Tests for LaborOperation model."""
    
    def test_hourly_labor_operation(self, app):
        """Test creating hourly labor operation."""
        with app.app_context():
            operation = LaborOperation(
                name='Sewing',
                cost_type='hourly',
                cost_per_hour=15.00,
                is_active=True
            )
            db.session.add(operation)
            db.session.commit()
            
            assert operation.cost_type == 'hourly'
            assert operation.cost_per_hour == 15.00
    
    def test_flat_rate_labor_operation(self, app):
        """Test creating flat rate labor operation."""
        with app.app_context():
            operation = LaborOperation(
                name='Fusion',
                cost_type='flat_rate',
                fixed_cost=5.00,
                is_active=True
            )
            db.session.add(operation)
            db.session.commit()
            
            assert operation.cost_type == 'flat_rate'
            assert operation.fixed_cost == 5.00
    
    def test_per_piece_labor_operation(self, app):
        """Test creating per-piece labor operation."""
        with app.app_context():
            operation = LaborOperation(
                name='Button Attachment',
                cost_type='per_piece',
                cost_per_piece=0.25,
                is_active=True
            )
            db.session.add(operation)
            db.session.commit()
            
            assert operation.cost_type == 'per_piece'
            assert operation.cost_per_piece == 0.25


class TestColorModel:
    """Tests for Color model."""
    
    def test_color_creation(self, app):
        """Test creating a color."""
        with app.app_context():
            color = Color(
                name='Royal Blue',
                color_code='#4169E1'
            )
            db.session.add(color)
            db.session.commit()
            
            assert color.id is not None
            assert color.name == 'Royal Blue'
    
    def test_color_unique_name(self, app):
        """Test that color names are unique."""
        with app.app_context():
            color1 = Color(name='UNIQUE COLOR')
            db.session.add(color1)
            db.session.commit()
            
            color2 = Color(name='UNIQUE COLOR')  # Same name
            db.session.add(color2)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()


class TestSizeRangeModel:
    """Tests for SizeRange model."""
    
    def test_size_range_creation(self, app):
        """Test creating a size range."""
        with app.app_context():
            size_range = SizeRange(
                name='Youth Sizes',
                regular_sizes='YXS, YS, YM, YL, YXL',
                extended_sizes='',
                extended_markup_percent=0,
                description='Youth size range'
            )
            db.session.add(size_range)
            db.session.commit()
            
            assert size_range.id is not None
            assert size_range.name == 'Youth Sizes'
    
    def test_extended_markup(self, app, sample_size_range):
        """Test extended size markup."""
        with app.app_context():
            size_range = SizeRange.query.filter_by(name='Standard Adult').first()
            
            assert size_range.extended_markup_percent == 15.0
            assert '2XL' in size_range.extended_sizes


class TestGlobalSettingModel:
    """Tests for GlobalSetting model."""
    
    def test_global_setting_retrieval(self, app):
        """Test retrieving global settings."""
        with app.app_context():
            label_setting = GlobalSetting.query.filter_by(
                setting_key='avg_label_cost'
            ).first()
            
            assert label_setting is not None
            assert label_setting.setting_value == 0.20
    
    def test_global_setting_update(self, app):
        """Test updating global settings."""
        with app.app_context():
            label_setting = GlobalSetting.query.filter_by(
                setting_key='avg_label_cost'
            ).first()
            
            label_setting.setting_value = 0.25
            db.session.commit()
            
            # Re-query to verify
            updated = GlobalSetting.query.filter_by(
                setting_key='avg_label_cost'
            ).first()
            assert updated.setting_value == 0.25
