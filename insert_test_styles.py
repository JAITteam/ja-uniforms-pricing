"""
Insert 50 random test styles for testing
Run from project directory: python insert_test_styles.py
"""

import random
import string
from datetime import datetime

# Add parent directory to path
import sys
sys.path.insert(0, '.')

from app import app, db
from models import (
    Style, Fabric, Notion, LaborOperation, Color, Variable,
    StyleFabric, StyleNotion, StyleLabor, StyleColor, StyleVariable,
    FabricVendor, SizeRange
)

# Random data pools
FIRST_WORDS = [
    "Classic", "Modern", "Elegant", "Professional", "Executive", "Premium",
    "Signature", "Essential", "Heritage", "Contemporary", "Luxury", "Urban",
    "Traditional", "Refined", "Distinguished", "Prestige", "Imperial", "Royal",
    "Supreme", "Elite", "Grand", "Noble", "Regal", "Majestic", "Sterling"
]

SECOND_WORDS = [
    "Server", "Bartender", "Chef", "Host", "Manager", "Concierge", "Valet",
    "Bellman", "Housekeeping", "Front Desk", "Banquet", "Kitchen", "Dining",
    "Lounge", "Spa", "Resort", "Hotel", "Restaurant", "Catering", "Event"
]

GARMENT_TYPES_MAP = {
    "Jacket": "SS JACKET/LINED SS DRESS",
    "Blazer": "SS JACKET/LINED SS DRESS",
    "Vest": "VEST",
    "Shirt": "SS TOP/ SS DRESS",
    "Blouse": "SS TOP/ SS DRESS",
    "Pants": "PANTS",
    "Trousers": "PANTS",
    "Skirt": "SHORTS/SKIRTS",
    "Dress": "SS TOP/ SS DRESS",
    "Apron": "APRON",
    "Polo": "SS TOP/ SS DRESS",
    "Tunic": "LS TOP/ LS DRESS"
}

GARMENT_STYLES = list(GARMENT_TYPES_MAP.keys())

GENDERS = ["MENS", "LADIES", "UNISEX"]

def generate_random_style_name():
    """Generate a random style name"""
    first = random.choice(FIRST_WORDS)
    second = random.choice(SECOND_WORDS)
    garment = random.choice(GARMENT_STYLES)
    return f"{first} {second} {garment}"

