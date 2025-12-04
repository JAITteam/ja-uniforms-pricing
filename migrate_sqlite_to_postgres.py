#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script for J.A. Uniforms
========================================================

This script migrates all data from SQLite to PostgreSQL while preserving
data integrity and relationships.

Usage:
    1. Install requirements: pip install -r requirements.txt
    2. Set up PostgreSQL database (see PRODUCTION_DEPLOYMENT_GUIDE.md)
    3. Configure the PostgreSQL connection below
    4. Run: python migrate_sqlite_to_postgres.py

Author: J.A. IT Team
"""

import os
import sqlite3
from datetime import datetime

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    exit(1)

# ============================================
# CONFIGURATION - MODIFY THESE VALUES
# ============================================

# SQLite source database
SQLITE_DB_PATH = "instance/uniforms.db"  # or "uniforms.db" if in root

# PostgreSQL target database
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "ja_uniforms",
    "user": "ja_uniforms_user",
    "password": "your_secure_password_here"  # CHANGE THIS!
}

# ============================================
# MIGRATION LOGIC
# ============================================

def get_sqlite_connection():
    """Connect to SQLite database."""
    if not os.path.exists(SQLITE_DB_PATH):
        # Try alternative paths
        alt_paths = ["uniforms.db", "instance/uniforms.db", "../uniforms.db"]
        for path in alt_paths:
            if os.path.exists(path):
                return sqlite3.connect(path)
        print(f"ERROR: SQLite database not found at {SQLITE_DB_PATH}")
        print("Tried paths:", alt_paths)
        exit(1)
    return sqlite3.connect(SQLITE_DB_PATH)


def get_postgres_connection():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"ERROR: Cannot connect to PostgreSQL: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is installed and running")
        print("2. Database 'ja_uniforms' exists")
        print("3. User and password are correct")
        print("4. User has permissions on the database")
        exit(1)


def get_table_names(sqlite_conn):
    """Get all table names from SQLite."""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    return tables


def get_table_schema(sqlite_conn, table_name):
    """Get column information for a table."""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = []
    for row in cursor.fetchall():
        col_name = row[1]
        col_type = row[2].upper()
        columns.append((col_name, col_type))
    return columns


def sqlite_to_postgres_type(sqlite_type):
    """Convert SQLite type to PostgreSQL type."""
    type_map = {
        "INTEGER": "INTEGER",
        "TEXT": "TEXT",
        "REAL": "DOUBLE PRECISION",
        "FLOAT": "DOUBLE PRECISION",
        "BLOB": "BYTEA",
        "BOOLEAN": "BOOLEAN",
        "DATETIME": "TIMESTAMP",
        "VARCHAR": "VARCHAR",
        "STRING": "TEXT"
    }
    
    # Handle VARCHAR(n)
    if "VARCHAR" in sqlite_type:
        return sqlite_type.replace("VARCHAR", "VARCHAR")
    
    for sqlite_t, postgres_t in type_map.items():
        if sqlite_t in sqlite_type:
            return postgres_t
    
    return "TEXT"  # Default fallback


def create_postgres_tables(pg_conn, sqlite_conn):
    """Create tables in PostgreSQL based on SQLite schema."""
    cursor = pg_conn.cursor()
    
    # Define table creation order (respecting foreign keys)
    # Tables with no foreign keys first
    table_order = [
        'users',
        'verification_codes',
        'fabric_vendors',
        'notion_vendors',
        'fabrics',
        'notions',
        'labor_operations',
        'cleaning_costs',
        'size_variants',
        'size_ranges',
        'colors',
        'variables',
        'global_settings',
        'styles',
        'style_fabrics',
        'style_notions',
        'style_labor',
        'style_colors',
        'style_variables',
        'style_images'
    ]
    
    # Get actual tables from SQLite
    actual_tables = get_table_names(sqlite_conn)
    
    # Create tables in order
    for table_name in table_order:
        if table_name not in actual_tables:
            print(f"  Skipping {table_name} (not in SQLite)")
            continue
        
        columns = get_table_schema(sqlite_conn, table_name)
        
        # Build CREATE TABLE statement
        col_defs = []
        for col_name, col_type in columns:
            pg_type = sqlite_to_postgres_type(col_type)
            
            # Handle primary key
            if col_name == 'id':
                col_defs.append(f"{col_name} SERIAL PRIMARY KEY")
            else:
                col_defs.append(f"{col_name} {pg_type}")
        
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)})"
        
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            cursor.execute(create_sql)
            print(f"  Created table: {table_name}")
        except psycopg2.Error as e:
            print(f"  ERROR creating {table_name}: {e}")
    
    pg_conn.commit()


def migrate_table_data(sqlite_conn, pg_conn, table_name):
    """Migrate data from SQLite table to PostgreSQL."""
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Get data from SQLite
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"  {table_name}: No data to migrate")
        return 0
    
    # Get column names
    columns = [description[0] for description in sqlite_cursor.description]
    
    # Prepare INSERT statement
    placeholders = ', '.join(['%s'] * len(columns))
    col_names = ', '.join(columns)
    insert_sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
    
    # Insert data
    try:
        for row in rows:
            # Convert None values and handle special types
            processed_row = []
            for val in row:
                if val is None:
                    processed_row.append(None)
                elif isinstance(val, bytes):
                    processed_row.append(val)
                else:
                    processed_row.append(val)
            
            pg_cursor.execute(insert_sql, processed_row)
        
        pg_conn.commit()
        
        # Reset sequence for tables with id column
        if 'id' in columns:
            pg_cursor.execute(f"""
                SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), 
                              COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1, false)
            """)
            pg_conn.commit()
        
        print(f"  {table_name}: Migrated {len(rows)} rows")
        return len(rows)
        
    except psycopg2.Error as e:
        print(f"  ERROR migrating {table_name}: {e}")
        pg_conn.rollback()
        return 0


def migrate_all_data(sqlite_conn, pg_conn):
    """Migrate all tables."""
    # Migration order (respecting foreign keys)
    table_order = [
        'users',
        'verification_codes',
        'fabric_vendors',
        'notion_vendors',
        'fabrics',
        'notions',
        'labor_operations',
        'cleaning_costs',
        'size_variants',
        'size_ranges',
        'colors',
        'variables',
        'global_settings',
        'styles',
        'style_fabrics',
        'style_notions',
        'style_labor',
        'style_colors',
        'style_variables',
        'style_images'
    ]
    
    actual_tables = get_table_names(sqlite_conn)
    total_rows = 0
    
    for table_name in table_order:
        if table_name in actual_tables:
            total_rows += migrate_table_data(sqlite_conn, pg_conn, table_name)
    
    # Migrate any remaining tables not in our order
    for table_name in actual_tables:
        if table_name not in table_order and table_name != 'alembic_version':
            total_rows += migrate_table_data(sqlite_conn, pg_conn, table_name)
    
    return total_rows


def verify_migration(sqlite_conn, pg_conn):
    """Verify migration was successful."""
    print("\n" + "="*50)
    print("VERIFICATION")
    print("="*50)
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    tables = get_table_names(sqlite_conn)
    all_match = True
    
    for table_name in tables:
        if table_name == 'alembic_version':
            continue
            
        # Count in SQLite
        sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        sqlite_count = sqlite_cursor.fetchone()[0]
        
        # Count in PostgreSQL
        try:
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            pg_count = pg_cursor.fetchone()[0]
            
            status = "OK" if sqlite_count == pg_count else "MISMATCH"
            if sqlite_count != pg_count:
                all_match = False
            
            print(f"  {table_name}: SQLite={sqlite_count}, PostgreSQL={pg_count} [{status}]")
        except psycopg2.Error:
            print(f"  {table_name}: SQLite={sqlite_count}, PostgreSQL=TABLE NOT FOUND [ERROR]")
            all_match = False
    
    return all_match


def main():
    """Main migration function."""
    print("="*60)
    print("J.A. UNIFORMS - SQLite to PostgreSQL Migration")
    print("="*60)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to databases
    print("\n[1/4] Connecting to databases...")
    sqlite_conn = get_sqlite_connection()
    pg_conn = get_postgres_connection()
    print("  SQLite: Connected")
    print("  PostgreSQL: Connected")
    
    # Create tables
    print("\n[2/4] Creating PostgreSQL tables...")
    create_postgres_tables(pg_conn, sqlite_conn)
    
    # Migrate data
    print("\n[3/4] Migrating data...")
    total_rows = migrate_all_data(sqlite_conn, pg_conn)
    
    # Verify
    print("\n[4/4] Verifying migration...")
    success = verify_migration(sqlite_conn, pg_conn)
    
    # Summary
    print("\n" + "="*60)
    print("MIGRATION COMPLETE")
    print("="*60)
    print(f"Total rows migrated: {total_rows}")
    print(f"Status: {'SUCCESS' if success else 'COMPLETED WITH WARNINGS'}")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print("\n" + "-"*60)
        print("NEXT STEPS:")
        print("-"*60)
        print("1. Update your .env file with PostgreSQL connection:")
        print(f"   DATABASE_URL=postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}")
        print("\n2. Restart your application")
        print("\n3. Test all functionality before removing SQLite backup")
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()


if __name__ == "__main__":
    main()
