import pandas as pd
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from database import db
from models import (
    FabricVendor, NotionVendor, Fabric, Notion,
    Style, StyleFabric, StyleNotion, StyleLabor,
    LaborOperation, CleaningCost
)

class ExcelImporter:
    """Handles importing data from Excel files into the database"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        
    def validate_excel_file(self, file):
        """Validate that the uploaded file is a valid Excel file"""
        if not file:
            return False, "No file provided"
            
        filename = secure_filename(file.filename)
        if not filename.endswith(('.xlsx', '.xls')):
            return False, "File must be an Excel file (.xlsx or .xls)"
            
        return True, filename
    
    def import_vendors(self, file_path, vendor_type='fabric'):
        """Import vendors from Excel file
        Expected columns: Name, Vendor Code
        """
        self.errors = []
        self.success_count = 0
        
        try:
            df = pd.read_excel(file_path)
            required_columns = ['Name', 'Vendor Code']
            
            # Validate columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                self.errors.append(f"Missing columns: {', '.join(missing_cols)}")
                return False
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row['Name']) or pd.isna(row['Vendor Code']):
                        continue
                    
                    # Check if vendor already exists
                    model = FabricVendor if vendor_type == 'fabric' else NotionVendor
                    existing = model.query.filter_by(vendor_code=str(row['Vendor Code'])).first()
                    
                    if existing:
                        self.warnings.append(f"Row {index + 2}: Vendor {row['Vendor Code']} already exists, skipping")
                        continue
                    
                    # Create new vendor
                    vendor = model(
                        name=str(row['Name']).strip(),
                        vendor_code=str(row['Vendor Code']).strip()
                    )
                    db.session.add(vendor)
                    self.success_count += 1
                    
                except Exception as e:
                    self.errors.append(f"Row {index + 2}: {str(e)}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            self.errors.append(f"File error: {str(e)}")
            return False
    
    def import_fabrics(self, file_path):
        """Import fabrics from Excel file
        Expected columns: Name, Fabric Code, Cost Per Yard, Color, Vendor Code
        """
        self.errors = []
        self.success_count = 0
        
        try:
            df = pd.read_excel(file_path)
            required_columns = ['Name', 'Cost Per Yard', 'Vendor Code']
            
            # Validate columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                self.errors.append(f"Missing columns: {', '.join(missing_cols)}")
                return False
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row['Name']) or pd.isna(row['Cost Per Yard']):
                        continue
                    
                    # Find vendor
                    vendor = FabricVendor.query.filter_by(
                        vendor_code=str(row['Vendor Code']).strip()
                    ).first()
                    
                    if not vendor:
                        self.errors.append(f"Row {index + 2}: Vendor {row['Vendor Code']} not found")
                        continue
                    
                    # Check if fabric already exists
                    fabric_code = str(row.get('Fabric Code', '')).strip() if not pd.isna(row.get('Fabric Code')) else None
                    if fabric_code:
                        existing = Fabric.query.filter_by(
                            fabric_code=fabric_code,
                            fabric_vendor_id=vendor.id
                        ).first()
                        if existing:
                            self.warnings.append(f"Row {index + 2}: Fabric {fabric_code} already exists, updating")
                            existing.cost_per_yard = float(row['Cost Per Yard'])
                            existing.name = str(row['Name']).strip()
                            if 'Color' in row and not pd.isna(row['Color']):
                                existing.color = str(row['Color']).strip()
                            continue
                    
                    # Create new fabric
                    fabric = Fabric(
                        name=str(row['Name']).strip(),
                        fabric_code=fabric_code,
                        cost_per_yard=float(row['Cost Per Yard']),
                        color=str(row.get('Color', '')).strip() if not pd.isna(row.get('Color')) else None,
                        fabric_vendor_id=vendor.id
                    )
                    db.session.add(fabric)
                    self.success_count += 1
                    
                except Exception as e:
                    self.errors.append(f"Row {index + 2}: {str(e)}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            self.errors.append(f"File error: {str(e)}")
            return False
    
    def import_notions(self, file_path):
        """Import notions from Excel file
        Expected columns: Name, Cost Per Unit, Unit Type, Vendor Code
        """
        self.errors = []
        self.success_count = 0
        
        try:
            df = pd.read_excel(file_path)
            required_columns = ['Name', 'Cost Per Unit', 'Vendor Code']
            
            # Validate columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                self.errors.append(f"Missing columns: {', '.join(missing_cols)}")
                return False
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row['Name']) or pd.isna(row['Cost Per Unit']):
                        continue
                    
                    # Find vendor
                    vendor = NotionVendor.query.filter_by(
                        vendor_code=str(row['Vendor Code']).strip()
                    ).first()
                    
                    if not vendor:
                        self.errors.append(f"Row {index + 2}: Vendor {row['Vendor Code']} not found")
                        continue
                    
                    # Create new notion
                    notion = Notion(
                        name=str(row['Name']).strip(),
                        cost_per_unit=float(row['Cost Per Unit']),
                        unit_type=str(row.get('Unit Type', 'each')).strip() if not pd.isna(row.get('Unit Type')) else 'each',
                        notion_vendor_id=vendor.id
                    )
                    db.session.add(notion)
                    self.success_count += 1
                    
                except Exception as e:
                    self.errors.append(f"Row {index + 2}: {str(e)}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            self.errors.append(f"File error: {str(e)}")
            return False
    
    def import_styles(self, file_path):
        """Import styles from Excel file with their BOMs
        Expected columns: Vendor Style, Style Name, Gender, Garment Type, Size Range, 
                         Base Margin %, Avg Label Cost, Notes,
                         Fabric 1 Name, Fabric 1 Code, Fabric 1 Yards,
                         Fabric 2 Name, Fabric 2 Code, Fabric 2 Yards, ...,
                         Notion 1 Name, Notion 1 Qty,
                         Notion 2 Name, Notion 2 Qty, ...,
                         Sewing Hours, Fusion Qty, Marker Cut Qty, Button Snap Qty
        """
        self.errors = []
        self.success_count = 0
        
        try:
            df = pd.read_excel(file_path)
            required_columns = ['Vendor Style', 'Style Name']
            
            # Validate columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                self.errors.append(f"Missing columns: {', '.join(missing_cols)}")
                return False
            
            # Process each row
            for index, row in df.iterrows():
                try:
                    # Skip empty rows
                    if pd.isna(row['Vendor Style']) or pd.isna(row['Style Name']):
                        continue
                    
                    vendor_style = str(row['Vendor Style']).strip()
                    
                    # Check if style already exists
                    existing = Style.query.filter_by(vendor_style=vendor_style).first()
                    if existing:
                        self.warnings.append(f"Row {index + 2}: Style {vendor_style} already exists, skipping")
                        continue
                    
                    # Parse vendor style
                    parts = vendor_style.split('-')
                    base_item = parts[0] if len(parts) > 0 else vendor_style
                    variant = parts[1] if len(parts) > 1 else ''
                    
                    # Create style
                    style = Style(
                        vendor_style=vendor_style,
                        base_item_number=base_item,
                        variant_code=variant,
                        style_name=str(row['Style Name']).strip(),
                        gender=str(row.get('Gender', '')).strip() if not pd.isna(row.get('Gender')) else None,
                        garment_type=str(row.get('Garment Type', '')).strip() if not pd.isna(row.get('Garment Type')) else None,
                        size_range=str(row.get('Size Range', 'XS-4XL')).strip() if not pd.isna(row.get('Size Range')) else 'XS-4XL',
                        base_margin_percent=float(row.get('Base Margin %', 60)) if not pd.isna(row.get('Base Margin %')) else 60.0,
                        avg_label_cost=float(row.get('Avg Label Cost', 0.20)) if not pd.isna(row.get('Avg Label Cost')) else 0.20,
                        notes=str(row.get('Notes', '')).strip() if not pd.isna(row.get('Notes')) else None
                    )
                    db.session.add(style)
                    db.session.flush()  # Get the style ID
                    
                    # Process fabrics (up to 5)
                    for i in range(1, 6):
                        fabric_name_col = f'Fabric {i} Name'
                        fabric_code_col = f'Fabric {i} Code'
                        fabric_yards_col = f'Fabric {i} Yards'
                        
                        if fabric_name_col in row and not pd.isna(row[fabric_name_col]):
                            # Find fabric
                            fabric_name = str(row[fabric_name_col]).strip()
                            fabric_code = str(row.get(fabric_code_col, '')).strip() if fabric_code_col in row and not pd.isna(row.get(fabric_code_col)) else None
                            
                            fabric = None
                            if fabric_code:
                                fabric = Fabric.query.filter_by(fabric_code=fabric_code).first()
                            if not fabric:
                                fabric = Fabric.query.filter_by(name=fabric_name).first()
                            
                            if fabric and fabric_yards_col in row and not pd.isna(row[fabric_yards_col]):
                                style_fabric = StyleFabric(
                                    style_id=style.id,
                                    fabric_id=fabric.id,
                                    yards_required=float(row[fabric_yards_col]),
                                    is_primary=(i == 1)
                                )
                                db.session.add(style_fabric)
                            elif not fabric:
                                self.warnings.append(f"Row {index + 2}: Fabric '{fabric_name}' not found")
                    
                    # Process notions (up to 10)
                    for i in range(1, 11):
                        notion_name_col = f'Notion {i} Name'
                        notion_qty_col = f'Notion {i} Qty'
                        
                        if notion_name_col in row and not pd.isna(row[notion_name_col]):
                            notion_name = str(row[notion_name_col]).strip()
                            notion = Notion.query.filter_by(name=notion_name).first()
                            
                            if notion and notion_qty_col in row and not pd.isna(row[notion_qty_col]):
                                style_notion = StyleNotion(
                                    style_id=style.id,
                                    notion_id=notion.id,
                                    quantity_required=int(row[notion_qty_col])
                                )
                                db.session.add(style_notion)
                            elif not notion:
                                self.warnings.append(f"Row {index + 2}: Notion '{notion_name}' not found")
                    
                    # Process labor operations
                    labor_mappings = [
                        ('Sewing Hours', 'Sewing', 'time_hours'),
                        ('Fusion Qty', 'FUSION', 'quantity'),
                        ('Marker Cut Qty', 'Marker+Cut', 'quantity'),
                        ('Button Snap Qty', 'Button/Snap/Grommet', 'quantity')
                    ]
                    
                    for col_name, op_name, field_type in labor_mappings:
                        if col_name in row and not pd.isna(row[col_name]):
                            labor_op = LaborOperation.query.filter_by(name=op_name).first()
                            if labor_op:
                                style_labor = StyleLabor(
                                    style_id=style.id,
                                    labor_operation_id=labor_op.id
                                )
                                if field_type == 'time_hours':
                                    style_labor.time_hours = float(row[col_name])
                                else:
                                    style_labor.quantity = int(row[col_name])
                                db.session.add(style_labor)
                    
                    self.success_count += 1
                    
                except Exception as e:
                    self.errors.append(f"Row {index + 2}: {str(e)}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            self.errors.append(f"File error: {str(e)}")
            return False
    
    def generate_template(self, template_type):
        """Generate Excel template for different import types"""
        templates = {
            'vendors': {
                'columns': ['Name', 'Vendor Code'],
                'sample_data': [
                    ['CARR TEXTILES', 'V100'],
                    ['WAWAK', 'N100']
                ]
            },
            'fabrics': {
                'columns': ['Name', 'Fabric Code', 'Cost Per Yard', 'Color', 'Vendor Code'],
                'sample_data': [
                    ['XANADU', '3202', 6.00, 'TEAL', 'V100'],
                    ['COTTON BLEND', 'CB100', 4.50, 'WHITE', 'V100']
                ]
            },
            'notions': {
                'columns': ['Name', 'Cost Per Unit', 'Unit Type', 'Vendor Code'],
                'sample_data': [
                    ['18L SPORT BUTTON', 0.04, 'each', 'N100'],
                    ['14" ZIPPER', 0.75, 'each', 'N100']
                ]
            },
            'styles': {
                'columns': [
                    'Vendor Style', 'Style Name', 'Gender', 'Garment Type', 'Size Range',
                    'Base Margin %', 'Avg Label Cost', 'Notes',
                    'Fabric 1 Name', 'Fabric 1 Code', 'Fabric 1 Yards',
                    'Fabric 2 Name', 'Fabric 2 Code', 'Fabric 2 Yards',
                    'Notion 1 Name', 'Notion 1 Qty',
                    'Notion 2 Name', 'Notion 2 Qty',
                    'Sewing Hours', 'Fusion Qty', 'Marker Cut Qty', 'Button Snap Qty'
                ],
                'sample_data': [
                    [
                        '21324-3202', 'SHIRT, MENS LARGO CAMP W/ SLEEVE TAB', 'MENS', 
                        'SS TOP/SS DRESS', 'XS-4XL', 60, 0.20, 'Summer collection',
                        'XANADU', '3202', 1.5, '', '', '',
                        '18L SPORT BUTTON', 7, '', '',
                        0.55, 1, 1, 7
                    ]
                ]
            }
        }
        
        if template_type not in templates:
            return None
            
        template = templates[template_type]
        df = pd.DataFrame(template['sample_data'], columns=template['columns'])
        
        # Create file in memory
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Import Template', index=False)
            
            # Add instructions sheet
            instructions = pd.DataFrame({
                'Instructions': [
                    f'This is the template for importing {template_type}.',
                    'Fill in your data following the same format as the sample row(s).',
                    'Do not change the column headers.',
                    'Delete the sample data rows before importing.',
                    '',
                    'Column descriptions:',
                ] + self._get_column_descriptions(template_type)
            })
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        output.seek(0)
        return output
    
    def _get_column_descriptions(self, template_type):
        """Get column descriptions for each template type"""
        descriptions = {
            'vendors': [
                'Name: The vendor company name',
                'Vendor Code: Unique code for the vendor (e.g., V100 for fabric vendors, N100 for notion vendors)'
            ],
            'fabrics': [
                'Name: Fabric name/description',
                'Fabric Code: Optional fabric code/SKU',
                'Cost Per Yard: Price per yard in dollars',
                'Color: Optional color description',
                'Vendor Code: Must match an existing fabric vendor code'
            ],
            'notions': [
                'Name: Notion name/description',
                'Cost Per Unit: Price per unit in dollars',
                'Unit Type: Unit of measurement (each, dozen, gross, etc.)',
                'Vendor Code: Must match an existing notion vendor code'
            ],
            'styles': [
                'Vendor Style: Unique style identifier (e.g., 21324-3202)',
                'Style Name: Full style description',
                'Gender: MENS, LADIES, or UNISEX',
                'Garment Type: Type of garment (e.g., SS TOP/SS DRESS, APRON, VEST)',
                'Size Range: Available sizes (e.g., XS-4XL)',
                'Base Margin %: Profit margin percentage (default 60)',
                'Avg Label Cost: Average label cost in dollars (default 0.20)',
                'Notes: Optional notes',
                'Fabric columns: Name must match existing fabric, Code is optional, Yards is required',
                'Notion columns: Name must match existing notion, Qty is the quantity needed',
                'Labor columns: Hours or quantities for each operation type'
            ]
        }
        
        return descriptions.get(template_type, [])