def insert_test_styles():
    with app.app_context():
        # Get existing data for relationships
        fabrics = Fabric.query.all()
        notions = Notion.query.all()
        labor_ops = LaborOperation.query.all()
        colors = Color.query.all()
        variables = Variable.query.all()
        size_ranges = SizeRange.query.all()
        
        if not fabrics:
            print("❌ No fabrics found! Please add some fabrics first.")
            return
        
        if not colors:
            print("❌ No colors found! Please add some colors first.")
            return
        
        print(f"\n📊 Available data:")
        print(f"   • Fabrics: {len(fabrics)}")
        print(f"   • Notions: {len(notions)}")
        print(f"   • Labor Ops: {len(labor_ops)}")
        print(f"   • Colors: {len(colors)}")
        print(f"   • Variables: {len(variables)}")
        print(f"   • Size Ranges: {len(size_ranges)}")
        
        created_count = 0
        skipped_count = 0
        
        print(f"\n🔄 Creating 50 test styles...\n")
        
        for i in range(50):
            try:
                # Generate style data
                style_name = generate_random_style_name()
                gender = random.choice(GENDERS)
                
                # Determine garment type from style name
                garment_type = "SS TOP/ SS DRESS"
                for garment, gtype in GARMENT_TYPES_MAP.items():
                    if garment.lower() in style_name.lower():
                        garment_type = gtype
                        break
                
                # Pick random size range
                size_range = random.choice(size_ranges).name if size_ranges else "XS-4XL"
                
                # Random margin between 55-65%
                margin = round(random.uniform(55, 65), 1)
                
                # Select fabrics first so we can build vendor_style correctly
                num_fabrics = random.randint(1, min(3, len(fabrics)))
                selected_fabrics = random.sample(fabrics, num_fabrics)
                primary_fabric = selected_fabrics[0]
                is_sublimation = random.choice([True, False, False, False])  # 25% chance for primary
                
                # Build vendor style with fabric code
                base_item = f"99{900 + i:03d}"
                fabric_code = primary_fabric.fabric_code or ''
                full_vendor_style = base_item + fabric_code
                if is_sublimation and fabric_code:
                    full_vendor_style += 'P'
                
                # Check if already exists
                existing = Style.query.filter_by(vendor_style=full_vendor_style).first()
                if existing:
                    skipped_count += 1
                    print(f"   ⏭️  {full_vendor_style} already exists, skipping")
                    continue
                
                # Create style
                style = Style(
                    vendor_style=full_vendor_style,
                    base_item_number=base_item,
                    style_name=style_name,
                    gender=gender,
                    garment_type=garment_type,
                    size_range=size_range,
                    base_margin_percent=margin,
                    notes=f"Test style created on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                )
                db.session.add(style)
                db.session.flush()
                
                # Add fabrics
                for idx, fabric in enumerate(selected_fabrics):
                    sf = StyleFabric(
                        style_id=style.id,
                        fabric_id=fabric.id,
                        yards_required=round(random.uniform(1.0, 3.5), 2),
                        is_primary=(idx == 0),
                        is_sublimation=(is_sublimation if idx == 0 else random.choice([True, False, False, False]))
                    )
                    db.session.add(sf)
                
                # Add 0-4 random notions
                if notions:
                    num_notions = random.randint(0, min(4, len(notions)))
                    if num_notions > 0:
                        selected_notions = random.sample(notions, num_notions)
                        for notion in selected_notions:
                            sn = StyleNotion(
                                style_id=style.id,
                                notion_id=notion.id,
                                quantity_required=random.randint(1, 10)
                            )
                            db.session.add(sn)
                
                # Add 1-3 random labor operations
                if labor_ops:
                    num_labor = random.randint(1, min(3, len(labor_ops)))
                    selected_labor = random.sample(labor_ops, num_labor)
                    for op in selected_labor:
                        sl = StyleLabor(
                            style_id=style.id,
                            labor_operation_id=op.id,
                            time_hours=round(random.uniform(0.5, 2.0), 2) if op.cost_type == 'hourly' else 0,
                            quantity=random.randint(1, 3) if op.cost_type != 'hourly' else 0
                        )
                        db.session.add(sl)
                
                # Add 2-6 random colors
                num_colors = random.randint(2, min(6, len(colors)))
                selected_colors = random.sample(colors, num_colors)
                for color in selected_colors:
                    sc = StyleColor(style_id=style.id, color_id=color.id)
                    db.session.add(sc)
                
                # Add 0-2 random variables
                if variables:
                    num_vars = random.randint(0, min(2, len(variables)))
                    if num_vars > 0:
                        selected_vars = random.sample(variables, num_vars)
                        for var in selected_vars:
                            sv = StyleVariable(style_id=style.id, variable_id=var.id)
                            db.session.add(sv)
                
                # Calculate suggested price
                db.session.flush()
                total_cost = style.get_total_cost()
                if total_cost > 0 and margin < 100:
                    style.suggested_price = round(total_cost / (1 - margin/100), 2)
                
                db.session.commit()
                created_count += 1
                
                print(f"   ✅ {full_vendor_style}: {style_name} (${style.suggested_price or 0:.2f})")
                
            except Exception as e:
                db.session.rollback()
                print(f"   ❌ Error creating style {i+1}: {e}")
                skipped_count += 1
        
        print(f"\n" + "="*60)
        print(f"✅ COMPLETE!")
        print(f"   • Created: {created_count} styles")
        print(f"   • Skipped: {skipped_count} styles")
        print(f"="*60)

if __name__ == "__main__":
    insert_test_styles()