import pandas as pd
from flask import Config, Flask, request, redirect, url_for
from flask import jsonify, request
from sqlalchemy import func
from database import db
#from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, Response
from config import Config
from database import db
from datetime import datetime
import os
import csv
from io import StringIO
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from models import (
    Style, Fabric, FabricVendor, Notion, NotionVendor, 
    LaborOperation, CleaningCost, StyleFabric, StyleNotion, 
    StyleLabor, Color, StyleColor, Variable, StyleVariable,
    SizeRange, GlobalSetting
)



# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)


# Initialize CSRF protection
csrf = CSRFProtect(app)


UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database with app
db.init_app(app)

# Import models AFTER db is initialized
from models import *

# ===== MAIN APPLICATION ROUTES =====
@app.route('/')
def index():
    """Dashboard with real-time stats"""
    
    # Get real counts
    total_styles = Style.query.count()
    total_fabrics = Fabric.query.count()
    total_notions = Notion.query.count()
    total_fabric_vendors = FabricVendor.query.count()
    total_notion_vendors = NotionVendor.query.count()
    
    # Get recent styles (last 4)
    recent_styles = Style.query.order_by(Style.id.desc()).limit(4).all()
    
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

# ===== DATABASE SETUP AND TEST ROUTES =====
@app.route('/test-db')
def test_db():
    try:
        db.create_all()
        return "<h1>Database connected successfully!</h1><p>All tables created!</p><a href='/create-complete-data'>Create Complete Sample Data</a>"
    except Exception as e:
        return f"<h1>Database error:</h1><p>{str(e)}</p>"
@app.route('/fix-cleaning-costs')
def fix_cleaning_costs():
    """Add missing cleaning cost records"""
    
    all_cleaning_costs = [
        {'garment_type': 'APRON', 'avg_minutes': 3, 'fixed_cost': 0.96},
        {'garment_type': 'VEST', 'avg_minutes': 4, 'fixed_cost': 1.28},
        {'garment_type': 'SS TOP/SS DRESS', 'avg_minutes': 5, 'fixed_cost': 1.60},
        {'garment_type': 'LS TOP/LS DRESS', 'avg_minutes': 7, 'fixed_cost': 2.24},
        {'garment_type': 'SHORTS/SKIRTS', 'avg_minutes': 4, 'fixed_cost': 1.28},
        {'garment_type': 'PANTS', 'avg_minutes': 5, 'fixed_cost': 1.60},
        {'garment_type': 'SS JACKET/LINED SS DRESS', 'avg_minutes': 10, 'fixed_cost': 3.20},
        {'garment_type': 'LS JACKET/LINED LS DRESS', 'avg_minutes': 12, 'fixed_cost': 3.84},
    ]
    
    added = 0
    for item in all_cleaning_costs:
        existing = CleaningCost.query.filter_by(garment_type=item['garment_type']).first()
        if not existing:
            cc = CleaningCost(
                garment_type=item['garment_type'],
                avg_minutes=item['avg_minutes'],
                fixed_cost=item['fixed_cost']
            )
            db.session.add(cc)
            added += 1
    
    db.session.commit()
    return f"<h1>Added {added} missing cleaning costs!</h1><a href='/master-costs'>View Master Costs</a>"

@app.route('/debug-cleaning')
def debug_cleaning():
    """Debug cleaning costs"""
    cleaning_costs = CleaningCost.query.all()
    
    html = "<h1>Cleaning Costs in Database</h1>"
    html += f"<p>Total records: {len(cleaning_costs)}</p>"
    html += "<table border='1' cellpadding='10'>"
    html += "<tr><th>ID</th><th>Garment Type</th><th>Minutes</th><th>Cost</th></tr>"
    
    for cc in cleaning_costs:
        html += f"<tr><td>{cc.id}</td><td>{cc.garment_type}</td><td>{cc.avg_minutes}</td><td>${cc.fixed_cost}</td></tr>"
    
    html += "</table>"
    
    # Test the API for each garment type
    html += "<h2>API Test Results</h2>"
    test_types = [
        'APRON', 'VEST', 'PANTS', 'SHORTS/SKIRTS',
        'SS TOP/SS DRESS', 'LS TOP/LS DRESS',
        'SS JACKET/LINED SS DRESS', 'LS JACKET/LINED LS DRESS'
    ]
    
    html += "<table border='1' cellpadding='10'>"
    html += "<tr><th>Garment Type</th><th>API Result</th></tr>"
    
    for gt in test_types:
        cc = CleaningCost.query.filter_by(garment_type=gt).first()
        if cc:
            html += f"<tr><td>{gt}</td><td style='color:green'>Found: ${cc.fixed_cost}</td></tr>"
        else:
            html += f"<tr><td>{gt}</td><td style='color:red'>NOT FOUND</td></tr>"
    
    html += "</table>"
    html += "<br><a href='/fix-cleaning-costs'>Fix Missing Records</a>"
    return html
@app.route('/create-complete-data')
def create_complete_data():
    try:
        result = create_complete_sample()
        return f"<h1>Success!</h1><p>{result}</p><a href='/test-complete-lookup'>Test Complete Lookup</a>"
    except Exception as e:
        return f"<h1>Error:</h1><p>{str(e)}</p>"

@app.route('/test-complete-lookup')
def test_complete_lookup():
    style = Style.query.filter_by(vendor_style='21324-3202').first()
    if style:
        # Calculate pricing for regular and extended sizes
        regular_price = style.get_retail_price(1.0)  # Regular sizes
        extended_price = style.get_retail_price(1.15)  # Extended sizes (2XL-4XL)
        
        html = f"""
        <div style="max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
            <h1>Complete Uniform Pricing Lookup Test</h1>
            
            <div style="border: 2px solid #007bff; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h2>Style Information</h2>
                <p><strong>Vendor Style:</strong> {style.vendor_style}</p>
                <p><strong>Name:</strong> {style.style_name}</p>
                <p><strong>Gender:</strong> {style.gender}</p>
                <p><strong>Garment Type:</strong> {style.garment_type}</p>
                <p><strong>Size Range:</strong> {style.size_range}</p>
            </div>
            
            <div style="border: 2px solid #28a745; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h2>Cost Breakdown</h2>
                <p><strong>Fabric Cost:</strong> ${style.get_total_fabric_cost():.2f}</p>
                <p><strong>Notion Cost:</strong> ${style.get_total_notion_cost():.2f}</p>
                <p><strong>Labor Cost:</strong> ${style.get_total_labor_cost():.2f}</p>
                <p><strong>Label Cost:</strong> ${style.avg_label_cost:.2f}</p>
                <hr>
                <p><strong>Total Cost:</strong> ${style.get_total_cost():.2f}</p>
            </div>
            
            <div style="border: 2px solid #dc3545; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h2>Retail Pricing</h2>
                <p><strong>Regular Sizes (XS-XL):</strong> ${regular_price:.2f}</p>
                <p><strong>Extended Sizes (2XL-4XL +15%):</strong> ${extended_price:.2f}</p>
                <p><strong>Margin:</strong> {style.base_margin_percent:.0f}%</p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="/" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Main Search</a>
                <a href="/admin-panel" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Admin Panel</a>
            </div>
        </div>
        """
        return html
    else:
        return "<h1>No style found!</h1><a href='/create-complete-data'>Create Sample Data First</a>"

# ===== ADMIN ROUTES (Future expansion) =====


@app.route('/api/style/<int:style_id>/upload-image', methods=['POST'])
def upload_style_image(style_id):
    """Upload an image for a style"""
    # Check if style exists
    style = Style.query.get_or_404(style_id)
    
    # Check if file is in request
    if 'image' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['image']
    
    # Check if filename is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Validate and save file
    if file and allowed_file(file.filename):
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_filename = secure_filename(file.filename)
        filename = f"style_{style_id}_{timestamp}_{original_filename}"
        
        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Save file to disk
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Check if this should be the primary image (first image for this style)
        is_primary = StyleImage.query.filter_by(style_id=style_id).count() == 0
        
        # Create database record
        new_image = StyleImage(
            style_id=style_id,
            filename=filename,
            is_primary=is_primary,
            upload_date=datetime.utcnow()
        )
        
        db.session.add(new_image)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': new_image.id,
            'filename': filename,
            'url': f'/static/img/{filename}',
            'is_primary': is_primary
        }), 200
    
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
            print(f"Error deleting file: {e}")
            # Continue anyway to remove from database
    
    # Delete database record
    db.session.delete(img)
    db.session.commit()
    
    return jsonify({'success': True}), 200

