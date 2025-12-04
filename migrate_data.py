#!/usr/bin/env python3
"""
SQLite to PostgreSQL Data Migration Script
For J.A. Uniforms Pricing Tool

Usage:
    1. Make sure PostgreSQL database exists and tables are created (flask db upgrade)
    2. Set your DATABASE_URL environment variable for PostgreSQL
    3. Run: python migrate_data.py
"""

import os
import sqlite3
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extras import execute_batch

# ============================================
# CONFIGURATION - Update these paths as needed
# ============================================

# SQLite database path (check which one exists)
SQLITE_PATHS = [
    'uniforms.db',           # Root directory
    'instance/uniforms.db',  # Flask instance folder
    '../uniforms.db',        # Parent directory
]

# Find SQLite database
SQLITE_PATH = None
for path in SQLITE_PATHS:
    if os.path.exists(path):
        SQLITE_PATH = path
        break

if not SQLITE_PATH:
    print("❌ ERROR: Could not find SQLite database!")
    print("   Searched in:", SQLITE_PATHS)
    print("   Please update SQLITE_PATH in this script.")
    exit(1)

print(f"📂 Found SQLite database: {SQLITE_PATH}")

# PostgreSQL connection from environment
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable not set!")
    print("   Set it in your .env file or environment:")
    print("   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/ja_uniforms")
    exit(1)

# Handle postgres:// vs postgresql:// URL format
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

print(f"🔗 Connecting to PostgreSQL...")

# ============================================
# TABLES TO MIGRATE (in order for foreign keys)
# ============================================

TABLES = [
    # Independent tables first (no foreign keys)
    'users',
    'global_settings',
    'size_ranges',
    'size_variants',
    'fabric_vendors',
    'notion_vendors',
    'labor_operations',
    'cleaning_costs',
    'colors',
    'variables',
    
    # Tables with foreign keys to vendors
    'fabrics',
    'notions',
    
    # Main entity
    'styles',
    
    # Junction tables (depend on styles)
    'style_fabrics',
    'style_notions',
    'style_colors',
    'style_labor',
    'style_variables',
    'style_images',
    
    # Other
    'verification_codes',
]

# Boolean columns that need conversion (SQLite 0/1 -> PostgreSQL boolean)
BOOLEAN_COLUMNS = {
    'users': ['is_active', 'must_change_password'],
    'labor_operations': ['is_active'],
    'styles': ['is_active', 'is_favorite'],
    'style_fabrics': ['is_primary', 'is_sublimation'],
    'style_images': ['is_primary'],
}

# ============================================
# MIGRATION FUNCTIONS
# ============================================

def convert_row(table_name, columns, row):
    """Convert SQLite row to PostgreSQL-compatible format"""
    converted = list(row)
    
    # Convert booleans
    if table_name in BOOLEAN_COLUMNS:
        for i, col in enumerate(columns):
            if col in BOOLEAN_COLUMNS[table_name]:
                if converted[i] is not None:
                    converted[i] = bool(converted[i])
    
    return tuple(converted)


def migrate_table(sqlite_cur, pg_cur, pg_conn, table_name):
    """Migrate a single table from SQLite to PostgreSQL"""
    try:
        # Check if table exists in SQLite
        sqlite_cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not sqlite_cur.fetchone():
            print(f"  ⚠️  {table_name}: Table not found in SQLite (skipped)")
            return 0
        
        # Get data from SQLite
        sqlite_cur.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cur.fetchall()
        
        if not rows:
            print(f"  ⏭️  {table_name}: 0 records (empty)")
            return 0
        
        # Get column names
        columns = [description[0] for description in sqlite_cur.description]
        
        # Convert rows for PostgreSQL
        converted_rows = [convert_row(table_name, columns, row) for row in rows]
        
        # Build INSERT statement with ON CONFLICT DO NOTHING (to handle duplicates)
        cols_str = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        # Clear existing data in PostgreSQL table (optional - comment out to append)
        # pg_cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
        
        # Insert data
        success_count = 0
        for row in converted_rows:
            try:
                pg_cur.execute(
                    f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
                    row
                )
                if pg_cur.rowcount > 0:
                    success_count += 1
            except Exception as e:
                print(f"      Row error: {e}")
        
        pg_conn.commit()
        
        # Reset sequence for id columns
        if 'id' in columns:
            try:
                pg_cur.execute(f"SELECT MAX(id) FROM {table_name}")
                max_id = pg_cur.fetchone()[0]
                if max_id:
                    # PostgreSQL sequence naming convention
                    pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), {max_id}, true)")
                    pg_conn.commit()
            except Exception as e:
                # Sequence might not exist or have different name
                pass
        
        print(f"  ✅ {table_name}: {success_count}/{len(rows)} records migrated")
        return success_count
        
    except Exception as e:
        print(f"  ❌ {table_name}: ERROR - {e}")
        pg_conn.rollback()
        return 0


def main():
    print("\n" + "=" * 60)
    print("   J.A. UNIFORMS - SQLite to PostgreSQL Migration")
    print("=" * 60 + "\n")
    
    # Connect to SQLite
    try:
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cur = sqlite_conn.cursor()
        print(f"✅ Connected to SQLite: {SQLITE_PATH}")
    except Exception as e:
        print(f"❌ SQLite connection failed: {e}")
        exit(1)
    
    # Connect to PostgreSQL
    try:
        pg_conn = psycopg2.connect(DATABASE_URL)
        pg_cur = pg_conn.cursor()
        print(f"✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print(f"   Check your DATABASE_URL: {DATABASE_URL[:50]}...")
        exit(1)
    
    # Get record counts from SQLite
    print("\n📊 SQLite database contents:")
    for table in TABLES:
        try:
            sqlite_cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = sqlite_cur.fetchone()[0]
            print(f"   {table}: {count} records")
        except:
            print(f"   {table}: (table not found)")
    
    # Confirm migration
    print("\n" + "-" * 60)
    response = input("🚀 Start migration? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Migration cancelled.")
        sqlite_conn.close()
        pg_conn.close()
        exit(0)
    
    print("\n📦 Migrating tables...\n")
    
    # Migrate each table
    total_migrated = 0
    for table in TABLES:
        count = migrate_table(sqlite_cur, pg_cur, pg_conn, table)
        total_migrated += count
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()
    
    print("\n" + "=" * 60)
    print(f"   ✅ MIGRATION COMPLETE!")
    print(f"   Total records migrated: {total_migrated}")
    print("=" * 60 + "\n")
    
    print("📋 Next steps:")
    print("   1. Update your .env file: DATABASE_URL=postgresql://...")
    print("   2. Restart your Flask application")
    print("   3. Test the application thoroughly")
    print("   4. Keep your SQLite backup safe!\n")


if __name__ == '__main__':
    main()
