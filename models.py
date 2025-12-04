from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class VerificationCode(db.Model):
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    code = db.Column(db.String(6), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
   
    
    def is_expired(self):
        return datetime.now() > self.expires_at
    

def get_current_time():
    """Get current  time - use this for all database timestamps"""
    return datetime.now()

        
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)  
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)  
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False, index=True)  
    is_active = db.Column(db.Boolean, default=True, index=True)  
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
     # Password Reset Fields
    must_change_password = db.Column(db.Boolean, default=False)
    temp_password_created_at = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_full_name(self):
        """Return full name or email if names not set"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.full_name:
            return self.full_name
        elif self.first_name:
            return self.first_name
        else:
            return self.email.split('@')[0].title()
    
    def get_display_name(self):
        """Return first name or email prefix"""
        if self.first_name:
            return self.first_name
        elif self.full_name:
            return self.full_name.split()[0]
        elif self.email:
            return self.email.split('@')[0].title()
        elif self.username:
            return self.username.split('@')[0].title()
        else:
            return 'User'
    
    def __repr__(self):
        return f'<User {self.email}>'

# ===== VENDOR TABLES =====
class FabricVendor(db.Model):
    __tablename__ = 'fabric_vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vendor_code = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

class NotionVendor(db.Model):
    __tablename__ = 'notion_vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vendor_code = db.Column(db.String(20), unique=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


# ===== PRODUCT TABLES =====
class Fabric(db.Model):
    __tablename__ = 'fabrics'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    fabric_code = db.Column(db.String(20))
    cost_per_yard = db.Column(db.Float, nullable=False)
    color = db.Column(db.String(50))
    fabric_vendor_id = db.Column(db.Integer, db.ForeignKey('fabric_vendors.id'), index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    fabric_vendor = db.relationship('FabricVendor', backref='fabrics')

class Notion(db.Model):
    __tablename__ = 'notions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    cost_per_unit = db.Column(db.Float, nullable=False)
    unit_type = db.Column(db.String(20), default='each')
    notion_vendor_id = db.Column(db.Integer, db.ForeignKey('notion_vendors.id'), index=True)  
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    notion_vendor = db.relationship('NotionVendor', backref='notions')

# ===== LABOR OPERATIONS (Your 5 Operations) =====
class LaborOperation(db.Model):
    __tablename__ = 'labor_operations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    cost_type = db.Column(db.String(20), nullable=False)  # 'flat_rate', 'hourly', 'per_piece'
    fixed_cost = db.Column(db.Float)  # For FUSION, Marker+Cut
    cost_per_hour = db.Column(db.Float)  # For Sewing
    cost_per_piece = db.Column(db.Float)  # For Button/Snap/Grommet
    is_active = db.Column(db.Boolean, default=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# ===== CLEANING COSTS BY GARMENT TYPE =====
class CleaningCost(db.Model):
    __tablename__ = 'cleaning_costs'
    
    id = db.Column(db.Integer, primary_key=True)
    garment_type = db.Column(db.String(50), nullable=False, unique=True)
    fixed_cost = db.Column(db.Float, nullable=False)
    avg_minutes = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

# ===== SIZE VARIANTS =====
class SizeVariant(db.Model):
    __tablename__ = 'size_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    size_name = db.Column(db.String(10), nullable=False)  # "XS", "S", "M", "L", "XL", "2XL", "3XL", "4XL"
    size_category = db.Column(db.String(20), nullable=False)  # "regular", "extended"
    price_multiplier = db.Column(db.Float, default=1.0)  # 1.0 for regular, 1.15 for extended

class SizeRange(db.Model):
    __tablename__ = 'size_ranges'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    regular_sizes = db.Column(db.String(100), nullable=False)
    extended_sizes = db.Column(db.String(100))
    extended_markup_percent = db.Column(db.Float, default=15.0)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<SizeRange {self.name}>'

# ===== MAIN STYLE TABLE =====
class Style(db.Model):
    __tablename__ = 'styles'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_style = db.Column(db.String(50), unique=True, nullable=False, index=True)
    base_item_number = db.Column(db.String(20))
    variant_code = db.Column(db.String(20))
    style_name = db.Column(db.String(200), unique=True, nullable=False, index=True)
    gender = db.Column(db.String(20), index=True)
    garment_type = db.Column(db.String(50), index=True)
    size_range = db.Column(db.String(50))
    base_margin_percent = db.Column(db.Float, default=60.0, index=True)
    avg_label_cost = db.Column(db.Float, default=0.20)
    shipping_cost = db.Column(db.Float, default=0.00)
    suggested_price = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, index=True)
    last_modified_by = db.Column(db.String(100), default='Admin')
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_favorite = db.Column(db.Boolean, default=False, index=True)
    colors = db.relationship('StyleColor', back_populates='style', cascade='all, delete-orphan')
    
    def get_total_fabric_cost(self):
        total = 0
        for sf in self.style_fabrics:
            base_cost = sf.yards_required * sf.fabric.cost_per_yard
            # Add $6 sublimation upcharge if checked
            if sf.is_sublimation:
                base_cost += 6.00 * sf.yards_required
            total += base_cost
        return round(total, 2)
        
    def get_total_notion_cost(self):
        total = 0
        for sn in self.style_notions:
            total += sn.quantity_required * sn.notion.cost_per_unit
        return round(total, 2)
    
   
    def get_total_labor_cost(self):
        total = 0
        
        # Regular labor operations
        for sl in self.style_labor:
            labor_op = sl.labor_operation
            # Skip if labor operation was deleted
            if not labor_op:
                continue
            if labor_op.cost_type == 'flat_rate':
                total += (labor_op.fixed_cost or 0) * (sl.quantity or 1)
            elif labor_op.cost_type == 'hourly':
                total += (labor_op.cost_per_hour or 0) * (sl.time_hours or 0)
            elif labor_op.cost_type == 'per_piece':
                total += (labor_op.cost_per_piece or 0) * (sl.quantity or 1)
        
        if self.garment_type:
            cleaning_cost = CleaningCost.query.filter_by(garment_type=self.garment_type).first()
            if cleaning_cost:
                total += cleaning_cost.fixed_cost
        
        return round(total, 2)
    
    def get_total_cost(self):
        # Always load label cost from global settings
        label_setting = GlobalSetting.query.filter_by(setting_key='avg_label_cost').first()
        label_cost = label_setting.setting_value if label_setting else 0.20
        
        return self.get_total_fabric_cost() + self.get_total_notion_cost() + self.get_total_labor_cost() + label_cost
    
    def get_retail_price(self, size_multiplier=1.0):
        base_cost = self.get_total_cost() * size_multiplier
        margin = self.base_margin_percent / 100.0
        return round(base_cost / (1 - margin), 2)


# =============================================================================
# JUNCTION TABLES - WITH INDEXES ON FOREIGN KEYS FOR BETTER QUERY PERFORMANCE
# =============================================================================

class StyleFabric(db.Model):
    __tablename__ = 'style_fabrics'
    __table_args__ = (db.UniqueConstraint('style_id', 'fabric_id', name='uq_style_fabric'),)

    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX
    fabric_id = db.Column(db.Integer, db.ForeignKey('fabrics.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX
    yards_required = db.Column(db.Float, nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    is_sublimation = db.Column(db.Boolean, default=False)
    notes = db.Column(db.String(200))

    style = db.relationship('Style', backref=db.backref('style_fabrics', cascade='all, delete-orphan'))
    fabric = db.relationship('Fabric')


class StyleNotion(db.Model):
    __tablename__ = 'style_notions'
    __table_args__ = (db.UniqueConstraint('style_id', 'notion_id', name='uq_style_notion'),)
    
    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX
    notion_id = db.Column(db.Integer, db.ForeignKey('notions.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX
    quantity_required = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String(200))
    
    style = db.relationship('Style', backref='style_notions')
    notion = db.relationship('Notion')


class Color(db.Model):
    __tablename__ = 'colors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)  # ← ADDED INDEX
    color_code = db.Column(db.String(50))  # Optional: for hex codes or reference codes
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Color {self.name}>'


class Variable(db.Model):
    __tablename__ = 'variables'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)  # ← ADDED INDEX
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Variable {self.name}>'


class StyleVariable(db.Model):
    __tablename__ = 'style_variables'
    __table_args__ = (db.UniqueConstraint('style_id', 'variable_id', name='uq_style_variable'),)


    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX
    variable_id = db.Column(db.Integer, db.ForeignKey('variables.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX

    style = db.relationship('Style', backref=db.backref('style_variables', cascade='all, delete-orphan'))
    variable = db.relationship('Variable')

    
class StyleColor(db.Model):
    __tablename__ = 'style_colors'
    __table_args__ = (db.UniqueConstraint('style_id', 'color_id', name='uq_style_color'),)

    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX

    style = db.relationship('Style', back_populates='colors')
    color = db.relationship('Color')


class StyleImage(db.Model):
    __tablename__ = 'style_images'

    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX
    filename = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)

    style = db.relationship('Style', backref=db.backref('images', cascade='all, delete-orphan'))


class StyleLabor(db.Model):
    __tablename__ = 'style_labor'
    __table_args__ = (db.UniqueConstraint('style_id', 'labor_operation_id', name='uq_style_labor'),)
    
    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX
    labor_operation_id = db.Column(db.Integer, db.ForeignKey('labor_operations.id', ondelete='CASCADE'), nullable=False, index=True)  # ← ADDED INDEX
    time_hours = db.Column(db.Float)
    quantity = db.Column(db.Integer, default=1)
    notes = db.Column(db.String(200))

    style = db.relationship('Style', backref=db.backref('style_labor', cascade='all, delete-orphan'))
    labor_operation = db.relationship('LaborOperation')


class GlobalSetting(db.Model):
    __tablename__ = 'global_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False, index=True)  # ← ADDED INDEX
    setting_value = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f'<GlobalSetting {self.setting_key}={self.setting_value}>'