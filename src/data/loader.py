"""
Cartly Data Loader Module
Handles loading, column mapping, and schema validation for CSV and Excel files.
"""

import io
from typing import Tuple, List, Dict, Any, Union
import pandas as pd

# Expected canonical columns
CANONICAL_COLUMNS = [
    "Invoice",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "Price",
    "Customer ID",
    "Country"
]

# Alternate column name mappings
COLUMN_ALIASES = {
    "invoice": "Invoice",
    "invoiceno": "Invoice",
    "invoice_no": "Invoice",
    "stockcode": "StockCode",
    "stock_code": "StockCode",
    "item_code": "StockCode",
    "description": "Description",
    "item_name": "Description",
    "product_name": "Description",
    "quantity": "Quantity",
    "qty": "Quantity",
    "invoicedate": "InvoiceDate",
    "invoice_date": "InvoiceDate",
    "date": "InvoiceDate",
    "price": "Price",
    "unitprice": "Price",
    "unit_price": "Price",
    "rate": "Price",
    "customer id": "Customer ID",
    "customer_id": "Customer ID",
    "customerid": "Customer ID",
    "cust_id": "Customer ID",
    "client_id": "Customer ID",
    "country": "Country",
    "region": "Country"
}


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Map common variant column names to the standard canonical schema."""
    renamed = {}
    for col in df.columns:
        norm_key = str(col).strip().lower().replace(" ", "").replace("_", "")
        # Also check direct lowercase match
        direct_key = str(col).strip().lower()
        if direct_key in COLUMN_ALIASES:
            renamed[col] = COLUMN_ALIASES[direct_key]
        elif norm_key in COLUMN_ALIASES:
            renamed[col] = COLUMN_ALIASES[norm_key]
    return df.rename(columns=renamed)


def validate_columns(df: pd.DataFrame) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that all required canonical columns are present in DataFrame.
    Returns: (is_valid, present_columns, missing_columns)
    """
    normalized_df = normalize_column_names(df)
    present = [col for col in CANONICAL_COLUMNS if col in normalized_df.columns]
    missing = [col for col in CANONICAL_COLUMNS if col not in normalized_df.columns]
    is_valid = len(missing) == 0
    return is_valid, present, missing


def load_dataset(
    file_or_path: Union[str, io.BytesIO, bytes],
    file_type: str = "csv",
    sheet_name: Union[str, int, None] = 0,
    nrows: Union[int, None] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load CSV or Excel file into a normalized pandas DataFrame with validation info.
    
    Returns:
        (df, metadata_dict)
    """
    metadata: Dict[str, Any] = {
        "file_type": file_type.lower(),
        "is_valid": False,
        "present_columns": [],
        "missing_columns": [],
        "original_rows": 0,
        "error_message": None
    }

    try:
        if file_type.lower() in ["csv", "txt"]:
            # Try reading with common encodings
            try:
                df = pd.read_csv(file_or_path, nrows=nrows, encoding="utf-8", low_memory=False)
            except UnicodeDecodeError:
                if hasattr(file_or_path, "seek"):
                    file_or_path.seek(0)
                df = pd.read_csv(file_or_path, nrows=nrows, encoding="latin1", low_memory=False)
        elif file_type.lower() in ["xlsx", "xls", "excel"]:
            df = pd.read_excel(file_or_path, sheet_name=sheet_name, nrows=nrows)
        else:
            metadata["error_message"] = f"Unsupported file format: {file_type}. Please upload a CSV or Excel (.xlsx) file."
            return pd.DataFrame(), metadata

        metadata["original_rows"] = len(df)
        df = normalize_column_names(df)
        is_valid, present, missing = validate_columns(df)

        metadata["is_valid"] = is_valid
        metadata["present_columns"] = present
        metadata["missing_columns"] = missing

        if not is_valid:
            metadata["error_message"] = (
                f"Validation Error: Missing required columns: {', '.join(missing)}. "
                f"Expected columns: {', '.join(CANONICAL_COLUMNS)}"
            )

        return df, metadata

    except Exception as e:
        metadata["error_message"] = f"Failed to read file: {str(e)}"
        return pd.DataFrame(), metadata
