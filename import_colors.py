"""
Import colors from V100COLORS.xlsx
Run this script from the ja-uniforms-pricing folder:
    python import_colors.py
"""
import pandas as pd
from app import app, db, Color

def import_colors():
    # Read Excel file
    df = pd.read_excel('V100COLORS.xlsx')
    
    imported = 0
    skipped = 0
    
    with app.app_context():
        for _, row in df.iterrows():
            color_name = str(row['Color']).strip().upper()
            
            if not color_name or color_name == 'NAN':
                continue
            
            # Check if color already exists
            existing = Color.query.filter_by(name=color_name).first()
            if existing:
                print(f"  Skipped (exists): {color_name}")
                skipped += 1
                continue
            
            # Create new color
            color = Color(name=color_name)
            db.session.add(color)
            imported += 1
            print(f"  Added: {color_name}")
        
        db.session.commit()
        print(f"\n✅ Import complete!")
        print(f"   Imported: {imported}")
        print(f"   Skipped: {skipped}")

if __name__ == '__main__':
    import_colors()