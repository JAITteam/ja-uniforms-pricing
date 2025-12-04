#!/usr/bin/env python3
"""
Import data from JSON export to PostgreSQL database
Run this AFTER running migrations: flask db upgrade
"""
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from app import app, db
from models import (
    User, FabricVendor, NotionVendor, Fabric, Notion, 
    LaborOperation, CleaningCost, SizeRange, SizeVariant,
    Color, Variable, Style, StyleFabric, StyleNotion, 
    StyleLabor, StyleColor, StyleVariable, StyleImage,
    GlobalSetting, VerificationCode
)

# Table import order (respecting foreign key dependencies)
TABLE_MODELS = {
    # Independent tables (no foreign keys)
    'users': User,
    'fabric_vendors': FabricVendor,
    'notion_vendors': NotionVendor,
    'labor_operations': LaborOperation,
    'cleaning_costs': CleaningCost,
    'size_ranges': SizeRange,
    'size_variants': SizeVariant,
    'colors': Color,
    'variables': Variable,
    'global_settings': GlobalSetting,
    'verification_codes': VerificationCode,
    
    # Dependent on vendors
    'fabrics': Fabric,
    'notions': Notion,
    
    # Dependent on styles (must come after styles)
    'styles': Style,
    
    # Junction tables (must come last)
    'style_fabrics': StyleFabric,
    'style_notions': StyleNotion,
    'style_labor': StyleLabor,
    'style_colors': StyleColor,
    'style_variables': StyleVariable,
    'style_images': StyleImage,
}

def parse_datetime(value):
    """Parse datetime string to datetime object"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except:
        return None

def import_table(table_name, rows, model_class):
    """Import data into a specific table"""
    if not rows:
        print(f"  ⊘ {table_name}: No data to import")
        return 0
    
    print(f"  → Importing {table_name}...", end=' ')
    
    imported = 0
    skipped = 0
    
    for row in rows:
        try:
            # Convert datetime strings to datetime objects
            for key, value in row.items():
                if key.endswith('_at') or key == 'last_login':
                    row[key] = parse_datetime(value)
            
            # Create model instance
            instance = model_class(**row)
            db.session.add(instance)
            imported += 1
            
        except Exception as e:
            print(f"\n    ✗ Error importing row: {e}")
            print(f"      Row data: {row}")
            skipped += 1
            db.session.rollback()
    
    try:
        db.session.commit()
        print(f"✓ {imported} rows imported", end='')
        if skipped:
            print(f" ({skipped} skipped)")
        else:
            print()
        return imported
    except Exception as e:
        db.session.rollback()
        print(f"\n    ✗ Commit failed: {e}")
        return 0

def main():
    print("🔄 Starting PostgreSQL data import...")
    print("⚠️  Make sure you've run 'flask db upgrade' first!\n")
    
    # Load exported data
    try:
        with open('sqlite_export.json', 'r') as f:
            export_data = json.load(f)
        print(f"✓ Loaded export file (sqlite_export.json)")
    except FileNotFoundError:
        print("✗ Error: sqlite_export.json not found!")
        print("  Run export_sqlite_data.py first")
        sys.exit(1)
    
    with app.app_context():
        print("\n📊 Importing tables in dependency order...")
        
        total_imported = 0
        
        for table_name, model_class in TABLE_MODELS.items():
            if table_name in export_data:
                count = import_table(table_name, export_data[table_name], model_class)
                total_imported += count
            else:
                print(f"  ⊘ {table_name}: Not found in export")
        
        # Reset sequences for PostgreSQL
        print("\n🔧 Resetting PostgreSQL sequences...")
        tables_with_id = [
            'users', 'fabric_vendors', 'notion_vendors', 'fabrics', 'notions',
            'labor_operations', 'cleaning_costs', 'size_ranges', 'size_variants',
            'colors', 'variables', 'styles', 'style_fabrics', 'style_notions',
            'style_labor', 'style_colors', 'style_variables', 'style_images',
            'global_settings', 'verification_codes'
        ]
        
        for table in tables_with_id:
            try:
                db.session.execute(f"""
                    SELECT setval('{table}_id_seq', 
                    COALESCE((SELECT MAX(id) FROM {table}), 1));
                """)
                print(f"  ✓ Reset sequence for {table}")
            except Exception as e:
                print(f"  ⊘ No sequence for {table}")
        
        db.session.commit()
        
        print(f"\n✅ Import complete!")
        print(f"📦 Total rows imported: {total_imported}")
        
        # Verify import
        print("\n🔍 Verifying import...")
        print(f"  • Users: {User.query.count()}")
        print(f"  • Styles: {Style.query.count()}")
        print(f"  • Fabrics: {Fabric.query.count()}")
        print(f"  • Notions: {Notion.query.count()}")
        print(f"  • Labor Operations: {LaborOperation.query.count()}")

if __name__ == '__main__':
    main()
