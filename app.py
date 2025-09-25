from flask import Flask, render_template, redirect, url_for, request
from config import Config
from database import db

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

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
        return redirect(url_for('view_style', vendor_style=vendor_style))
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
    
    html = """
    <div style="max-width: 1200px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
        <h1>All Uniform Styles</h1>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead>
                <tr style="background-color: #f8f9fa;">
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Vendor Style</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Style Name</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Gender</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: right;">Total Cost</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: right;">Retail Price</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: center;">Action</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for style in styles:
        html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 12px;"><strong>{style.vendor_style}</strong></td>
                <td style="border: 1px solid #ddd; padding: 12px;">{style.style_name}</td>
                <td style="border: 1px solid #ddd; padding: 12px;">{style.gender}</td>
                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">${style.get_total_cost():.2f}</td>
                <td style="border: 1px solid #ddd; padding: 12px; text-align: right;">${style.get_retail_price():.2f}</td>
                <td style="border: 1px solid #ddd; padding: 12px; text-align: center;">
                    <a href="/style/{style.vendor_style}" style="background-color: #007bff; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">View</a>
                </td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
        <div style="margin: 20px 0;">
            <a href="/admin-panel" style="background-color: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Back to Admin</a>
        </div>
    </div>
    """
    return html

@app.route('/master-costs')
def master_costs():
    fabrics = Fabric.query.order_by(Fabric.name).all()
    notions = Notion.query.order_by(Notion.name).all()
    labor_ops = LaborOperation.query.order_by(LaborOperation.name).all()
    cleaning_costs = CleaningCost.query.order_by(CleaningCost.garment_type).all()
    
    html = """
    <div style="max-width: 1200px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
        <h1>Master Cost Lists</h1>
        
        <h2>Fabrics</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead>
                <tr style="background-color: #e3f2fd;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Name</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Code</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Cost/Yard</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Vendor</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for fabric in fabrics:
        vendor_name = fabric.fabric_vendor.name if fabric.fabric_vendor else 'N/A'
        html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{fabric.name}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{fabric.fabric_code or ''}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">${fabric.cost_per_yard:.2f}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{vendor_name}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <h2>Notions</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead>
                <tr style="background-color: #f3e5f5;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Name</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Cost/Unit</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Unit Type</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Vendor</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for notion in notions:
        vendor_name = notion.notion_vendor.name if notion.notion_vendor else 'N/A'
        html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{notion.name}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">${notion.cost_per_unit:.4f}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{notion.unit_type}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{vendor_name}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <h2>Labor Operations</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead>
                <tr style="background-color: #fff3e0;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Operation</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Cost Type</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Rate</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for labor in labor_ops:
        if labor.cost_type == 'flat_rate':
            rate = f"${labor.fixed_cost:.2f} flat"
        elif labor.cost_type == 'hourly':
            rate = f"${labor.cost_per_hour:.2f}/hour"
        elif labor.cost_type == 'per_piece':
            rate = f"${labor.cost_per_piece:.2f}/piece"
        else:
            rate = "Variable"
            
        html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{labor.name}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{labor.cost_type.replace('_', ' ').title()}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{rate}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <h2>Cleaning Costs</h2>
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <thead>
                <tr style="background-color: #e8f5e8;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Garment Type</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Minutes</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">Fixed Cost</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for cleaning in cleaning_costs:
        html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{cleaning.garment_type}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{cleaning.avg_minutes}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">${cleaning.fixed_cost:.2f}</td>
            </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <div style="margin: 20px 0;">
            <a href="/admin-panel" style="background-color: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Back to Admin</a>
        </div>
    </div>
    """
    return html

# ===== PLACEHOLDER ROUTES FOR FUTURE FEATURES =====
@app.route('/import-excel')
def import_excel():
    return """
    <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
        <h1>Excel Import</h1>
        <p>This feature will be implemented in the next phase to import your 400 existing uniform styles from Excel.</p>
        <a href="/admin-panel" style="background-color: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Back to Admin</a>
    </div>
    """

# ===== APPLICATION STARTUP =====
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)