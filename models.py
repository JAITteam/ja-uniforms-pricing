from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import pytz

def get_eastern_time():
    """Get current system time"""
    return datetime.now()
# ===== AUTHENTICATION =====
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='viewer')  # 'admin' or 'viewer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

# ===== VENDOR TABLES =====
class FabricVendor(db.Model):
    __tablename__ = 'fabric_vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vendor_code = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=get_eastern_time)

class NotionVendor(db.Model):
    __tablename__ = 'notion_vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    vendor_code = db.Column(db.String(20), unique=True)
    updated_at = db.Column(db.DateTime, default=get_eastern_time, onupdate=get_eastern_time)


# ===== PRODUCT TABLES =====
class Fabric(db.Model):
    __tablename__ = 'fabrics'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    fabric_code = db.Column(db.String(20))
    cost_per_yard = db.Column(db.Float, nullable=False)
    color = db.Column(db.String(50))
    fabric_vendor_id = db.Column(db.Integer, db.ForeignKey('fabric_vendors.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    fabric_vendor = db.relationship('FabricVendor', backref='fabrics')

class Notion(db.Model):
    __tablename__ = 'notions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cost_per_unit = db.Column(db.Float, nullable=False)
    unit_type = db.Column(db.String(20), default='each')
    notion_vendor_id = db.Column(db.Integer, db.ForeignKey('notion_vendors.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ===== CLEANING COSTS BY GARMENT TYPE =====
class CleaningCost(db.Model):
    __tablename__ = 'cleaning_costs'
    
    id = db.Column(db.Integer, primary_key=True)
    garment_type = db.Column(db.String(50), nullable=False, unique=True)
    fixed_cost = db.Column(db.Float, nullable=False)
    avg_minutes = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    #created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=get_eastern_time)
    
    def __repr__(self):
        return f'<SizeRange {self.name}>'

# ===== MAIN STYLE TABLE =====
class Style(db.Model):
    __tablename__ = 'styles'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor_style = db.Column(db.String(50), unique=True, nullable=False)  # "21324-3202"
    base_item_number = db.Column(db.String(20))  # "21324"
    variant_code = db.Column(db.String(20))      # "3202"
    style_name = db.Column(db.String(200),unique=True, nullable=False)
    gender = db.Column(db.String(20))            # "MENS", "LADIES", "UNISEX"
    garment_type = db.Column(db.String(50))      # "SS TOP/SS DRESS", "APRON", etc.
    size_range = db.Column(db.String(50))        # "XS-4XL"
    base_margin_percent = db.Column(db.Float, default=60.0)
    avg_label_cost = db.Column(db.Float, default=0.20)
    shipping_cost = db.Column(db.Float, default=0.00)  # ADD THIS
    suggested_price = db.Column(db.Float)  # ADD THIS
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=get_eastern_time, onupdate=get_eastern_time)
    last_modified_by = db.Column(db.String(100), default='Admin')
    is_active = db.Column(db.Boolean, default=True)
    is_favorite = db.Column(db.Boolean, default=False)
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

# ===== JUNCTION TABLES =====
class StyleFabric(db.Model):
    __tablename__ = 'style_fabrics'
    
    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id'), nullable=False)
    fabric_id = db.Column(db.Integer, db.ForeignKey('fabrics.id'), nullable=False)
    yards_required = db.Column(db.Float, nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    is_sublimation = db.Column(db.Boolean, default=False)  # ADD THIS
    notes = db.Column(db.String(200))
    
    style = db.relationship('Style', backref='style_fabrics')
    fabric = db.relationship('Fabric')

class StyleNotion(db.Model):
    __tablename__ = 'style_notions'
    
    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id'), nullable=False)
    notion_id = db.Column(db.Integer, db.ForeignKey('notions.id'), nullable=False)
    quantity_required = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String(200))
    
    style = db.relationship('Style', backref='style_notions')
    notion = db.relationship('Notion')

class Color(db.Model):
    __tablename__ = 'colors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    color_code = db.Column(db.String(50))  # Optional: for hex codes or reference codes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Color {self.name}>'

class Variable(db.Model):
    __tablename__ = 'variables'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Variable {self.name}>'

class StyleVariable(db.Model):
    __tablename__ = 'style_variables'
    
    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id'), nullable=False)
    variable_id = db.Column(db.Integer, db.ForeignKey('variables.id'), nullable=False)
    
    style = db.relationship('Style')
    variable = db.relationship('Variable')
    
# Create junction table for Style-Color relationship
class StyleColor(db.Model):
    __tablename__ = 'style_colors'
    
    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id'), nullable=False)
    color_id = db.Column(db.Integer, db.ForeignKey('colors.id'), nullable=False)
    
    style = db.relationship('Style', back_populates='colors')
    color = db.relationship('Color')

class StyleImage(db.Model):
    __tablename__ = 'style_images'
    
    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    style = db.relationship('Style', backref='images')

class StyleLabor(db.Model):
    __tablename__ = 'style_labor'
    
    id = db.Column(db.Integer, primary_key=True)
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id'), nullable=False)
    labor_operation_id = db.Column(db.Integer, db.ForeignKey('labor_operations.id'), nullable=False)
    time_hours = db.Column(db.Float)  # For hourly operations
    # Standardize on minutes everywhere
    #time_minutes = db.Column(db.Float)  # Instead of time_hours
    quantity = db.Column(db.Integer, default=1)  # For flat rate/per piece operations
    notes = db.Column(db.String(200))
    
    style = db.relationship('Style', backref='style_labor')
    labor_operation = db.relationship('LaborOperation')

class GlobalSetting(db.Model):
    __tablename__ = 'global_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<GlobalSetting {self.setting_key}={self.setting_value}>'

# ===== SAMPLE DATA FUNCTION =====
def create_complete_sample():
    """Create complete sample data with all your business requirements"""
    
    if User.query.first():
        return "Sample data already exists"
    
    # Create users
    admin = User(username='ruben', role='admin')
    admin.set_password('admin123')
    viewer = User(username='employee', role='viewer')
    viewer.set_password('view123')
    db.session.add_all([admin, viewer])
    
    # Create vendors
    carr = FabricVendor(name='CARR TEXTILES', vendor_code='V100')
    wawak = NotionVendor(name='WAWAK', vendor_code='N100')
    db.session.add_all([carr, wawak])
    db.session.flush()
    
    # Create your 5 labor operations
    labor_ops = [
        LaborOperation(name='FUSION', cost_type='flat_rate', fixed_cost=1.50),
        LaborOperation(name='Marker+Cut', cost_type='flat_rate', fixed_cost=1.50),
        LaborOperation(name='Sewing', cost_type='hourly', cost_per_hour=19.32),
        LaborOperation(name='Button/Snap/Grommet', cost_type='per_piece', cost_per_piece=0.15),
    ]
    db.session.add_all(labor_ops)
    
    # Create cleaning costs
    cleaning_costs = [
        CleaningCost(garment_type='APRON', fixed_cost=0.96, avg_minutes=3),
        CleaningCost(garment_type='VEST', fixed_cost=1.28, avg_minutes=4),
        CleaningCost(garment_type='SS TOP/SS DRESS', fixed_cost=1.60, avg_minutes=5),
        CleaningCost(garment_type='LS TOP/LS DRESS', fixed_cost=2.24, avg_minutes=7),
        CleaningCost(garment_type='SHORTS/SKIRTS', fixed_cost=1.28, avg_minutes=4),
        CleaningCost(garment_type='PANTS', fixed_cost=1.60, avg_minutes=5),
        CleaningCost(garment_type='SS JACKET/LINED SS DRESS', fixed_cost=3.20, avg_minutes=10),
        CleaningCost(garment_type='LS JACKET/LINED LS DRESS', fixed_cost=3.84, avg_minutes=12),
    ]
    db.session.add_all(cleaning_costs)
    
    # Create size variants
    sizes = [
        SizeVariant(size_name='XS', size_category='regular', price_multiplier=1.0),
        SizeVariant(size_name='S', size_category='regular', price_multiplier=1.0),
        SizeVariant(size_name='M', size_category='regular', price_multiplier=1.0),
        SizeVariant(size_name='L', size_category='regular', price_multiplier=1.0),
        SizeVariant(size_name='XL', size_category='regular', price_multiplier=1.0),
        SizeVariant(size_name='2XL', size_category='extended', price_multiplier=1.15),
        SizeVariant(size_name='3XL', size_category='extended', price_multiplier=1.15),
        SizeVariant(size_name='4XL', size_category='extended', price_multiplier=1.15),
    ]
    db.session.add_all(sizes)
    db.session.flush()
    
    # Create products
    fabric = Fabric(name='XANADU', fabric_code='3202', cost_per_yard=6.00, color='TEAL', fabric_vendor_id=carr.id)
    notion = Notion(name='18L SPORT BUTTON', cost_per_unit=0.04, unit_type='each', notion_vendor_id=wawak.id)
    db.session.add_all([fabric, notion])
    db.session.flush()
    
    # Create sample style
    style = Style(
        vendor_style='21324-3202',
        base_item_number='21324',
        variant_code='3202',
        style_name='SHIRT, MENS LARGO CAMP W/ SLEEVE TAB',
        gender='MENS',
        garment_type='SS TOP/SS DRESS',
        size_range='XS-4XL',
        base_margin_percent=60.0
    )
    db.session.add(style)
    db.session.flush()
    
    # Create BOM relationships
    style_fabric = StyleFabric(style_id=style.id, fabric_id=fabric.id, yards_required=1.5, is_primary=True)
    style_notion = StyleNotion(style_id=style.id, notion_id=notion.id, quantity_required=7)
    
    # Add labor operations to style
    sewing_op = LaborOperation.query.filter_by(name='Sewing').first()
    fusion_op = LaborOperation.query.filter_by(name='FUSION').first()
    marker_op = LaborOperation.query.filter_by(name='Marker+Cut').first()
    button_op = LaborOperation.query.filter_by(name='Button/Snap/Grommet').first()
    
    style_labor = [
        StyleLabor(style_id=style.id, labor_operation_id=fusion_op.id, quantity=1),
        StyleLabor(style_id=style.id, labor_operation_id=marker_op.id, quantity=1),
        StyleLabor(style_id=style.id, labor_operation_id=sewing_op.id, time_hours=0.55),
        StyleLabor(style_id=style.id, labor_operation_id=button_op.id, quantity=7),
    ]
    
    db.session.add_all([style_fabric, style_notion] + style_labor)
    db.session.commit()
    
    return "Complete uniform pricing sample data created successfully!"