@app.route('/migrate-db')
def migrate_db():
    """One-time migration to add new columns to styles table"""
    try:
        from sqlalchemy import text, inspect
        
        inspector = inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('styles')]
        
        migrations_run = []
        migrations_skipped = []
        
        # Add shipping_cost if it doesn't exist
        if 'shipping_cost' not in existing_columns:
            db.session.execute(text('ALTER TABLE styles ADD COLUMN shipping_cost FLOAT DEFAULT 0.00'))
            migrations_run.append('Added shipping_cost column')
        else:
            migrations_skipped.append('shipping_cost already exists')
        
        # Add suggested_price if it doesn't exist
        if 'suggested_price' not in existing_columns:
            db.session.execute(text('ALTER TABLE styles ADD COLUMN suggested_price FLOAT'))
            migrations_run.append('Added suggested_price column')
        else:
            migrations_skipped.append('suggested_price already exists')
        
        db.session.commit()
        
        html = f"""
        <div style="max-width: 800px; margin: 50px auto; padding: 20px; font-family: Arial;">
            <h1>Database Migration Complete</h1>
            
            <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>✓ Migrations Run Successfully:</h3>
                <ul>
        """
        
        if migrations_run:
            for migration in migrations_run:
                html += f"<li>{migration}</li>"
        else:
            html += "<li>No new migrations needed</li>"
        
        html += "</ul></div>"
        
        if migrations_skipped:
            html += """
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>⊙ Already Up to Date:</h3>
                <ul>
            """
            for skipped in migrations_skipped:
                html += f"<li>{skipped}</li>"
            html += "</ul></div>"
        
        html += """
            <div style="margin-top: 30px;">
                <a href="/admin-panel" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Admin Panel</a>
                <a href="/style/new" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-left: 10px;">Test Style Form</a>
            </div>
            
            <div style="margin-top: 30px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                <p><strong>Note:</strong> This migration only needs to be run once. You can delete the /migrate-db route after running it.</p>
            </div>
        </div>
        """
        
        return html
        
    except Exception as e:
        db.session.rollback()
        return f"""
        <div style="max-width: 800px; margin: 50px auto; padding: 20px; font-family: Arial;">
            <h1>Migration Error</h1>
            <div style="background: #f8d7da; padding: 15px; border-radius: 5px; color: #721c24;">
                <p><strong>Error:</strong> {str(e)}</p>
            </div>
            <p>This might mean:</p>
            <ul>
                <li>The columns already exist (which is fine!)</li>
                <li>There's a database connection issue</li>
                <li>The database user doesn't have ALTER TABLE permissions</li>
            </ul>
            <a href="/admin-panel" style="background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Back to Admin</a>
        </div>
        """
@app.route('/verify-db')
def verify_db():
    """Check database schema"""
    from sqlalchemy import inspect
    
    inspector = inspect(db.engine)
    columns = inspector.get_columns('styles')
    
    html = """
    <div style="max-width: 800px; margin: 50px auto; padding: 20px; font-family: Arial;">
        <h1>Database Schema Verification</h1>
        <h2>Styles Table Columns:</h2>
        <table border="1" cellpadding="10" style="border-collapse: collapse; width: 100%;">
            <tr>
                <th>Column Name</th>
                <th>Type</th>
                <th>Nullable</th>
                <th>Default</th>
            </tr>
    """
    
    for col in columns:
        html += f"""
            <tr>
                <td><strong>{col['name']}</strong></td>
                <td>{col['type']}</td>
                <td>{'Yes' if col['nullable'] else 'No'}</td>
                <td>{col['default'] or 'None'}</td>
            </tr>
        """
    
    html += """
        </table>
        <div style="margin-top: 20px;">
            <a href="/admin-panel" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Back to Admin</a>
        </div>
    </div>
    """
    
    return html

@app.route('/migrate-sublimation')
def migrate_sublimation():
    """Add sublimation column to style_fabrics"""
    try:
        from sqlalchemy import text, inspect
        
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('style_fabrics')]
        
        if 'is_sublimation' not in columns:
            db.session.execute(text('ALTER TABLE style_fabrics ADD COLUMN is_sublimation BOOLEAN DEFAULT 0'))
            db.session.commit()
            return "<h1>✓ Added is_sublimation column</h1><a href='/style/new'>Test Style Form</a>"
        else:
            return "<h1>Column already exists</h1><a href='/style/new'>Go to Style Form</a>"
    except Exception as e:
        db.session.rollback()
        return f"<h1>Error:</h1><p>{str(e)}</p>"
    
# SIZE RANGE ENDPOINTS
@app.route('/api/size-ranges', methods=['GET', 'POST'])
def handle_size_ranges():
    if request.method == 'GET':
        size_ranges = SizeRange.query.order_by(SizeRange.name).all()
        return jsonify([{
            'id': sr.id,
            'name': sr.name,
            'regular_sizes': sr.regular_sizes,
            'extended_sizes': sr.extended_sizes,
            'extended_markup_percent': float(sr.extended_markup_percent),
            'description': sr.description
        } for sr in size_ranges])
    
    elif request.method == 'POST':
        data = request.json
        size_range = SizeRange(
            name=data.get('name', '').strip().upper(),
            regular_sizes=data.get('regular_sizes', '').strip(),
            extended_sizes=data.get('extended_sizes', '').strip(),
            extended_markup_percent=float(data.get('extended_markup_percent', 15.0)),
            description=data.get('description', '').strip()
        )
        db.session.add(size_range)
        db.session.commit()
        return jsonify({'success': True, 'id': size_range.id})

@app.route('/api/size-ranges/<int:size_range_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_size_range(size_range_id):
    size_range = SizeRange.query.get_or_404(size_range_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': size_range.id,
            'name': size_range.name,
            'regular_sizes': size_range.regular_sizes,
            'extended_sizes': size_range.extended_sizes,
            'extended_markup_percent': float(size_range.extended_markup_percent),
            'description': size_range.description
        })
    
    elif request.method == 'PUT':
        data = request.json
        size_range.name = data.get('name', size_range.name).strip().upper()
        size_range.regular_sizes = data.get('regular_sizes', size_range.regular_sizes).strip()
        size_range.extended_sizes = data.get('extended_sizes', size_range.extended_sizes).strip()
        size_range.extended_markup_percent = float(data.get('extended_markup_percent', size_range.extended_markup_percent))
        size_range.description = data.get('description', size_range.description).strip()
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(size_range)
        db.session.commit()
        return jsonify({'success': True})
    

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
def handle_global_setting(setting_id):
    setting = GlobalSetting.query.get_or_404(setting_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': setting.id,
            'setting_key': setting.setting_key,
            'setting_value': float(setting.setting_value),
            'description': setting.description
        })
    
    elif request.method == 'PUT':
        data = request.json
        setting.setting_value = float(data.get('setting_value', setting.setting_value))
        setting.description = data.get('description', setting.description)
        db.session.commit()
        return jsonify({'success': True})
    

@app.route('/import-colors')
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
def handle_colors():
    if request.method == 'GET':
        colors = Color.query.order_by(Color.name).all()
        return jsonify([{'id': c.id, 'name': c.name} for c in colors])
    
    elif request.method == 'POST':
        data = request.json
        color_name = data.get('name', '').strip().upper()
        
        if not color_name:
            return jsonify({'error': 'Color name required'}), 400
        
        # Check if exists
        existing = Color.query.filter(func.lower(Color.name) == color_name.lower()).first()
        if existing:
            return jsonify({'success': True, 'id': existing.id, 'name': existing.name, 'existed': True})
        
        # Create new
        color = Color(name=color_name)
        db.session.add(color)
        db.session.commit()
        
        return jsonify({'success': True, 'id': color.id, 'name': color.name, 'existed': False})

