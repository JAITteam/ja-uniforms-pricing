# J.A Uniforms Pricing Tool

Internal web application for uniform pricing and cost management.

## Setup
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run app: `python app.py`

## Team
- Developer 1: [Your Name]
- Developer 2: [Friend's Name]

## Status
🚧 In Development

## Excel Import Format

Upload an `.xlsx` file at `/import-excel`. The workbook may include the following sheets (names are case-insensitive; spaces allowed). Columns listed are recommended; importer accepts common variants in parentheses.

- FabricVendors
  - name (Name)
  - vendor_code (Vendor Code, code)

- NotionVendors
  - name (Name)
  - vendor_code (Vendor Code, code)

- Fabrics
  - name (Name)
  - fabric_code (Fabric Code, code) [optional]
  - cost_per_yard (Cost Per Yard, cost)
  - color (Color) [optional]
  - fabric_vendor_code (vendor_code, Vendor Code) [optional]
  - fabric_vendor_name (vendor_name, Vendor) [optional]

- Notions
  - name (Name)
  - cost_per_unit (Cost Per Unit, cost)
  - unit_type (Unit Type, unit) [default: each]
  - notion_vendor_code (vendor_code, Vendor Code) [optional]
  - notion_vendor_name (vendor_name, Vendor) [optional]

- LaborOperations
  - name (Name)
  - cost_type (Cost Type) one of: flat_rate, hourly, per_piece
  - fixed_cost (Fixed Cost) [for flat_rate]
  - cost_per_hour (Cost Per Hour) [for hourly]
  - cost_per_piece (Cost Per Piece) [for per_piece]
  - is_active (Active) [true/false]

- CleaningCosts
  - garment_type (Garment Type)
  - fixed_cost (Fixed Cost)
  - avg_minutes (Avg Minutes, minutes)

- SizeVariants
  - size_name (Size, size)
  - size_category (Category, category) [regular/extended]
  - price_multiplier (Multiplier, multiplier)

- Styles
  - vendor_style (Vendor Style, code)
  - base_item_number (Base Item Number)
  - variant_code (Variant Code)
  - style_name (Style Name, name)
  - gender (Gender)
  - garment_type (Garment Type)
  - size_range (Size Range)
  - base_margin_percent (Base Margin %, margin)
  - avg_label_cost (Avg Label Cost, label_cost)
  - notes (Notes)

- StyleFabrics
  - vendor_style (Vendor Style)
  - fabric_name (Fabric Name) and/or fabric_code (Fabric Code)
  - color (Color) [helps resolve fabric]
  - yards_required (Yards Required, yards)
  - is_primary (Primary) [true/false]
  - notes (Notes)

- StyleNotions
  - vendor_style (Vendor Style)
  - notion_name (Notion Name, name)
  - quantity_required (Quantity Required, qty)
  - notes (Notes)

- StyleLabor
  - vendor_style (Vendor Style)
  - labor_operation (Labor Operation, operation)
  - time_hours (Time Hours, hours) [for hourly]
  - quantity (Quantity, qty) [for flat_rate/per_piece]
  - notes (Notes)

Notes
- The importer performs upserts (update if found, otherwise create), committing after each sheet.
- Sheet names are matched case-insensitively; spaces are ignored.
- Minimal required fields: see each section; missing rows are skipped and reported.