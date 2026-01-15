"""
Delete the 50 test styles that were inserted
Run from project directory: python delete_test_styles.py
"""

import sys
sys.path.insert(0, '.')

from app import app, db
from models import (
    Style, StyleFabric, StyleNotion, StyleLabor, StyleColor, StyleVariable
)

def delete_test_styles():
    with app.app_context():
        # Find all test styles (vendor_style starting with 99900-99949 or 99900T-99949T etc.)
        test_styles = Style.query.filter(
            Style.vendor_style.like('999%')
        ).all()
        
        if not test_styles:
            print("❌ No test styles found to delete.")
            return
        
        print(f"\n🔍 Found {len(test_styles)} test styles to delete:\n")
        
        for style in test_styles[:10]:  # Show first 10
            print(f"   • {style.vendor_style}: {style.style_name}")
        
        if len(test_styles) > 10:
            print(f"   ... and {len(test_styles) - 10} more")
        
        confirm = input(f"\n⚠️  Delete all {len(test_styles)} styles? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Cancelled.")
            return
        
        deleted_count = 0
        
        for style in test_styles:
            try:
                # Delete related records first
                StyleFabric.query.filter_by(style_id=style.id).delete()
                StyleNotion.query.filter_by(style_id=style.id).delete()
                StyleLabor.query.filter_by(style_id=style.id).delete()
                StyleColor.query.filter_by(style_id=style.id).delete()
                StyleVariable.query.filter_by(style_id=style.id).delete()
                
                # Delete the style
                db.session.delete(style)
                deleted_count += 1
                
            except Exception as e:
                print(f"   ❌ Error deleting {style.vendor_style}: {e}")
                db.session.rollback()
        
        db.session.commit()
        
        print(f"\n✅ Deleted {deleted_count} test styles successfully!")

if __name__ == "__main__":
    delete_test_styles()