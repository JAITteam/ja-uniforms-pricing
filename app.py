import pandas as pd
from flask import Config, Flask, request, redirect, url_for
from flask import jsonify, request
from sqlalchemy import func
from models import Style
from database import db
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from config import Config
from database import db
import os
from werkzeug.utils import secure_filename



# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)


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
    return render_template('dashboard.html')

@app.route('/search', methods=['POST'])
def search_style():
    vendor_style = request.form.get('vendor_style', '').strip()
    if vendor_style:
        return redirect(url_for('style_wizard') + f'?vendor_style={vendor_style}')
    return redirect(url_for('index'))

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
    style = Style.query.get_or_404(style_id)
    
    if 'image' not in request.files:
        return jsonify({'error': 'No file'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{style_id}_{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Check if this should be primary (first image)
        is_primary = StyleImage.query.filter_by(style_id=style_id).count() == 0
        
        img = StyleImage(
            style_id=style_id,
            filename=filename,
            is_primary=is_primary
        )
        db.session.add(img)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'id': img.id,
            'filename': filename,
            'url': f'/static/img/{filename}'
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/style-image/<int:image_id>', methods=['DELETE'])
def delete_style_image(image_id):
    img = StyleImage.query.get_or_404(image_id)
    
    # Delete file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], img.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    db.session.delete(img)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/style/<int:style_id>/images', methods=['GET'])
def get_style_images(style_id):
    images = StyleImage.query.filter_by(style_id=style_id).order_by(StyleImage.is_primary.desc()).all()
    return jsonify([{
        'id': img.id,
        'url': f'/static/img/{img.filename}',
        'is_primary': img.is_primary
    } for img in images])



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
    styles = Style.query.order_by(Style.vendor_style).all()
    
    # Get unique genders for filter dropdown
    genders = db.session.query(Style.gender).distinct().all()
    gender_list = [g[0] for g in genders if g[0]]
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>All Styles - J.A Uniforms</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .filter-section { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .table-container { background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            table { margin-bottom: 0; }
            th { cursor: pointer; user-select: none; background-color: #e9ecef; position: relative; }
            th:hover { background-color: #dee2e6; }
            th.sortable::after { content: ' ⇅'; color: #999; }
            th.sort-asc::after { content: ' ↑'; color: #000; }
            th.sort-desc::after { content: ' ↓'; color: #000; }
            .no-results { text-align: center; padding: 40px; color: #666; }
            .search-box { max-width: 400px; }
            .filter-group { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
            .badge { font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div class="container-fluid" style="max-width: 1400px;">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h1>All Uniform Styles</h1>
                    <p class="text-muted mb-0">Total: <span id="totalCount">0</span> styles</p>
                </div>
                <a href="/admin-panel" class="btn btn-secondary">Back to Admin</a>
            </div>

            <!-- Filters Section -->
            <div class="filter-section">
                <div class="row g-3">
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Search</label>
                        <input 
                            type="text" 
                            id="searchInput" 
                            class="form-control" 
                            placeholder="Search vendor style, name, or any field..."
                            autocomplete="off">
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-bold">Gender</label>
                        <select id="genderFilter" class="form-select">
                            <option value="">All Genders</option>
    """
    
    for gender in gender_list:
        html += f'<option value="{gender}">{gender}</option>'
    
    html += """
                        </select>
                    </div>
                    <div class="col-md-3">
                        <label class="form-label fw-bold">Cost Range</label>
                        <select id="costFilter" class="form-select">
                            <option value="">All Costs</option>
                            <option value="0-30">$0 - $30</option>
                            <option value="30-50">$30 - $50</option>
                            <option value="50-100">$50 - $100</option>
                            <option value="100-999">$100+</option>
                        </select>
                    </div>
                </div>
                <div class="mt-3">
                    <button class="btn btn-sm btn-outline-secondary" onclick="clearFilters()">Clear All Filters</button>
                </div>
            </div>

            <!-- Table -->
            <div class="table-container">
                <table class="table table-hover" id="stylesTable">
                    <thead>
                        <tr>
                            <th class="sortable" data-sort="vendor_style">Vendor Style</th>
                            <th class="sortable" data-sort="style_name">Style Name</th>
                            <th class="sortable" data-sort="gender">Gender</th>
                            <th class="sortable text-end" data-sort="total_cost">Total Cost</th>
                            <th class="sortable text-end" data-sort="retail_price">Retail Price</th>
                            <th class="text-center">Action</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
    """
    
    for style in styles:
        total_cost = style.get_total_cost()
        retail_price = style.get_retail_price()
        html += f"""
                        <tr data-vendor-style="{style.vendor_style}" 
                            data-style-name="{style.style_name}" 
                            data-gender="{style.gender}"
                            data-total-cost="{total_cost}"
                            data-retail-price="{retail_price}">
                            <td><strong>{style.vendor_style}</strong></td>
                            <td>{style.style_name}</td>
                            <td><span class="badge bg-secondary">{style.gender}</span></td>
                            <td class="text-end">${total_cost:.2f}</td>
                            <td class="text-end">${retail_price:.2f}</td>
                            <td class="text-center">
                                <a href="/style/new?vendor_style={style.vendor_style}" class="btn btn-sm btn-primary">Edit</a>
                            </td>
                        </tr>
        """
    
    html += """
                    </tbody>
                </table>
                <div id="noResults" class="no-results" style="display: none;">
                    <p>No styles match your filters.</p>
                </div>
            </div>
        </div>

        <script>
            const rows = document.querySelectorAll('#tableBody tr');
            const searchInput = document.getElementById('searchInput');
            const genderFilter = document.getElementById('genderFilter');
            const costFilter = document.getElementById('costFilter');
            const totalCount = document.getElementById('totalCount');
            const noResults = document.getElementById('noResults');
            const tableBody = document.getElementById('tableBody');

            let currentSort = { column: null, direction: 'asc' };

            // Update count
            function updateCount() {
                const visible = Array.from(rows).filter(r => r.style.display !== 'none').length;
                totalCount.textContent = visible;
                noResults.style.display = visible === 0 ? 'block' : 'none';
                tableBody.style.display = visible === 0 ? 'none' : '';
            }

            // Filter function
            function filterTable() {
                const searchTerm = searchInput.value.toLowerCase();
                const selectedGender = genderFilter.value.toLowerCase();
                const selectedCost = costFilter.value;

                rows.forEach(row => {
                    const vendorStyle = row.dataset.vendorStyle.toLowerCase();
                    const styleName = row.dataset.styleName.toLowerCase();
                    const gender = row.dataset.gender.toLowerCase();
                    const totalCost = parseFloat(row.dataset.totalCost);

                    // Search filter
                    const matchesSearch = !searchTerm || 
                        vendorStyle.includes(searchTerm) || 
                        styleName.includes(searchTerm) ||
                        gender.includes(searchTerm);

                    // Gender filter
                    const matchesGender = !selectedGender || gender === selectedGender;

                    // Cost filter
                    let matchesCost = true;
                    if (selectedCost) {
                        const [min, max] = selectedCost.split('-').map(Number);
                        matchesCost = totalCost >= min && totalCost <= (max || Infinity);
                    }

                    row.style.display = matchesSearch && matchesGender && matchesCost ? '' : 'none';
                });

                updateCount();
            }

            // Sort function
            function sortTable(column) {
                const sortedRows = Array.from(rows);
                
                // Toggle direction
                if (currentSort.column === column) {
                    currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
                } else {
                    currentSort.column = column;
                    currentSort.direction = 'asc';
                }

                sortedRows.sort((a, b) => {
                    let aVal = a.dataset[column];
                    let bVal = b.dataset[column];

                    // Convert to numbers for cost/price columns
                    if (column === 'total_cost' || column === 'retail_price') {
                        aVal = parseFloat(aVal);
                        bVal = parseFloat(bVal);
                    } else {
                        aVal = aVal.toLowerCase();
                        bVal = bVal.toLowerCase();
                    }

                    if (aVal < bVal) return currentSort.direction === 'asc' ? -1 : 1;
                    if (aVal > bVal) return currentSort.direction === 'asc' ? 1 : -1;
                    return 0;
                });

                // Re-append rows in sorted order
                sortedRows.forEach(row => tableBody.appendChild(row));

                // Update header indicators
                document.querySelectorAll('th.sortable').forEach(th => {
                    th.classList.remove('sort-asc', 'sort-desc');
                });
                const activeHeader = document.querySelector(`th[data-sort="${column}"]`);
                activeHeader.classList.add(currentSort.direction === 'asc' ? 'sort-asc' : 'sort-desc');
            }

            // Clear filters
            function clearFilters() {
                searchInput.value = '';
                genderFilter.value = '';
                costFilter.value = '';
                filterTable();
            }

            // Event listeners
            searchInput.addEventListener('input', filterTable);
            genderFilter.addEventListener('change', filterTable);
            costFilter.addEventListener('change', filterTable);

            document.querySelectorAll('th.sortable').forEach(th => {
                th.addEventListener('click', () => sortTable(th.dataset.sort));
            });

            // Initial count
            updateCount();
        </script>
    </body>
    </html>
    """
    
    return html

# ADD THESE ROUTES TO YOUR app.py
# These replace your existing /master-costs route and add the API endpoints

# ===== EDITABLE MASTER COSTS - REPLACE EXISTING /master-costs ROUTE =====

# ADD THESE ROUTES TO YOUR app.py
# These replace your existing /master-costs route and add the API endpoints

# ===== EDITABLE MASTER COSTS WITH VENDOR MANAGEMENT =====

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
                <div>
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
                <div>
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
                    <tr data-id="{fabric.id}">
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
                    <tr data-id="{labor.id}">
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
            <p style="color: #666; margin-bottom: 15px;">Based on $19.32/hour = $0.32/minute</p>
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
            <h2>Colors</h2>
            <div style="margin-bottom: 15px;">
                <input type="text" id="colorSearch" placeholder="Search colors..." style="width: 300px; padding: 8px; margin-bottom: 10px;">
            </div>
            <button class="btn btn-success add-row-btn" onclick="openModal('color')">+ Add Color</button>
            <table class="vendors">
                <thead>
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
                const inputs = document.querySelectorAll('#modalBody input, #modalBody select');
                
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

            // Color search filter - ADD THIS ENTIRE BLOCK HERE
            document.getElementById('colorSearch')?.addEventListener('input', function() {{
                const searchTerm = this.value.toLowerCase();
                const rows = document.querySelectorAll('.color-row');
                
                rows.forEach(row => {{
                    const colorName = row.cells[0].textContent.toLowerCase();
                    row.style.display = colorName.includes(searchTerm) ? '' : 'none';
                }});
            }});
 
            function deleteItem(type, id) {{
                fetch(`/api/${{type}}s/${{id}}`, {{
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
    
    return render_template("style_wizard.html", 
                          fabric_vendors=fabric_vendors,
                          notion_vendors=notion_vendors,
                          fabrics=fabrics,
                          notions=notions,
                          labor_ops=labor_ops,
                          garment_types=garment_types)

@app.route("/import-step1", methods=["GET","POST"])
def import_step1():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Upload an .xlsx file", "warning")
            return redirect(url_for("import_step1"))
        import pandas as pd
        xls = pd.ExcelFile(file)
        sheets = []
        for name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=name)
            if df.empty: 
                continue
            cols = {c.lower().strip(): c for c in df.columns}
            item_col = next((cols[k] for k in cols if "item" in k), None)
            variant_col = next((cols[k] for k in cols if "variant" in k), None)
            name_col = next((cols[k] for k in cols if k in ("name","style name","description")), None)
            preview = []
            if item_col and name_col:
                row0 = df.iloc[0]
                base = str(row0[item_col]).strip().split("-")[0]
                variant = str(row0[variant_col]).strip() if variant_col else ""
                vendor_style = "-".join([p for p in [base, variant] if p])
                preview.append({
                    "sheet": name,
                    "vendor_style": vendor_style,
                    "base_item_number": base,
                    "variant_code": variant,
                    "style_name": str(row0[name_col]).strip(),
                })
            sheets.append(preview)
        return render_template("import_step1.html", previews=sheets)
    return render_template("import_step1.html", previews=None)

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
            "label_cost": float(style.avg_label_cost or 0.20),  # NEW
            "shipping_cost": float(style.shipping_cost or 0.00),  # NEW
            "suggested_price": float(style.suggested_price or 0) if style.suggested_price else None,  # NEW
        },
        "fabrics": fabrics_payload,
        "notions": notions_payload,
        "labor": labor_payload,
        "cleaning": cleaning_payload,
        "colors": colors_payload,  # NEW
}), 200


@app.post("/api/style/save")
def api_style_save():
    """
    Upsert a Style and replace its BOM, Labor, and Colors with the payload from the UI.
    """
    data = request.get_json(silent=True) or {}
    s = data.get("style") or {}
    name = (s.get("style_name") or "").strip()
    if not name:
        return jsonify({"error": "style.style_name required"}), 400

    try:
        # Upsert style by style_name
        style = Style.query.filter(func.lower(Style.style_name) == name.lower()).first()
        is_new = False
        if not style:
            style = Style()
            is_new = True

        style.style_name = name
        style.vendor_style = (s.get("vendor_style") or None)
        style.base_item_number = (s.get("base_item_number") or None)
        style.variant_code = (s.get("variant_code") or None)
        style.gender = (s.get("gender") or None)
        style.garment_type = (s.get("garment_type") or None)
        style.size_range = (s.get("size_range") or None)
        style.base_margin_percent = float(s.get("margin") or 60.0)
        style.avg_label_cost = float(s.get("label_cost") or 0.20)
        style.shipping_cost = float(s.get("shipping_cost") or 0.00)  # NEW
        style.suggested_price = float(s.get("suggested_price") or 0) if s.get("suggested_price") else None  # NEW
        
        db.session.add(style)
        db.session.flush()

        # Wipe existing junctions
        StyleFabric.query.filter_by(style_id=style.id).delete()
        StyleNotion.query.filter_by(style_id=style.id).delete()
        StyleLabor.query.filter_by(style_id=style.id).delete()
        StyleColor.query.filter_by(style_id=style.id).delete()  # NEW
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
                    is_sublimation=bool(f.get("sublimation") or False)  # ADD THIS LIne
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

        # Colors - NEW SECTION
        for color_data in data.get("colors") or []:
            color_id = color_data.get("color_id")
            if color_id:
                # Verify color exists
                color = Color.query.get(color_id)
                if color:
                    style_color = StyleColor(
                        style_id=style.id,
                        color_id=color_id
                    )
                    db.session.add(style_color)

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