@app.route('/api/colors/<int:color_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_color(color_id):
    color = Color.query.get_or_404(color_id)
    
    if request.method == 'GET':
        return jsonify({'id': color.id, 'name': color.name})
    
    elif request.method == 'PUT':
        data = request.json
        color.name = data.get('name', color.name).strip().upper()
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(color)
        db.session.commit()
        return jsonify({'success': True})

# Helper function to parse size range
def parse_size_range(size_range):
    """Parse size range string into individual sizes"""
    if not size_range:
        return []
    
    # Remove spaces and convert to uppercase
    size_range = size_range.upper().strip()
    
    # All possible sizes in order
    all_sizes = ['XXS', 'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL']
    
    # Parse range (e.g., "S-4XL" or "XS-XL")
    if '-' in size_range:
        parts = size_range.split('-')
        start_size = parts[0].strip()
        end_size = parts[1].strip()
        
        try:
            start_idx = all_sizes.index(start_size)
            end_idx = all_sizes.index(end_size)
            return all_sizes[start_idx:end_idx + 1]
        except ValueError:
            return []
    else:
        # Single size or comma-separated
        return [s.strip() for s in size_range.split(',')]

# Helper to determine if size is extended
def is_extended_size(size):
    """Check if size is extended (2XL and above)"""
    extended = ['2XL', '3XL', '4XL', '5XL']
    return size in extended

@app.route('/export-sap-format', methods=['POST'])
def export_sap_format():
    """Export selected styles in SAP B1 format"""
    try:
        import json
        style_ids = json.loads(request.form.get('style_ids', '[]'))
        
        if not style_ids:
            return "No styles selected", 400
        
        # Get selected styles
        styles = Style.query.filter(Style.id.in_(style_ids)).all()
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers (row 1 and 2 are identical)
        headers = ['Code', 'Name', 'U_COLOR', 'U_SIZE', 'U_VARIABLE', 
                   'U_PRICE', 'U_SHIP_COST', 'U_STYLE', 'U_CardCode', 'U_PROD_NAME']
        writer.writerow(headers)
        writer.writerow(headers)  # Duplicate header row
        
        # Generate rows for each style
        for style in styles:
            # Get base cost
            base_cost = style.get_total_cost()
            
            # Parse sizes
            sizes = parse_size_range(style.size_range)
            if not sizes:
                sizes = ['S', 'M', 'L', 'XL', '2XL', '3XL', '4XL']  # Default
            
            # Get colors (from style_colors relationship)
            colors = [sc.color.name.upper() for sc in style.colors] if style.colors else ['BLACK']
            
            # Get variables (from style_variables if exists)
            variables = []
            if hasattr(style, 'style_variables'):
                variables = [sv.variable.name.upper() for sv in style.style_variables]
            
            # Get vendor code from fabric vendor (first fabric's vendor)
            vendor_code = 'V100'  # Default
            if style.style_fabrics and style.style_fabrics[0].fabric.fabric_vendor:
                vendor_code = style.style_fabrics[0].fabric.fabric_vendor.vendor_code
            
            # Remove hyphens from vendor style
            u_style = style.vendor_style.replace('-', '')
            
            # Shipping cost
            shipping_cost = style.shipping_cost if hasattr(style, 'shipping_cost') else 0.00
            
            # Generate rows: Colors × Sizes × Variables
            for color in colors:
                for size in sizes:
                    # Calculate price based on size
                    if is_extended_size(size):
                        price = round(base_cost * 1.15, 2)  # Extended size markup
                    else:
                        price = round(base_cost, 2)  # Regular size
                    
                    if variables:
                        # If has variables, generate row for each variable
                        for variable in variables:
                            writer.writerow([
                                '',  # Code (blank)
                                '',  # Name (blank)
                                color,  # U_COLOR
                                size,  # U_SIZE
                                variable,  # U_VARIABLE
                                price,  # U_PRICE
                                shipping_cost,  # U_SHIP_COST
                                u_style,  # U_STYLE
                                vendor_code,  # U_CardCode
                                style.style_name  # U_PROD_NAME
                            ])
                        
                        # Also add row with blank variable
                        writer.writerow([
                            '', '', color, size, '', price, shipping_cost,
                            u_style, vendor_code, style.style_name
                        ])
                    else:
                        # No variables, just one row per color-size combination
                        writer.writerow([
                            '', '', color, size, '', price, shipping_cost,
                            u_style, vendor_code, style.style_name
                        ])
        
        # Prepare download
        output.seek(0)
        filename = f"SAP_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return f"Error exporting: {str(e)}", 500



# ========================================
# EXPORT ROUTE WITH DYNAMIC MARKUP
# ========================================

@app.route('/export-sap-single-style', methods=['POST'])
def export_sap_single_style():
    """Export a single style in SAP B1 format"""
    try:
        vendor_style = request.form.get('vendor_style')
        
        if not vendor_style:
            return "No style specified", 400
        
        # Get the style
        style = Style.query.filter_by(vendor_style=vendor_style).first()
        
        if not style:
            return "Style not found", 404
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Headers (row 1 and 2 are identical)
        headers = ['Code', 'Name', 'U_COLOR', 'U_SIZE', 'U_VARIABLE', 
                   'U_PRICE', 'U_SHIP_COST', 'U_STYLE', 'U_CardCode', 'U_PROD_NAME']
        writer.writerow(headers)
        writer.writerow(headers)  # Duplicate header row
        
        # Get base cost
        base_cost = style.get_total_cost()
        
        # ========================================
        # GET DYNAMIC MARKUP FROM SIZE RANGE
        # ========================================
        size_range = SizeRange.query.filter_by(name=style.size_range).first()
        extended_markup_percent = 15  # Default fallback
        
        if size_range:
            extended_markup_percent = size_range.extended_markup_percent
        
        # Convert percentage to multiplier (20% = 1.20, 15% = 1.15)
        extended_multiplier = 1 + (extended_markup_percent / 100)
        
        # Parse sizes
        sizes = parse_size_range(style.size_range)
        if not sizes:
            sizes = ['S', 'M', 'L', 'XL', '2XL', '3XL', '4XL']  # Default
        
        # Get colors (from style_colors relationship)
        colors = [sc.color.name.upper() for sc in style.colors] if style.colors else ['BLACK']
        
        # Get variables (from style_variables if exists)
        variables = []
        if hasattr(style, 'style_variables'):
            variables = [sv.variable.name.upper() for sv in style.style_variables]
        
        # Get vendor code from fabric vendor (first fabric's vendor)
        vendor_code = 'V100'  # Default
        if style.style_fabrics and style.style_fabrics[0].fabric.fabric_vendor:
            vendor_code = style.style_fabrics[0].fabric.fabric_vendor.vendor_code
        
        # Remove hyphens from vendor style
        u_style = style.vendor_style.replace('-', '')
        
        # Shipping cost
        shipping_cost = style.shipping_cost if hasattr(style, 'shipping_cost') else 0.00
        
        # Generate rows: Colors × Sizes × Variables
        for color in colors:
            for size in sizes:
                # ========================================
                # CALCULATE PRICE WITH DYNAMIC MARKUP
                # ========================================
                if is_extended_size(size, size_range):
                    price = round(base_cost * extended_multiplier, 2)  # Use dynamic markup
                else:
                    price = round(base_cost, 2)  # Regular size
                
                if variables:
                    # If has variables, generate row for each variable
                    for variable in variables:
                        writer.writerow([
                            '',  # Code (blank)
                            '',  # Name (blank)
                            color,  # U_COLOR
                            size,  # U_SIZE
                            variable,  # U_VARIABLE
                            price,  # U_PRICE
                            shipping_cost,  # U_SHIP_COST
                            u_style,  # U_STYLE
                            vendor_code,  # U_CardCode
                            style.style_name  # U_PROD_NAME
                        ])
                    
                    # Also add row with blank variable
                    writer.writerow([
                        '', '', color, size, '', price, shipping_cost,
                        u_style, vendor_code, style.style_name
                    ])
                else:
                    # No variables, just one row per color-size combination
                    writer.writerow([
                        '', '', color, size, '', price, shipping_cost,
                        u_style, vendor_code, style.style_name
                    ])
        
        # Prepare download
        output.seek(0)
        filename = f"SAP_{style.vendor_style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return f"Error exporting: {str(e)}", 500


# ========================================
# HELPER FUNCTION - UPDATE THIS TOO
# ========================================
def is_extended_size(size, size_range=None):
    """
    Check if a size is an extended size based on the size range.
    If size_range object is provided, check against its extended_sizes.
    Otherwise, use legacy logic.
    """
    if size_range and size_range.extended_sizes:
        # Parse extended sizes from the size range
        extended_sizes = [s.strip() for s in size_range.extended_sizes.split(',')]
        return size in extended_sizes
    
    # Legacy fallback: sizes like 2XL, 3XL, 4XL, 5XL are extended
    extended_patterns = ['2XL', '3XL', '4XL', '5XL', '6XL', 'XXL', 'XXXL', 'XXXXL']
    return size.upper() in extended_patterns
    

@app.route('/admin-panel')
def admin_panel():
    # Check if we have any styles
    styles_count = Style.query.count()
    fabrics_count = Fabric.query.count()
    notions_count = Notion.query.count()
    labor_ops_count = LaborOperation.query.count()
    
    html = f"""
    <div style="max-width: 1000px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
        <h1>J.A Uniforms - Admin Panel</h1>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0;">
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; text-align: center;">
                <h3>Styles</h3>
                <p style="font-size: 24px; color: #007bff;">{styles_count}</p>
            </div>
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; text-align: center;">
                <h3>Fabrics</h3>
                <p style="font-size: 24px; color: #28a745;">{fabrics_count}</p>
            </div>
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; text-align: center;">
                <h3>Notions</h3>
                <p style="font-size: 24px; color: #ffc107;">{notions_count}</p>
            </div>
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 20px; text-align: center;">
                <h3>Labor Operations</h3>
                <p style="font-size: 24px; color: #dc3545;">{labor_ops_count}</p>
            </div>
        </div>
        
        <div style="margin: 30px 0;">
            <h2>Quick Actions</h2>
            <a href="/view-all-styles" style="display: inline-block; background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">View All Styles</a>
            <a href="/master-costs" style="display: inline-block; background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">Master Costs</a>
            <a href="/import-excel" style="display: inline-block; background-color: #ffc107; color: black; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">Import Excel</a>
            <a href="/" style="display: inline-block; background-color: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">Back to Search</a>
        </div>
    </div>
    """
    return html

@app.route('/view-all-styles')
def view_all_styles():
    """View all styles with filters"""
    styles = Style.query.all()
    
    # Calculate stats
    total_styles = len(styles)
    total_value = sum([s.get_total_cost() for s in styles])
    avg_cost = total_value / total_styles if total_styles > 0 else 0
    
    return render_template('view_all_styles.html', 
                         styles=styles,
                         total_styles=total_styles,
                         total_value=total_value,
                         avg_cost=avg_cost)

@app.route('/api/style/delete/<int:style_id>', methods=['DELETE'])
def delete_style(style_id):
    """Delete a style and all its relationships"""
    try:
        style = Style.query.get_or_404(style_id)
        
        # Delete style images first (foreign key constraint)
        db.session.execute(
            db.text("DELETE FROM style_images WHERE style_id = :style_id"),
            {"style_id": style_id}
        )
        
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
        print(f"Delete error: {error_details}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/style/duplicate/<int:style_id>', methods=['POST'])
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
        print(f"Duplicate error: {error_details}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/styles/bulk-delete', methods=['POST'])
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
            db.session.execute(
                db.text("DELETE FROM style_images WHERE style_id = :style_id"),
                {"style_id": style_id}
            )
            
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
        print(f"Bulk delete error: {error_details}")
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

# ADD THESE ROUTES TO YOUR app.py
# These replace your existing /master-costs route and add the API endpoints

# ===== EDITABLE MASTER COSTS WITH VENDOR MANAGEMENT =====
@app.route('/migrate-phase1')
def migrate_phase1():
    """Add Phase 1 columns to styles table"""
    try:
        from sqlalchemy import text, inspect
        
        inspector = inspect(db.engine)
        existing_columns = [col['name'] for col in inspector.get_columns('styles')]
        
        migrations = []
        
        if 'last_modified_by' not in existing_columns:
            db.session.execute(text("ALTER TABLE styles ADD COLUMN last_modified_by VARCHAR(100) DEFAULT 'Admin'"))
            migrations.append('✅ Added last_modified_by')
        
        if 'is_active' not in existing_columns:
            db.session.execute(text('ALTER TABLE styles ADD COLUMN is_active BOOLEAN DEFAULT 1'))
            migrations.append('✅ Added is_active')
        
        if 'is_favorite' not in existing_columns:
            db.session.execute(text('ALTER TABLE styles ADD COLUMN is_favorite BOOLEAN DEFAULT 0'))
            migrations.append('✅ Added is_favorite')
        
        db.session.commit()
        
        html = '<h1>🎉 Phase 1 Migration Complete!</h1>'
        if migrations:
            html += '<ul style="font-size: 1.2rem;">'
            for m in migrations:
                html += f'<li>{m}</li>'
            html += '</ul>'
        else:
            html += '<p>All columns already exist!</p>'
        
        html += '<br><a href="/view-all-styles" style="padding: 10px 20px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px;">Go to Styles</a>'
        
        return html
        
    except Exception as e:
        db.session.rollback()
        import traceback
        return f"<h1>❌ Migration Error:</h1><pre>{traceback.format_exc()}</pre>"

@app.route('/api/style/<int:style_id>/favorite', methods=['POST'])
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
def master_costs_editable():
    """Display editable master cost lists that affect all styles"""
    fabrics = Fabric.query.order_by(Fabric.name).all()
    notions = Notion.query.order_by(Notion.name).all()
    labor_ops = LaborOperation.query.order_by(LaborOperation.name).all()
    cleaning_costs = CleaningCost.query.order_by(CleaningCost.garment_type).all()
    fabric_vendors = FabricVendor.query.order_by(FabricVendor.name).all()
    notion_vendors = NotionVendor.query.order_by(NotionVendor.name).all()
    
    # Build vendor options HTML
    fabric_vendor_options = ''.join([f'<option value="{v.id}">{v.name}</option>' for v in fabric_vendors])
    notion_vendor_options = ''.join([f'<option value="{v.id}">{v.name}</option>' for v in notion_vendors])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Master Cost Lists</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; padding: 30px; background-color: #f5f5f5; }}
            .container {{ max-width: 1400px; margin: 0 auto; background-color: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            h1 {{ font-size: 32px; margin-bottom: 10px; color: #333; }}
            .subtitle {{ color: #666; margin-bottom: 30px; font-size: 14px; }}
            h2 {{ font-size: 24px; margin-top: 40px; margin-bottom: 15px; color: #333; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            thead {{ background-color: #e8f4f8; }}
            .notions thead {{ background-color: #f3e8f8; }}
            .labor thead {{ background-color: #fef3e8; }}
            .cleaning thead {{ background-color: #e8f8f0; }}
            .vendors thead {{ background-color: #ffe8e8; }}
            th {{ text-align: left; padding: 12px; font-weight: 600; color: #333; border: 1px solid #ddd; }}
            td {{ padding: 12px; border: 1px solid #ddd; }}
            tbody tr:hover {{ background-color: #f9f9f9; }}
            .btn {{ padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; margin-right: 5px; transition: all 0.2s; }}
            .btn-primary {{ background-color: #007bff; color: white; }}
            .btn-primary:hover {{ background-color: #0056b3; }}
            .btn-success {{ background-color: #28a745; color: white; }}
            .btn-success:hover {{ background-color: #218838; }}
            .btn-danger {{ background-color: #dc3545; color: white; }}
            .btn-danger:hover {{ background-color: #c82333; }}
            .btn-secondary {{ background-color: #6c757d; color: white; text-decoration: none; display: inline-block; }}
            .btn-secondary:hover {{ background-color: #545b62; }}
            .btn-small {{ padding: 4px 8px; font-size: 12px; }}
            .actions {{ display: flex; gap: 5px; }}
            .add-row-btn {{ margin: 10px 0 20px 0; }}
            input, select {{ width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }}
            input:focus, select:focus {{ outline: none; border-color: #007bff; box-shadow: 0 0 0 2px rgba(0,123,255,0.1); }}
            .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); z-index: 1000; }}
            .modal-content {{ background-color: white; margin: 100px auto; padding: 30px; width: 500px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .modal-header {{ margin-bottom: 20px; }}
            .modal-header h3 {{ margin: 0; color: #333; }}
            .form-group {{ margin-bottom: 15px; }}
            .form-group label {{ display: block; margin-bottom: 5px; font-weight: 600; color: #555; }}
            .modal-footer {{ margin-top: 20px; text-align: right; }}
            .notification {{ position: fixed; top: 20px; right: 20px; padding: 15px 20px; border-radius: 4px; color: white; display: none; z-index: 2000; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
            .notification.success {{ background-color: #28a745; }}
            .notification.error {{ background-color: #dc3545; }}
            .back-button {{ margin-top: 40px; }}
            .warning-box {{ background-color: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .vendor-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 40px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Master Cost Lists</h1>
            <p class="subtitle">These costs apply to ALL styles. When you update a price here, it automatically updates all styles that use this item.</p>
            
            <div class="warning-box">
                <strong>⚠️ Important:</strong> Changes to master costs will immediately affect the pricing of all existing uniform styles in your system.
            </div>
            
            <!-- VENDORS SECTION -->
            <h2>Vendors</h2>
            <div class="vendor-grid">
                <!-- FABRIC VENDORS -->
                <div id="fabric-vendors">
                    <h3>Fabric Vendors</h3>
                    <button class="btn btn-success add-row-btn" onclick="openModal('fabric_vendor')">+ Add Fabric Vendor</button>
                    <table class="vendors">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Code</th>
                                <th style="width: 120px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    for vendor in fabric_vendors:
        html += f"""
                            <tr>
                                <td>{vendor.name}</td>
                                <td>{vendor.vendor_code or ''}</td>
                                <td>
                                    <div class="actions">
                                        <button class="btn btn-primary btn-small" onclick="editFabricVendor({vendor.id})">Edit</button>
                                        <button class="btn btn-danger btn-small" onclick="deleteFabricVendor({vendor.id})">Delete</button>
                                    </div>
                                </td>
                            </tr>
        """
    
    html += """
                        </tbody>
                    </table>
                </div>
                
                <!-- NOTION VENDORS -->
                <div id="notion-vendors">
                    <h3>Notion Vendors</h3>
                    <button class="btn btn-success add-row-btn" onclick="openModal('notion_vendor')">+ Add Notion Vendor</button>
                    <table class="vendors">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Code</th>
                                <th style="width: 120px;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
    """
    
    for vendor in notion_vendors:
        html += f"""
                            <tr>
                                <td>{vendor.name}</td>
                                <td>{vendor.vendor_code or ''}</td>
                                <td>
                                    <div class="actions">
                                        <button class="btn btn-primary btn-small" onclick="editNotionVendor({vendor.id})">Edit</button>
                                        <button class="btn btn-danger btn-small" onclick="deleteNotionVendor({vendor.id})">Delete</button>
                                    </div>
                                </td>
                            </tr>
        """

    html += """
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- FABRICS -->
            <h2>Fabrics</h2>
            <div style="margin-bottom: 15px;">
                <input type="text" id="fabricSearch" placeholder="🔍 Search fabrics..." style="width: 300px; padding: 8px; margin-bottom: 10px;">
                <span id="fabricCount" style="margin-left: 15px; color: #666;"></span>
            </div>
            <button class="btn btn-success add-row-btn" onclick="openModal('fabric')">+ Add Fabric</button>
            <table class="fabrics">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Code</th>
                        <th>Cost/Yard</th>
                        <th>Vendor</th>
                        <th style="width: 150px;">Actions</th>
                    </tr>
                </thead>
                <tbody id="fabricsTable">
    """
    
    for fabric in fabrics:
        vendor_name = fabric.fabric_vendor.name if fabric.fabric_vendor else 'N/A'
        html += f"""
                    <tr data-id="{fabric.id}" class="fabric-row">
                        <td>{fabric.name}</td>
                        <td>{fabric.fabric_code or ''}</td>
                        <td>${fabric.cost_per_yard:.2f}</td>
                        <td>{vendor_name}</td>
                        <td>
                            <div class="actions">
                                <button class="btn btn-primary btn-small" onclick="editFabric({fabric.id})">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deleteFabric({fabric.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <!-- NOTIONS -->
        <h2>Notions</h2>
        <div style="margin-bottom: 15px;">
            <input type="text" id="notionSearch" placeholder="🔍 Search notions..." style="width: 300px; padding: 8px; margin-bottom: 10px;">
            <span id="notionCount" style="margin-left: 15px; color: #666;"></span>
        </div>
        <button class="btn btn-success add-row-btn" onclick="openModal('notion')">+ Add Notion</button>
        <table class="notions">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Cost/Unit</th>
                    <th>Unit Type</th>
                    <th>Vendor</th>
                    <th style="width: 150px;">Actions</th>
                </tr>
            </thead>
            <tbody id="notionsTable">
    """
    
    for notion in notions:
        vendor_name = notion.notion_vendor.name if notion.notion_vendor else 'N/A'
        html += f"""
                    <tr data-id="{notion.id}">
                        <td>{notion.name}</td>
                        <td>${notion.cost_per_unit:.4f}</td>
                        <td>{notion.unit_type}</td>
                        <td>{vendor_name}</td>
                        <td>
                            <div class="actions">
                                <button class="btn btn-primary btn-small" onclick="editNotion({notion.id})">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deleteNotion({notion.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <!-- LABOR OPERATIONS -->
        <h2>Labor Operations</h2>
        <div style="margin-bottom: 15px;">
            <input type="text" id="laborSearch" placeholder="🔍 Search labor operations..." style="width: 300px; padding: 8px; margin-bottom: 10px;">
            <span id="laborCount" style="margin-left: 15px; color: #666;"></span>
        </div>
        <button class="btn btn-success add-row-btn" onclick="openModal('labor')">+ Add Labor Operation</button>
        <table class="labor">
            <thead>
                <tr>
                    <th>Operation</th>
                    <th>Cost Type</th>
                    <th>Rate</th>
                    <th style="width: 150px;">Actions</th>
                </tr>
            </thead>
            <tbody id="laborTable">
    """
    
    for labor in labor_ops:
        if labor.cost_type == 'flat_rate':
            rate_display = f"${labor.fixed_cost:.2f} flat"
        elif labor.cost_type == 'hourly':
            rate_display = f"${labor.cost_per_hour:.2f}/hour"
        elif labor.cost_type == 'per_piece':
            rate_display = f"${labor.cost_per_piece:.2f}/piece"
        else:
            rate_display = "N/A"
            
        html += f"""
                    <tr data-id="{labor.id}" class="labor-row">
                        <td>{labor.name}</td>
                        <td>{labor.cost_type.replace('_', ' ').title()}</td>
                        <td>{rate_display}</td>
                        <td>
                            <div class="actions">
                                <button class="btn btn-primary btn-small" onclick="editLabor({labor.id})">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deleteLabor({labor.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <!-- CLEANING COSTS -->
        <h2>Cleaning & Ironing Costs</h2>
        <p style="color: #666; margin-bottom: 5px;">Based on $19.32/hour = $0.32/minute</p>
        <div style="margin-bottom: 15px;">
            <input type="text" id="cleaningSearch" placeholder="🔍 Search cleaning costs..." style="width: 300px; padding: 8px; margin-bottom: 10px;">
            <span id="cleaningCount" style="margin-left: 15px; color: #666;"></span>
        </div>
        <button class="btn btn-success add-row-btn" onclick="openModal('cleaning')">+ Add Cleaning Cost</button>
        <table class="cleaning">
            <thead>
                <tr>
                    <th>Garment Type</th>
                    <th>Minutes</th>
                    <th>Fixed Cost</th>
                    <th style="width: 150px;">Actions</th>
                </tr>
            </thead>
            <tbody id="cleaningTable">
    """
    
    for cleaning in cleaning_costs:
        html += f"""
                    <tr data-id="{cleaning.id}">
                        <td>{cleaning.garment_type}</td>
                        <td>{cleaning.avg_minutes}</td>
                        <td>${cleaning.fixed_cost:.2f}</td>
                        <td>
                            <div class="actions">
                                <button class="btn btn-primary btn-small" onclick="editCleaning({cleaning.id})">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deleteCleaning({cleaning.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
        """
    html += """
            </tbody>
        </table>
    """
    # Add to master_costs_editable() function, after notion vendors section:
    html += """
            <!-- COLORS SECTION -->
            <h2 id="colors-section">Colors</h2>
            <div style="margin-bottom: 15px;">
                <input type="text" id="colorSearch" placeholder="🔍 Search colors..." style="width: 300px; padding: 8px; margin-bottom: 10px;">
                <span id="colorCount" style="margin-left: 15px; color: #666;"></span>
            </div>
            <button class="btn btn-success add-row-btn" onclick="openModal('color')">+ Add Color</button>
            <div style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px;">
                <table class="vendors" style="margin-bottom: 0;">
                    <thead style="position: sticky; top: 0; background: #ffe8e8; z-index: 10;">
                        <tr>
                            <th>Color Name</th>
                            <th style="width: 120px;">Actions</th>
                        </tr>
                    </thead>
                    <tbody id="colorTableBody">
    """

    colors = Color.query.order_by(Color.name).all()
    for color in colors:
        html += f"""
                    <tr class="color-row">
                        <td>{color.name}</td>
                        <td>
                            <div class="actions">
                                <button class="btn btn-primary btn-small" onclick="editColor({color.id})">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deleteColor({color.id})">Delete</button>
                                </div>
                            </td>
                    </tr>
    """
    html += f"""
                </tbody>
            </table>
            </div>
            
            <!-- VARIABLES SECTION - ADD THIS ENTIRE BLOCK HERE -->
            <h2 id="variables-section">Variables</h2>
            <div style="margin-bottom: 15px;">
                <input type="text" id="variableSearch" placeholder="Search variables..." style="width: 300px; padding: 8px; margin-bottom: 10px;">
            </div>
            <button class="btn btn-success add-row-btn" onclick="openModal('variable')">+ Add Variable</button>
            <table class="vendors">
                <thead>
                    <tr>
                        <th>Variable Name</th>
                        <th style="width: 120px;">Actions</th>
                    </tr>
                </thead>
                <tbody id="variableTableBody">
    """

    variables = Variable.query.order_by(Variable.name).all()
    for variable in variables:
        html += f"""
                    <tr class="variable-row">
                        <td>{variable.name}</td>
                        <td>
                            <div class="actions">
                                <button class="btn btn-primary btn-small" onclick="editVariable({variable.id})">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deleteVariable({variable.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
        """
    
    html += f"""
                </tbody>
            </table>  

            <!-- SIZE RANGES SECTION - INSERT HERE -->
            <h2 id="size-ranges-section">Size Ranges</h2>
            <div style="margin-bottom: 15px;">
                <input type="text" id="sizeRangeSearch" placeholder="Search size ranges..." style="width: 300px; padding: 8px; margin-bottom: 10px;">
            </div>
            <button class="btn btn-success add-row-btn" onclick="openModal('size_range')">+ Add Size Range</button>
            <table class="vendors">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Regular Sizes</th>
                        <th>Extended Sizes</th>
                        <th>Markup %</th>
                        <th>Description</th>
                        <th style="width: 120px;">Actions</th>
                    </tr>
                </thead>
                <tbody id="sizeRangeTableBody">
    """

    size_ranges = SizeRange.query.order_by(SizeRange.name).all()
    for sr in size_ranges:
        html += f"""
                    <tr class="size-range-row">
                        <td><strong>{sr.name}</strong></td>
                        <td>{sr.regular_sizes}</td>
                        <td>{sr.extended_sizes or 'N/A'}</td>
                        <td>{sr.extended_markup_percent}%</td>
                        <td>{sr.description or ''}</td>
                        <td>
                            <div class="actions">
                                <button class="btn btn-primary btn-small" onclick="editSizeRange({sr.id})">Edit</button>
                                <button class="btn btn-danger btn-small" onclick="deleteSizeRange({sr.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
        """
    
    html += f"""
                </tbody>
            </table>

            <!-- GLOBAL SETTINGS SECTION - ADD HERE -->
            <h2 id="global-settings-section">Global Settings</h2>
            <p style="color: #666; margin-bottom: 15px;">Default values applied to all new styles</p>
            <table class="vendors">
                <thead>
                    <tr>
                        <th>Setting</th>
                        <th>Value</th>
                        <th>Description</th>
                        <th style="width: 120px;">Actions</th>
                    </tr>
                </thead>
                <tbody>
    """

    global_settings = GlobalSetting.query.all()
    for setting in global_settings:
        display_name = setting.setting_key.replace('_', ' ').title()
        html += f"""
                    <tr>
                        <td><strong>{display_name}</strong></td>
                        <td>${setting.setting_value:.2f}</td>
                        <td>{setting.description or ''}</td>
                        <td>
                            <div class="actions">
                                <button class="btn btn-primary btn-small" onclick="editGlobalSetting({setting.id})">Edit</button>
                            </div>
                        </td>
                    </tr>
        """
    
    html += f"""
                </tbody>
            </table>
            <div class="back-button">
                <a href="/admin-panel" class="btn btn-secondary">Back to Admin</a>
            </div>
        </div>
        
        <!-- Modal for Add/Edit -->
        <div id="modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3 id="modalTitle">Add Item</h3>
                </div>
                <div id="modalBody"></div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="saveItem()">Save</button>
                </div>
            </div>
        </div>
        
        <!-- Notification -->
        <div id="notification" class="notification"></div>
        
        <script>
            let currentEditType = '';
            let currentEditId = null;
            const fabricVendorOptions = '{fabric_vendor_options}';
            const notionVendorOptions = '{notion_vendor_options}';
            
            // Standard garment types for cleaning costs
            
            
            function openModal(type, id = null) {{
                currentEditType = type;
                currentEditId = id;
                
                const modal = document.getElementById('modal');
                const modalTitle = document.getElementById('modalTitle');
                const modalBody = document.getElementById('modalBody');
                
                modalTitle.textContent = id ? 'Edit ' + capitalize(type.replace('_', ' ')) : 'Add ' + capitalize(type.replace('_', ' '));
                
                let formHtml = '';
                
                if (type === 'fabric_vendor') {{
                    formHtml = `
                        <div class="form-group">
                            <label>Vendor Name *</label>
                            <input type="text" id="name" required placeholder="e.g., CARR TEXTILES">
                        </div>
                        <div class="form-group">
                            <label>Vendor Code *</label>
                            <input type="text" id="vendor_code" required placeholder="e.g., V100">
                        </div>
                    `;
                }} else if (type === 'notion_vendor') {{
                    formHtml = `
                        <div class="form-group">
                            <label>Vendor Name *</label>
                            <input type="text" id="name" required placeholder="e.g., WAWAK">
                        </div>
                        <div class="form-group">
                            <label>Vendor Code *</label>
                            <input type="text" id="vendor_code" required placeholder="e.g., N100">
                        </div>
                    `;
                }} else if (type === 'fabric') {{
                    formHtml = `
                        <div class="form-group">
                            <label>Fabric Name *</label>
                            <input type="text" id="name" required placeholder="e.g., XANADU">
                        </div>
                        <div class="form-group">
                            <label>Fabric Code</label>
                            <input type="text" id="fabric_code" placeholder="e.g., 3202">
                        </div>
                        <div class="form-group">
                            <label>Cost per Yard *</label>
                            <input type="number" id="cost_per_yard" step="0.01" required placeholder="e.g., 6.00">
                        </div>
                        <div class="form-group">
                            <label>Vendor *</label>
                            <select id="fabric_vendor_id" required>
                                <option value="">Select Vendor</option>
                                ${{fabricVendorOptions}}
                            </select>
                        </div>
                    `;
                }} else if (type === 'notion') {{
                    formHtml = `
                        <div class="form-group">
                            <label>Notion Name *</label>
                            <input type="text" id="name" required placeholder="e.g., 18L SPORT BUTTON">
                        </div>
                        <div class="form-group">
                            <label>Cost per Unit *</label>
                            <input type="number" id="cost_per_unit" step="0.0001" required placeholder="e.g., 0.04">
                        </div>
                        <div class="form-group">
                            <label>Unit Type *</label>
                            <select id="unit_type" required>
                                <option value="each">each</option>
                                <option value="yard">yard</option>
                                <option value="set">set</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Vendor *</label>
                            <select id="notion_vendor_id" required>
                                <option value="">Select Vendor</option>
                                ${{notionVendorOptions}}
                            </select>
                        </div>
                    `;
                }} else if (type === 'labor') {{
                    formHtml = `
                        <div class="form-group">
                            <label>Operation Name *</label>
                            <input type="text" id="name" required placeholder="e.g., Sewing">
                        </div>
                        <div class="form-group">
                            <label>Cost Type *</label>
                            <select id="cost_type" required onchange="updateLaborFields()">
                                <option value="flat_rate">Flat Rate</option>
                                <option value="hourly">Hourly</option>
                                <option value="per_piece">Per Piece</option>
                            </select>
                        </div>
                        <div class="form-group" id="flat_rate_group">
                            <label>Fixed Cost</label>
                            <input type="number" id="fixed_cost" step="0.01" placeholder="e.g., 1.50">
                        </div>
                        <div class="form-group" id="hourly_group" style="display:none;">
                            <label>Cost per Hour</label>
                            <input type="number" id="cost_per_hour" step="0.01" placeholder="e.g., 19.32">
                        </div>
                        <div class="form-group" id="per_piece_group" style="display:none;">
                            <label>Cost per Piece</label>
                            <input type="number" id="cost_per_piece" step="0.01" placeholder="e.g., 0.15">
                        </div>
                    `;

                }} else if (type === 'cleaning') {{
                    formHtml = `
                        <div class="form-group">
                            <label>Garment Type *</label>
                            <input type="text" id="garment_type" required placeholder="e.g., SS TOP/SS DRESS" style="text-transform: uppercase;">
                            <small style="color: #666;">Enter any garment type description</small>
                        </div>
                        <div class="form-group">
                            <label>Average Minutes *</label>
                            <input type="number" id="avg_minutes" required placeholder="e.g., 5">
                            <small style="color: #666;">Based on $0.32/minute</small>
                        </div>
                        <div class="form-group">
                            <label>Fixed Cost *</label>
                            <input type="number" id="fixed_cost" step="0.01" required placeholder="e.g., 1.60">
                            <small style="color: #666;">Will be calculated: Minutes × $0.32</small>
                        </div>
                    `;
                }} else if (type === 'color') {{
                    formHtml = '<div class="form-group"><label>Color Name *</label><input type="text" id="name" required placeholder="e.g., ADMIRAL BLUE" style="text-transform: uppercase;"></div>';
                }} else if (type === 'variable') {{
                    formHtml = '<div class="form-group"><label>Variable Name *</label><input type="text" id="name" required placeholder="e.g., TALL" style="text-transform: uppercase;"></div>';
                }} else if (type === 'size_range') {{
                    formHtml = `
                        <div class="form-group">
                            <label>Size Range Name * (e.g., XS-6XL, 00-30)</label>
                            <input type="text" id="name" required placeholder="e.g., XS-6XL" style="text-transform: uppercase;">
                        </div>
                        <div class="form-group">
                            <label>Regular Sizes * (e.g., XS-XL, 00-18)</label>
                            <input type="text" id="regular_sizes" required placeholder="e.g., XS-XL">
                        </div>
                        <div class="form-group">
                            <label>Extended Sizes (e.g., 2XL-6XL, 20-30)</label>
                            <input type="text" id="extended_sizes" placeholder="e.g., 2XL-6XL">
                        </div>
                        <div class="form-group">
                            <label>Extended Markup % *</label>
                            <input type="number" id="extended_markup_percent" required value="15" step="0.1" min="0" max="100">
                        </div>
                        <div class="form-group">
                            <label>Description (optional)</label>
                            <textarea id="description" rows="2" placeholder="Notes about this size range"></textarea>
                        </div>
                    `;
                }} else if (type === 'global_setting') {{
                    formHtml = `
                        <div class="form-group">
                            <label>Setting Value *</label>
                            <input type="number" id="setting_value" step="0.01" required placeholder="e.g., 0.20">
                        </div>
                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="description" rows="2" placeholder="Description of this setting"></textarea>
                        </div>
                    `;
                }}

                modalBody.innerHTML = formHtml;
                
                // If editing, load current values
                if (id) {{
                    const endpoint = type.replace('_', '-');
                    fetch(`/api/${{endpoint}}s/${{id}}`)
                        .then(response => response.json())
                        .then(data => {{
                            Object.keys(data).forEach(key => {{
                                const input = document.getElementById(key);
                                if (input) {{
                                    input.value = data[key] || '';
                                }}
                            }});
                            if (type === 'labor') {{
                                updateLaborFields();
                            }}
                        }});
                }}
                
                // Auto-calculate cleaning cost based on minutes
                if (type === 'cleaning') {{
                    const minutesInput = document.getElementById('avg_minutes');
                    const costInput = document.getElementById('fixed_cost');
                    minutesInput.addEventListener('input', function() {{
                        if (this.value) {{
                            costInput.value = (parseFloat(this.value) * 0.32).toFixed(2);
                        }}
                    }});
                }}
                
                modal.style.display = 'block';
            }}
            
            function updateLaborFields() {{
                const costType = document.getElementById('cost_type').value;
                document.getElementById('flat_rate_group').style.display = costType === 'flat_rate' ? 'block' : 'none';
                document.getElementById('hourly_group').style.display = costType === 'hourly' ? 'block' : 'none';
                document.getElementById('per_piece_group').style.display = costType === 'per_piece' ? 'block' : 'none';
            }}
            
            function closeModal() {{
                document.getElementById('modal').style.display = 'none';
                currentEditType = '';
                currentEditId = null;
            }}
            
            function saveItem() {{
                const data = {{}};
                const inputs = document.querySelectorAll('#modalBody input, #modalBody select, #modalBody textarea');

                
                inputs.forEach(input => {{
                    if (input.value) {{
                        data[input.id] = input.value;
                    }}
                }});
                
                const endpoint = currentEditType.replace('_', '-');
                const url = currentEditId 
                    ? `/api/${{endpoint}}s/${{currentEditId}}` 
                    : `/api/${{endpoint}}s`;
                
                const method = currentEditId ? 'PUT' : 'POST';
                
                fetch(url, {{
                    method: method,
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify(data)
                }})
                .then(response => response.json())
                .then(() => {{
                    showNotification('Saved successfully!', 'success');
                    closeModal();
                    setTimeout(() => location.reload(), 1000);
                }})
                .catch(error => {{
                    showNotification('Error saving: ' + error, 'error');
                }});
            }}
            
            // Fabric Vendor functions
            function editFabricVendor(id) {{ openModal('fabric_vendor', id); }}
            function deleteFabricVendor(id) {{
                if (confirm('Delete this fabric vendor? Fabrics using this vendor will need to be reassigned.')) {{
                    deleteItem('fabric-vendor', id);
                }}
            }}
            
            // Notion Vendor functions
            function editNotionVendor(id) {{ openModal('notion_vendor', id); }}
            function deleteNotionVendor(id) {{
                if (confirm('Delete this notion vendor? Notions using this vendor will need to be reassigned.')) {{
                    deleteItem('notion-vendor', id);
                }}
            }}
            
            // Fabric functions
            function editFabric(id) {{ openModal('fabric', id); }}
            function deleteFabric(id) {{
                if (confirm('Delete this fabric? This may affect existing styles.')) {{
                    deleteItem('fabric', id);
                }}
            }}
            
            // Notion functions
            function editNotion(id) {{ openModal('notion', id); }}
            function deleteNotion(id) {{
                if (confirm('Delete this notion? This may affect existing styles.')) {{
                    deleteItem('notion', id);
                }}
            }}
            
            // Labor functions
            function editLabor(id) {{ openModal('labor', id); }}
            function deleteLabor(id) {{
                if (confirm('Delete this labor operation? This may affect existing styles.')) {{
                    deleteItem('labor', id);
                }}
            }}
            
            // Cleaning functions
            function editCleaning(id) {{ openModal('cleaning', id); }}
            function deleteCleaning(id) {{
                if (confirm('Delete this cleaning cost? This may affect existing styles')) {{
                    deleteItem('cleaning', id);
                }}
            }}

            // Color functions - ADD THESE LINES
            function editColor(id) {{ openModal('color', id); }}
            function deleteColor(id) {{
                if (confirm('Delete this color? This may affect existing styles.')) {{
                    deleteItem('color', id);
                }}
            }}

            // Universal filter function for all tables
            function setupTableFilter(searchId, rowClass, countId) {{
                const searchInput = document.getElementById(searchId);
                if (!searchInput) return;
                
                const updateCount = () => {{
                    const rows = document.querySelectorAll('.' + rowClass);
                    const visible = Array.from(rows).filter(r => r.style.display !== 'none').length;
                    const countEl = document.getElementById(countId);
                    if (countEl) countEl.textContent = 'Showing ' + visible + ' of ' + rows.length;
                }};
                
                searchInput.addEventListener('input', function() {{
                    const searchTerm = this.value.toLowerCase();
                    const rows = document.querySelectorAll('.' + rowClass);
                    
                    rows.forEach(row => {{
                        const text = row.textContent.toLowerCase();
                        row.style.display = text.includes(searchTerm) ? '' : 'none';
                    }});
                    
                    updateCount();
                }});
                
                updateCount();
            }}
            
            // Initialize all filters
            setupTableFilter('fabricSearch', 'fabric-row', 'fabricCount');
            setupTableFilter('notionSearch', 'notion-row', 'notionCount');
            setupTableFilter('laborSearch', 'labor-row', 'laborCount');
            setupTableFilter('cleaningSearch', 'cleaning-row', 'cleaningCount');
            setupTableFilter('colorSearch', 'color-row', 'colorCount');
            setupTableFilter('variableSearch', 'variable-row', 'variableCount');
            setupTableFilter('sizeRangeSearch', 'size-range-row', 'sizeRangeCount');

            // Variable functions - ADD THIS ENTIRE BLOCK HERE
            function editVariable(id) {{ openModal('variable', id); }}
            function deleteVariable(id) {{
                if (confirm('Delete this variable? This may affect existing styles.')) {{
                    deleteItem('variable', id);
                }}
            }}
            
            // Variable search filter
            document.getElementById('variableSearch')?.addEventListener('input', function() {{
                const searchTerm = this.value.toLowerCase();
                const rows = document.querySelectorAll('.variable-row');
                
                rows.forEach(row => {{
                    const variableName = row.cells[0].textContent.toLowerCase();
                    row.style.display = variableName.includes(searchTerm) ? '' : 'none';
                }});
            }});

            // Size Range functions - ADD THIS ENTIRE BLOCK
            function editSizeRange(id) {{ openModal('size_range', id); }}
            function deleteSizeRange(id) {{
                if (confirm('Delete this size range? This may affect existing styles.')) {{
                    deleteItem('size_range', id);
                }}
            }}
            // Global Setting function - ADD THIS LINE
            function editGlobalSetting(id) {{ openModal('global_setting', id); }}

            // Size Range search filter
            document.getElementById('sizeRangeSearch')?.addEventListener('input', function() {{
                const searchTerm = this.value.toLowerCase();
                const rows = document.querySelectorAll('.size-range-row');
                
                rows.forEach(row => {{
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                }});
            }});

            function deleteItem(type, id) {{
                // Convert underscore to hyphen for API endpoint
                const endpoint = type.replace('_', '-');
                
                fetch(`/api/${{endpoint}}s/${{id}}`, {{
                    method: 'DELETE'
                }})
                .then(response => response.json())
                .then(() => {{
                    showNotification('Deleted successfully!', 'success');
                    setTimeout(() => location.reload(), 500);
                }})
                .catch(error => {{
                    showNotification('Error deleting: ' + error, 'error');
                }});
            }}
            
            function showNotification(message, type) {{
                const notification = document.getElementById('notification');
                notification.textContent = message;
                notification.className = 'notification ' + type;
                notification.style.display = 'block';
                
                setTimeout(() => {{
                    notification.style.display = 'none';
                }}, 3000);
            }}
            
            function capitalize(str) {{
                return str.charAt(0).toUpperCase() + str.slice(1);
            }}
            
            window.onclick = function(event) {{
                const modal = document.getElementById('modal');
                if (event.target == modal) {{
                    closeModal();
                }}
            }}
        </script>
    </body>
    </html>
    """
    
    return html


# ===== API ENDPOINTS FOR MASTER COSTS =====

# FABRIC VENDOR ENDPOINTS
@app.route('/api/fabric-vendors/<int:vendor_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_fabric_vendor(vendor_id):
    vendor = FabricVendor.query.get_or_404(vendor_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': vendor.id,
            'name': vendor.name,
            'vendor_code': vendor.vendor_code
        })
    
    elif request.method == 'PUT':
        data = request.json
        vendor.name = data.get('name', vendor.name)
        vendor.vendor_code = data.get('vendor_code', vendor.vendor_code)
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(vendor)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/fabric-vendors', methods=['POST'])
def create_fabric_vendor():
    data = request.json
    vendor = FabricVendor(
        name=data['name'],
        vendor_code=data.get('vendor_code')
    )
    db.session.add(vendor)
    db.session.commit()
    return jsonify({'success': True, 'id': vendor.id})


# NOTION VENDOR ENDPOINTS
@app.route('/api/notion-vendors/<int:vendor_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_notion_vendor(vendor_id):
    vendor = NotionVendor.query.get_or_404(vendor_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': vendor.id,
            'name': vendor.name,
            'vendor_code': vendor.vendor_code
        })
    
    elif request.method == 'PUT':
        data = request.json
        vendor.name = data.get('name', vendor.name)
        vendor.vendor_code = data.get('vendor_code', vendor.vendor_code)
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(vendor)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/notion-vendors', methods=['POST'])
def create_notion_vendor():
    data = request.json
    vendor = NotionVendor(
        name=data['name'],
        vendor_code=data.get('vendor_code')
    )
    db.session.add(vendor)
    db.session.commit()
    return jsonify({'success': True, 'id': vendor.id})


# FABRIC ENDPOINTS
@app.route('/api/fabrics/<int:fabric_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_fabric(fabric_id):
    fabric = Fabric.query.get_or_404(fabric_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': fabric.id,
            'name': fabric.name,
            'fabric_code': fabric.fabric_code,
            'cost_per_yard': fabric.cost_per_yard,
            'fabric_vendor_id': fabric.fabric_vendor_id
        })
    
    elif request.method == 'PUT':
        data = request.json
        fabric.name = data.get('name', fabric.name)
        fabric.fabric_code = data.get('fabric_code', fabric.fabric_code)
        fabric.cost_per_yard = float(data.get('cost_per_yard', fabric.cost_per_yard))
        fabric.fabric_vendor_id = int(data.get('fabric_vendor_id', fabric.fabric_vendor_id))
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(fabric)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/fabrics', methods=['POST'])
def create_fabric():
    data = request.json
    fabric = Fabric(
        name=data['name'],
        fabric_code=data.get('fabric_code'),
        cost_per_yard=float(data['cost_per_yard']),
        fabric_vendor_id=int(data['fabric_vendor_id'])
    )
    db.session.add(fabric)
    db.session.commit()
    return jsonify({'success': True, 'id': fabric.id})


# NOTION ENDPOINTS
@app.route('/api/notions/<int:notion_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_notion(notion_id):
    notion = Notion.query.get_or_404(notion_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': notion.id,
            'name': notion.name,
            'cost_per_unit': notion.cost_per_unit,
            'unit_type': notion.unit_type,
            'notion_vendor_id': notion.notion_vendor_id
        })
    
    elif request.method == 'PUT':
        data = request.json
        notion.name = data.get('name', notion.name)
        notion.cost_per_unit = float(data.get('cost_per_unit', notion.cost_per_unit))
        notion.unit_type = data.get('unit_type', notion.unit_type)
        notion.notion_vendor_id = int(data.get('notion_vendor_id', notion.notion_vendor_id))
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(notion)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/notions', methods=['POST'])
def create_notion():
    data = request.json
    notion = Notion(
        name=data['name'],
        cost_per_unit=float(data['cost_per_unit']),
        unit_type=data['unit_type'],
        notion_vendor_id=int(data['notion_vendor_id'])
    )
    db.session.add(notion)
    db.session.commit()
    return jsonify({'success': True, 'id': notion.id})


# LABOR OPERATION ENDPOINTS
@app.route('/api/labors/<int:labor_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_labor(labor_id):
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
        data = request.json
        labor.name = data.get('name', labor.name)
        labor.cost_type = data.get('cost_type', labor.cost_type)
        labor.fixed_cost = float(data['fixed_cost']) if data.get('fixed_cost') else None
        labor.cost_per_hour = float(data['cost_per_hour']) if data.get('cost_per_hour') else None
        labor.cost_per_piece = float(data['cost_per_piece']) if data.get('cost_per_piece') else None
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(labor)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/labors', methods=['POST'])
def create_labor():
    data = request.json
    labor = LaborOperation(
        name=data['name'],
        cost_type=data['cost_type'],
        fixed_cost=float(data['fixed_cost']) if data.get('fixed_cost') else None,
        cost_per_hour=float(data['cost_per_hour']) if data.get('cost_per_hour') else None,
        cost_per_piece=float(data['cost_per_piece']) if data.get('cost_per_piece') else None
    )
    db.session.add(labor)
    db.session.commit()
    return jsonify({'success': True, 'id': labor.id})


# CLEANING COST ENDPOINTS
@app.route('/api/cleanings/<int:cleaning_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_cleaning(cleaning_id):
    cleaning = CleaningCost.query.get_or_404(cleaning_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': cleaning.id,
            'garment_type': cleaning.garment_type,
            'avg_minutes': cleaning.avg_minutes,
            'fixed_cost': cleaning.fixed_cost
        })
    
    elif request.method == 'PUT':
        data = request.json
        cleaning.garment_type = data.get('garment_type', cleaning.garment_type)
        cleaning.avg_minutes = int(data.get('avg_minutes', cleaning.avg_minutes))
        cleaning.fixed_cost = float(data.get('fixed_cost', cleaning.fixed_cost))
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(cleaning)
        db.session.commit()
        return jsonify({'success': True})
    
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
def create_cleaning():
    data = request.json
    cleaning = CleaningCost(
        garment_type=data['garment_type'],
        avg_minutes=int(data['avg_minutes']),
        fixed_cost=float(data['fixed_cost'])
    )
    db.session.add(cleaning)
    db.session.commit()
    return jsonify({'success': True, 'id': cleaning.id})
# ===== PLACEHOLDER ROUTES FOR FUTURE FEATURES =====
@app.route("/style/new")
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
def handle_variables():
    if request.method == 'GET':
        variables = Variable.query.order_by(Variable.name).all()
        return jsonify([{'id': v.id, 'name': v.name} for v in variables])
    
    elif request.method == 'POST':
        data = request.json
        variable_name = data.get('name', '').strip().upper()
        
        if not variable_name:
            return jsonify({'error': 'Variable name required'}), 400
        
        # Check if exists
        existing = Variable.query.filter(func.lower(Variable.name) == variable_name.lower()).first()
        if existing:
            return jsonify({'success': True, 'id': existing.id, 'name': existing.name, 'existed': True})
        
        # Create new
        variable = Variable(name=variable_name)
        db.session.add(variable)
        db.session.commit()
        
        return jsonify({'success': True, 'id': variable.id, 'name': variable.name, 'existed': False})

@app.route('/api/variables/<int:variable_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_variable(variable_id):
    variable = Variable.query.get_or_404(variable_id)
    
    if request.method == 'GET':
        return jsonify({'id': variable.id, 'name': variable.name})
    
    elif request.method == 'PUT':
        data = request.json
        variable.name = data.get('name', variable.name).strip().upper()
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(variable)
        db.session.commit()
        return jsonify({'success': True})
    
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


@app.post("/api/style/save")
def api_style_save():
    """
    Upsert a Style and replace its BOM, Labor, Colors, and Variables.
    Uses vendor_style as the unique identifier.
    """
    data = request.get_json(silent=True) or {}
    s = data.get("style") or {}
    
    style_name = (s.get("style_name") or "").strip()
    vendor_style = (s.get("vendor_style") or "").strip()
    
    if not style_name:
        return jsonify({"error": "style.style_name required"}), 400

    try:
        # Upsert style by vendor_style (the unique identifier)
        style = None
        is_new = False
        
        if vendor_style:
            # If vendor_style provided, look for existing style by vendor_style
            style = Style.query.filter_by(vendor_style=vendor_style).first()
        
        if not style:
            # If not found by vendor_style, try by style_name
            style = Style.query.filter(func.lower(Style.style_name) == style_name.lower()).first()
        
        if not style:
            # Create new style
            style = Style()
            is_new = True

        # Update style fields
        style.style_name = style_name
        style.vendor_style = vendor_style if vendor_style else None
        style.base_item_number = (s.get("base_item_number") or None)
        style.variant_code = (s.get("variant_code") or None)
        style.gender = (s.get("gender") or None)
        style.garment_type = (s.get("garment_type") or None)
        style.size_range = (s.get("size_range") or None)
        style.notes = (s.get("notes") or None)
        style.base_margin_percent = float(s.get("margin") or 60.0)
        style.suggested_price = float(s.get("suggested_price") or 0) if s.get("suggested_price") else None
        
        db.session.add(style)
        db.session.flush()

        # Wipe existing junctions
        StyleFabric.query.filter_by(style_id=style.id).delete()
        StyleNotion.query.filter_by(style_id=style.id).delete()
        StyleLabor.query.filter_by(style_id=style.id).delete()
        StyleColor.query.filter_by(style_id=style.id).delete()
        StyleVariable.query.filter_by(style_id=style.id).delete()
        db.session.flush()

        # Fabrics
        for f in data.get("fabrics") or []:
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

        # Notions
        for n in data.get("notions") or []:
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

        # Labor
        for l in data.get("labor") or []:
            if not l.get("name"):
                continue
            
            op = LaborOperation.query.filter(
                func.lower(LaborOperation.name) == l["name"].strip().lower()
            ).first()
            
            if not op:
                continue
            
            qty_or_hours = float(l.get("qty_or_hours") or 0)
            
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
                    time_hours=None,
                    quantity=int(qty_or_hours) if qty_or_hours else 1
                )
            db.session.add(sl)

        # Colors
        for color_data in data.get("colors") or []:
            color_id = color_data.get("color_id")
            if color_id:
                color = Color.query.get(color_id)
                if color:
                    style_color = StyleColor(
                        style_id=style.id,
                        color_id=color_id
                    )
                    db.session.add(style_color)

        # Variables
        for variable_data in data.get("variables") or []:
            variable_id = variable_data.get("variable_id")
            if variable_id:
                variable = Variable.query.get(variable_id)
                if variable:
                    style_variable = StyleVariable(
                        style_id=style.id,
                        variable_id=variable_id
                    )
                    db.session.add(style_variable)

        db.session.commit()
        return jsonify({"ok": True, "new": is_new, "style_id": style.id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
    
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
    app.run(debug=True, host='0.0.0.0', port=5000)