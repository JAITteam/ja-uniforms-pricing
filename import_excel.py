from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from database import db
from models import (
    FabricVendor,
    NotionVendor,
    Fabric,
    Notion,
    LaborOperation,
    CleaningCost,
    SizeVariant,
    Style,
    StyleFabric,
    StyleNotion,
    StyleLabor,
)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _as_str(value: Any) -> Optional[str]:
    if _is_missing(value):
        return None
    return str(value).strip()


def _as_float(value: Any) -> Optional[float]:
    if _is_missing(value):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _as_int(value: Any) -> Optional[int]:
    if _is_missing(value):
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def _as_bool(value: Any) -> Optional[bool]:
    if _is_missing(value):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return None


def _summ(summary: Dict[str, Any], sheet: str, created: int = 0, updated: int = 0, skipped: int = 0, errors: Optional[List[str]] = None) -> None:
    if errors is None:
        errors = []
    summary[sheet] = {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


def _get_or_create_fabric_vendor(name: Optional[str], vendor_code: Optional[str]) -> Optional[FabricVendor]:
    if not name and not vendor_code:
        return None
    query = FabricVendor.query
    if vendor_code:
        instance = query.filter_by(vendor_code=vendor_code).first()
        if instance:
            if name and instance.name != name:
                instance.name = name
            return instance
    if name:
        instance = query.filter_by(name=name).first()
        if instance:
            if vendor_code and instance.vendor_code != vendor_code:
                instance.vendor_code = vendor_code
            return instance
    instance = FabricVendor(name=name or vendor_code or "Unknown", vendor_code=vendor_code)
    db.session.add(instance)
    db.session.flush()
    return instance


def _get_or_create_notion_vendor(name: Optional[str], vendor_code: Optional[str]) -> Optional[NotionVendor]:
    if not name and not vendor_code:
        return None
    query = NotionVendor.query
    if vendor_code:
        instance = query.filter_by(vendor_code=vendor_code).first()
        if instance:
            if name and instance.name != name:
                instance.name = name
            return instance
    if name:
        instance = query.filter_by(name=name).first()
        if instance:
            if vendor_code and instance.vendor_code != vendor_code:
                instance.vendor_code = vendor_code
            return instance
    instance = NotionVendor(name=name or vendor_code or "Unknown", vendor_code=vendor_code)
    db.session.add(instance)
    db.session.flush()
    return instance


def _import_fabric_vendors(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        name = _as_str(row.get("name")) or _as_str(row.get("Name"))
        vendor_code = _as_str(row.get("vendor_code")) or _as_str(row.get("Vendor Code")) or _as_str(row.get("code"))
        if not name and not vendor_code:
            skipped += 1
            continue
        try:
            existing = None
            if vendor_code:
                existing = FabricVendor.query.filter_by(vendor_code=vendor_code).first()
            if not existing and name:
                existing = FabricVendor.query.filter_by(name=name).first()
            if existing:
                if name and existing.name != name:
                    existing.name = name
                if vendor_code and existing.vendor_code != vendor_code:
                    existing.vendor_code = vendor_code
                updated += 1
            else:
                db.session.add(FabricVendor(name=name or "Unknown", vendor_code=vendor_code))
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _import_notion_vendors(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        name = _as_str(row.get("name")) or _as_str(row.get("Name"))
        vendor_code = _as_str(row.get("vendor_code")) or _as_str(row.get("Vendor Code")) or _as_str(row.get("code"))
        if not name and not vendor_code:
            skipped += 1
            continue
        try:
            existing = None
            if vendor_code:
                existing = NotionVendor.query.filter_by(vendor_code=vendor_code).first()
            if not existing and name:
                existing = NotionVendor.query.filter_by(name=name).first()
            if existing:
                if name and existing.name != name:
                    existing.name = name
                if vendor_code and existing.vendor_code != vendor_code:
                    existing.vendor_code = vendor_code
                updated += 1
            else:
                db.session.add(NotionVendor(name=name or "Unknown", vendor_code=vendor_code))
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _import_fabrics(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        name = _as_str(row.get("name")) or _as_str(row.get("Name"))
        fabric_code = _as_str(row.get("fabric_code")) or _as_str(row.get("Fabric Code")) or _as_str(row.get("code"))
        cost_per_yard = _as_float(row.get("cost_per_yard") or row.get("Cost Per Yard") or row.get("cost"))
        color = _as_str(row.get("color") or row.get("Color"))
        vendor_code = _as_str(row.get("fabric_vendor_code") or row.get("vendor_code") or row.get("Vendor Code"))
        vendor_name = _as_str(row.get("fabric_vendor_name") or row.get("vendor_name") or row.get("Vendor"))
        if not name or cost_per_yard is None:
            skipped += 1
            continue
        try:
            vendor = _get_or_create_fabric_vendor(vendor_name, vendor_code)
            existing = None
            if fabric_code:
                existing = Fabric.query.filter_by(fabric_code=fabric_code).first()
            if not existing:
                existing = Fabric.query.filter_by(name=name, color=color).first()
            if existing:
                existing.name = name
                existing.fabric_code = fabric_code
                existing.cost_per_yard = cost_per_yard
                existing.color = color
                existing.fabric_vendor_id = vendor.id if vendor else None
                updated += 1
            else:
                db.session.add(
                    Fabric(
                        name=name,
                        fabric_code=fabric_code,
                        cost_per_yard=cost_per_yard,
                        color=color,
                        fabric_vendor_id=vendor.id if vendor else None,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _import_notions(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        name = _as_str(row.get("name")) or _as_str(row.get("Name"))
        cost_per_unit = _as_float(row.get("cost_per_unit") or row.get("Cost Per Unit") or row.get("cost"))
        unit_type = _as_str(row.get("unit_type") or row.get("Unit Type") or row.get("unit")) or "each"
        vendor_code = _as_str(row.get("notion_vendor_code") or row.get("vendor_code") or row.get("Vendor Code"))
        vendor_name = _as_str(row.get("notion_vendor_name") or row.get("vendor_name") or row.get("Vendor"))
        if not name or cost_per_unit is None:
            skipped += 1
            continue
        try:
            vendor = _get_or_create_notion_vendor(vendor_name, vendor_code)
            existing = Notion.query.filter_by(name=name).first()
            if existing:
                existing.cost_per_unit = cost_per_unit
                existing.unit_type = unit_type
                existing.notion_vendor_id = vendor.id if vendor else None
                updated += 1
            else:
                db.session.add(
                    Notion(
                        name=name,
                        cost_per_unit=cost_per_unit,
                        unit_type=unit_type,
                        notion_vendor_id=vendor.id if vendor else None,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _import_labor_operations(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        name = _as_str(row.get("name") or row.get("Name"))
        cost_type = _as_str(row.get("cost_type") or row.get("Cost Type"))
        fixed_cost = _as_float(row.get("fixed_cost") or row.get("Fixed Cost"))
        cost_per_hour = _as_float(row.get("cost_per_hour") or row.get("Cost Per Hour"))
        cost_per_piece = _as_float(row.get("cost_per_piece") or row.get("Cost Per Piece"))
        is_active = _as_bool(row.get("is_active") or row.get("Active"))
        if not name or not cost_type:
            skipped += 1
            continue
        try:
            existing = LaborOperation.query.filter_by(name=name).first()
            if existing:
                existing.cost_type = cost_type
                existing.fixed_cost = fixed_cost
                existing.cost_per_hour = cost_per_hour
                existing.cost_per_piece = cost_per_piece
                if is_active is not None:
                    existing.is_active = is_active
                updated += 1
            else:
                db.session.add(
                    LaborOperation(
                        name=name,
                        cost_type=cost_type,
                        fixed_cost=fixed_cost,
                        cost_per_hour=cost_per_hour,
                        cost_per_piece=cost_per_piece,
                        is_active=True if is_active is None else is_active,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _import_cleaning_costs(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        garment_type = _as_str(row.get("garment_type") or row.get("Garment Type"))
        fixed_cost = _as_float(row.get("fixed_cost") or row.get("Fixed Cost"))
        avg_minutes = _as_int(row.get("avg_minutes") or row.get("Avg Minutes") or row.get("minutes"))
        if not garment_type or fixed_cost is None or avg_minutes is None:
            skipped += 1
            continue
        try:
            existing = CleaningCost.query.filter_by(garment_type=garment_type).first()
            if existing:
                existing.fixed_cost = fixed_cost
                existing.avg_minutes = avg_minutes
                updated += 1
            else:
                db.session.add(CleaningCost(garment_type=garment_type, fixed_cost=fixed_cost, avg_minutes=avg_minutes))
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _import_size_variants(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        size_name = _as_str(row.get("size_name") or row.get("Size") or row.get("size"))
        size_category = _as_str(row.get("size_category") or row.get("Category") or row.get("category"))
        price_multiplier = _as_float(row.get("price_multiplier") or row.get("Multiplier") or row.get("multiplier"))
        if not size_name:
            skipped += 1
            continue
        try:
            existing = SizeVariant.query.filter_by(size_name=size_name).first()
            if existing:
                if size_category:
                    existing.size_category = size_category
                if price_multiplier is not None:
                    existing.price_multiplier = price_multiplier
                updated += 1
            else:
                db.session.add(
                    SizeVariant(
                        size_name=size_name,
                        size_category=size_category or "regular",
                        price_multiplier=1.0 if price_multiplier is None else price_multiplier,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _import_styles(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        vendor_style = _as_str(row.get("vendor_style") or row.get("Vendor Style") or row.get("code"))
        base_item_number = _as_str(row.get("base_item_number") or row.get("Base Item Number"))
        variant_code = _as_str(row.get("variant_code") or row.get("Variant Code"))
        style_name = _as_str(row.get("style_name") or row.get("Style Name") or row.get("name"))
        gender = _as_str(row.get("gender") or row.get("Gender"))
        garment_type = _as_str(row.get("garment_type") or row.get("Garment Type"))
        size_range = _as_str(row.get("size_range") or row.get("Size Range"))
        base_margin_percent = _as_float(row.get("base_margin_percent") or row.get("Base Margin %") or row.get("margin"))
        avg_label_cost = _as_float(row.get("avg_label_cost") or row.get("Avg Label Cost") or row.get("label_cost"))
        notes = _as_str(row.get("notes") or row.get("Notes"))
        if not vendor_style or not style_name:
            skipped += 1
            continue
        try:
            existing = Style.query.filter_by(vendor_style=vendor_style).first()
            if existing:
                existing.base_item_number = base_item_number
                existing.variant_code = variant_code
                existing.style_name = style_name
                existing.gender = gender
                existing.garment_type = garment_type
                existing.size_range = size_range
                if base_margin_percent is not None:
                    existing.base_margin_percent = base_margin_percent
                if avg_label_cost is not None:
                    existing.avg_label_cost = avg_label_cost
                existing.notes = notes
                updated += 1
            else:
                db.session.add(
                    Style(
                        vendor_style=vendor_style,
                        base_item_number=base_item_number,
                        variant_code=variant_code,
                        style_name=style_name,
                        gender=gender,
                        garment_type=garment_type,
                        size_range=size_range,
                        base_margin_percent=60.0 if base_margin_percent is None else base_margin_percent,
                        avg_label_cost=0.20 if avg_label_cost is None else avg_label_cost,
                        notes=notes,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _resolve_style(vendor_style: Optional[str]) -> Optional[Style]:
    if not vendor_style:
        return None
    return Style.query.filter_by(vendor_style=vendor_style).first()


def _resolve_fabric(name: Optional[str], fabric_code: Optional[str], color: Optional[str]) -> Optional[Fabric]:
    if fabric_code:
        inst = Fabric.query.filter_by(fabric_code=fabric_code).first()
        if inst:
            return inst
    if name and color:
        inst = Fabric.query.filter_by(name=name, color=color).first()
        if inst:
            return inst
    if name:
        inst = Fabric.query.filter_by(name=name).first()
        if inst:
            return inst
    return None


def _resolve_notion(name: Optional[str]) -> Optional[Notion]:
    if not name:
        return None
    return Notion.query.filter_by(name=name).first()


def _resolve_labor_operation(name: Optional[str]) -> Optional[LaborOperation]:
    if not name:
        return None
    return LaborOperation.query.filter_by(name=name).first()


def _import_style_fabrics(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        vendor_style = _as_str(row.get("vendor_style") or row.get("Vendor Style"))
        fabric_name = _as_str(row.get("fabric_name") or row.get("Fabric Name"))
        fabric_code = _as_str(row.get("fabric_code") or row.get("Fabric Code"))
        color = _as_str(row.get("color") or row.get("Color"))
        yards_required = _as_float(row.get("yards_required") or row.get("Yards Required") or row.get("yards"))
        is_primary = _as_bool(row.get("is_primary") or row.get("Primary"))
        notes = _as_str(row.get("notes") or row.get("Notes"))
        if not vendor_style or yards_required is None:
            skipped += 1
            continue
        try:
            style = _resolve_style(vendor_style)
            fabric = _resolve_fabric(fabric_name, fabric_code, color)
            if not style or not fabric:
                errors.append(f"Missing reference for style {vendor_style} or fabric {fabric_code or fabric_name}")
                skipped += 1
                continue
            existing = StyleFabric.query.filter_by(style_id=style.id, fabric_id=fabric.id).first()
            if existing:
                existing.yards_required = yards_required
                if is_primary is not None:
                    existing.is_primary = is_primary
                existing.notes = notes
                updated += 1
            else:
                db.session.add(
                    StyleFabric(
                        style_id=style.id,
                        fabric_id=fabric.id,
                        yards_required=yards_required,
                        is_primary=False if is_primary is None else is_primary,
                        notes=notes,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _import_style_notions(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        vendor_style = _as_str(row.get("vendor_style") or row.get("Vendor Style"))
        notion_name = _as_str(row.get("notion_name") or row.get("Notion Name") or row.get("name"))
        quantity_required = _as_int(row.get("quantity_required") or row.get("Quantity Required") or row.get("qty"))
        notes = _as_str(row.get("notes") or row.get("Notes"))
        if not vendor_style or not notion_name or quantity_required is None:
            skipped += 1
            continue
        try:
            style = _resolve_style(vendor_style)
            notion = _resolve_notion(notion_name)
            if not style or not notion:
                errors.append(f"Missing reference for style {vendor_style} or notion {notion_name}")
                skipped += 1
                continue
            existing = StyleNotion.query.filter_by(style_id=style.id, notion_id=notion.id).first()
            if existing:
                existing.quantity_required = quantity_required
                existing.notes = notes
                updated += 1
            else:
                db.session.add(
                    StyleNotion(
                        style_id=style.id,
                        notion_id=notion.id,
                        quantity_required=quantity_required,
                        notes=notes,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


def _import_style_labor(df: pd.DataFrame) -> Tuple[int, int, int, List[str]]:
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []
    for _, row in df.iterrows():
        vendor_style = _as_str(row.get("vendor_style") or row.get("Vendor Style"))
        labor_name = _as_str(row.get("labor_operation") or row.get("Labor Operation") or row.get("operation"))
        time_hours = _as_float(row.get("time_hours") or row.get("Time Hours") or row.get("hours"))
        quantity = _as_int(row.get("quantity") or row.get("Quantity") or row.get("qty"))
        notes = _as_str(row.get("notes") or row.get("Notes"))
        if not vendor_style or not labor_name:
            skipped += 1
            continue
        try:
            style = _resolve_style(vendor_style)
            labor = _resolve_labor_operation(labor_name)
            if not style or not labor:
                errors.append(f"Missing reference for style {vendor_style} or labor {labor_name}")
                skipped += 1
                continue
            existing = StyleLabor.query.filter_by(style_id=style.id, labor_operation_id=labor.id).first()
            if existing:
                existing.time_hours = time_hours
                if quantity is not None:
                    existing.quantity = quantity
                existing.notes = notes
                updated += 1
            else:
                db.session.add(
                    StyleLabor(
                        style_id=style.id,
                        labor_operation_id=labor.id,
                        time_hours=time_hours,
                        quantity=1 if quantity is None else quantity,
                        notes=notes,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f"Row error: {exc}")
    return created, updated, skipped, errors


_IMPORT_ORDER: List[Tuple[str, str, Any]] = [
    ("fabric_vendors", "FabricVendors", _import_fabric_vendors),
    ("notion_vendors", "NotionVendors", _import_notion_vendors),
    ("fabrics", "Fabrics", _import_fabrics),
    ("notions", "Notions", _import_notions),
    ("labor_operations", "LaborOperations", _import_labor_operations),
    ("cleaning_costs", "CleaningCosts", _import_cleaning_costs),
    ("size_variants", "SizeVariants", _import_size_variants),
    ("styles", "Styles", _import_styles),
    ("style_fabrics", "StyleFabrics", _import_style_fabrics),
    ("style_notions", "StyleNotions", _import_style_notions),
    ("style_labor", "StyleLabor", _import_style_labor),
]


def import_workbook(file_path: str) -> Dict[str, Any]:
    """Import an Excel workbook into the database.

    Expected sheet names (case-insensitive, spaces ignored):
      - FabricVendors
      - NotionVendors
      - Fabrics
      - Notions
      - LaborOperations
      - CleaningCosts
      - SizeVariants
      - Styles
      - StyleFabrics
      - StyleNotions
      - StyleLabor
    """
    xls = pd.read_excel(file_path, sheet_name=None)

    def normalize_sheet_name(name: str) -> str:
        return name.strip().lower().replace(" ", "_")

    normalized: Dict[str, pd.DataFrame] = {normalize_sheet_name(k): v for k, v in xls.items()}
    summary: Dict[str, Any] = {}

    for normalized_name, canonical, importer in _IMPORT_ORDER:
        df = normalized.get(normalized_name)
        if df is None:
            _summ(summary, canonical, created=0, updated=0, skipped=0, errors=["Sheet not found; skipped"]) 
            continue
        try:
            created, updated, skipped, errors = importer(df)
            db.session.commit()
            _summ(summary, canonical, created=created, updated=updated, skipped=skipped, errors=errors)
        except Exception as exc:
            db.session.rollback()
            _summ(summary, canonical, created=0, updated=0, skipped=len(df), errors=[f"Import failed: {exc}"])

    return summary

