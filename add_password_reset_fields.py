"""
ADD PASSWORD RESET FIELDS TO USER TABLE
=======================================
This script adds the necessary columns for admin-controlled password reset:
- must_change_password: Boolean flag to force password change on login
- temp_password_created_at: When the temporary password was set

Usage:
    python add_password_reset_fields.py
"""

import sqlite3
import os

DB_PATH = 'instance/uniforms.db'

def add_password_reset_fields():
    """Add password reset columns to users table"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at: {DB_PATH}")
        return False
    
    print("=" * 60)
    print("🔧 ADDING PASSWORD RESET FIELDS TO USERS TABLE")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check current columns
        cursor.execute("PRAGMA table_info(users)")
        columns = {col[1] for col in cursor.fetchall()}
        
        print(f"\n📋 Current columns: {len(columns)}")
        
        # Add must_change_password column if not exists
        if 'must_change_password' not in columns:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN must_change_password BOOLEAN DEFAULT 0
            """)
            print("✅ Added: must_change_password column")
        else:
            print("⏭️  SKIP: must_change_password (already exists)")
        
        # Add temp_password_created_at column if not exists
        if 'temp_password_created_at' not in columns:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN temp_password_created_at DATETIME
            """)
            print("✅ Added: temp_password_created_at column")
        else:
            print("⏭️  SKIP: temp_password_created_at (already exists)")
        
        conn.commit()
        
        # Verify
        cursor.execute("PRAGMA table_info(users)")
        new_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📋 Updated columns in 'users' table:")
        for col in new_columns:
            marker = "✅ NEW" if col in ['must_change_password', 'temp_password_created_at'] else ""
            print(f"   - {col} {marker}")
        
        print("\n" + "=" * 60)
        print("✅ PASSWORD RESET FIELDS ADDED SUCCESSFULLY!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


if __name__ == '__main__':
    success = add_password_reset_fields()
    
    if success:
        print("\n🎉 Database updated!")
        print("\n📝 Next steps:")
        print("   1. Update your models.py (add the new fields)")
        print("   2. Update admin_users.html (add reset button)")
        print("   3. Add new routes to app.py")
    else:
        print("\n❌ Failed. Please check errors above.")