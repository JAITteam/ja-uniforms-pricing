# Excel Import Guide for JA Uniforms

## Overview

This guide explains how to import your existing uniform data from Excel spreadsheets into the JA Uniforms system.

## Import Order

You must import data in this specific order:
1. **Vendors** (Fabric and Notion suppliers)
2. **Products** (Fabrics and Notions)
3. **Styles** (Uniform styles with Bill of Materials)

## Step-by-Step Instructions

### Step 1: Import Vendors

#### Fabric Vendors
1. Download the vendors template from the Import page
2. Your Excel should have these columns:
   - **Name**: Vendor company name (e.g., "CARR TEXTILES")
   - **Vendor Code**: Unique code (e.g., "V100", "V101")

Example:
| Name | Vendor Code |
|------|-------------|
| CARR TEXTILES | V100 |
| ABC FABRICS | V101 |

#### Notion Vendors
Use the same template format:
| Name | Vendor Code |
|------|-------------|
| WAWAK | N100 |
| BUTTON WORLD | N101 |

### Step 2: Import Products

#### Fabrics
1. Download the fabrics template
2. Required columns:
   - **Name**: Fabric name/description
   - **Fabric Code**: Optional SKU/code
   - **Cost Per Yard**: Price in dollars
   - **Color**: Optional color description
   - **Vendor Code**: Must match an existing fabric vendor

Example:
| Name | Fabric Code | Cost Per Yard | Color | Vendor Code |
|------|-------------|---------------|--------|-------------|
| XANADU | 3202 | 6.00 | TEAL | V100 |
| COTTON BLEND | CB100 | 4.50 | WHITE | V100 |

#### Notions
1. Download the notions template
2. Required columns:
   - **Name**: Notion description
   - **Cost Per Unit**: Price per unit
   - **Unit Type**: "each", "dozen", "gross", etc.
   - **Vendor Code**: Must match an existing notion vendor

Example:
| Name | Cost Per Unit | Unit Type | Vendor Code |
|------|---------------|-----------|-------------|
| 18L SPORT BUTTON | 0.04 | each | N100 |
| 14" ZIPPER | 0.75 | each | N100 |

### Step 3: Import Styles

This is the most complex import. Download the styles template which includes:

#### Basic Style Information
- **Vendor Style**: Unique identifier (e.g., "21324-3202")
- **Style Name**: Full description
- **Gender**: MENS, LADIES, or UNISEX
- **Garment Type**: SS TOP/SS DRESS, APRON, VEST, etc.
- **Size Range**: e.g., "XS-4XL"
- **Base Margin %**: Profit margin (default 60)
- **Avg Label Cost**: Label cost in dollars (default 0.20)
- **Notes**: Optional notes

#### Fabric Requirements (up to 5 fabrics per style)
- **Fabric 1 Name**: Must match existing fabric name exactly
- **Fabric 1 Code**: Optional, helps identify specific fabric
- **Fabric 1 Yards**: Yards required
- (Repeat for Fabric 2, 3, 4, 5 as needed)

#### Notion Requirements (up to 10 notions per style)
- **Notion 1 Name**: Must match existing notion name exactly
- **Notion 1 Qty**: Quantity required
- (Repeat for Notion 2-10 as needed)

#### Labor Requirements
- **Sewing Hours**: Hours required for sewing
- **Fusion Qty**: Number of fusion operations (usually 1)
- **Marker Cut Qty**: Number of marker/cut operations (usually 1)
- **Button Snap Qty**: Number of buttons/snaps/grommets

Example row:
| Vendor Style | Style Name | Gender | Garment Type | Size Range | Base Margin % | Avg Label Cost | Notes | Fabric 1 Name | Fabric 1 Code | Fabric 1 Yards | Notion 1 Name | Notion 1 Qty | Sewing Hours | Fusion Qty | Marker Cut Qty | Button Snap Qty |
|--------------|------------|--------|--------------|------------|---------------|----------------|-------|---------------|---------------|----------------|---------------|--------------|--------------|------------|----------------|-----------------|
| 21324-3202 | SHIRT, MENS LARGO CAMP W/ SLEEVE TAB | MENS | SS TOP/SS DRESS | XS-4XL | 60 | 0.20 | Summer collection | XANADU | 3202 | 1.5 | 18L SPORT BUTTON | 7 | 0.55 | 1 | 1 | 7 |

## Common Issues and Solutions

### Issue: "Vendor not found"
**Solution**: Make sure the vendor code in your product import exactly matches a vendor you've already imported.

### Issue: "Fabric/Notion not found" when importing styles
**Solution**: The fabric or notion name in your style import must exactly match an existing item. Check for:
- Extra spaces
- Different capitalization
- Typos

### Issue: Import seems successful but data doesn't appear
**Solution**: Check if items were skipped as duplicates. The system won't overwrite existing vendor styles.

## Best Practices

1. **Test with small datasets first**: Import a few records to ensure your format is correct
2. **Use consistent naming**: Keep fabric and notion names consistent across all imports
3. **Clean your data**: Remove extra spaces, standardize capitalization
4. **Keep backups**: Save your original Excel files before importing
5. **Check for duplicates**: The system will skip duplicate vendor styles

## Updating Existing Data

- To update existing fabric/notion prices: Import with the same fabric code or name
- To add new styles: Ensure the vendor style code is unique
- The system will warn you about duplicates rather than overwriting

## Labor Operations Reference

The system has these pre-defined labor operations:
- **FUSION**: Flat rate $1.50
- **Marker+Cut**: Flat rate $1.50
- **Sewing**: Hourly rate $19.32/hour
- **Button/Snap/Grommet**: Per piece $0.15

## Cleaning Costs

Cleaning costs are automatically added based on garment type:
- **SS TOP/SS DRESS**: $1.60
- **APRON**: $0.96
- **VEST**: $1.28

## Need Help?

1. Start with the downloadable templates
2. Import in the correct order: Vendors → Products → Styles
3. Check error messages carefully - they indicate which row had issues
4. For large imports, consider breaking into smaller batches