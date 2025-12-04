#!/usr/bin/env python3
"""
Export data from SQLite to JSON format for PostgreSQL migration
"""
import json
import sqlite3
from datetime import datetime

def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def export_table(cursor, table_name):
    """Export a single table to list of dictionaries"""
    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    
    data = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(columns):
            row_dict[col] = row[i]
        data.append(row_dict)
    
    return data

def main():
    print("🔄 Starting SQLite data export...")
    
    # Connect to SQLite database
    conn = sqlite3.connect('uniforms.db')
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'alembic%';")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 Found {len(tables)} tables to export")
    
    # Export all tables
    export_data = {}
    for table in tables:
        try:
            print(f"  ✓ Exporting {table}...", end=' ')
            export_data[table] = export_table(cursor, table)
            print(f"({len(export_data[table])} rows)")
        except Exception as e:
            print(f"  ✗ Error exporting {table}: {e}")
    
    # Save to JSON file
    output_file = 'sqlite_export.json'
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=serialize_datetime)
    
    conn.close()
    
    print(f"\n✅ Export complete! Data saved to {output_file}")
    print(f"📦 Total tables exported: {len(export_data)}")
    
    # Print summary
    print("\n📋 Export Summary:")
    for table, rows in export_data.items():
        print(f"  • {table}: {len(rows)} rows")

if __name__ == '__main__':
    main()
