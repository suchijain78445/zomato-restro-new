import hashlib
import re
from typing import Any, Optional

import pandas as pd


def parse_rating(val: Any) -> Optional[float]:
    """
    Parses rate strings like '4.1/5', ' 4.1 /5 ', 'NEW', '-', '', non-numeric values.
    Returns float rounded to 1 decimal place in range [0.0, 5.0], or None.
    """
    if pd.isna(val) or val is None:
        return None

    s = str(val).strip()
    if not s or s.upper() in ("NEW", "-", "N/A"):
        return None

    # Handle standard 'X/5' pattern or plain floats
    match = re.search(r"(-?[0-9]+(?:\.[0-9]+)?)\s*/\s*5", s)

    if match:
        try:
            r = float(match.group(1))
            return max(0.0, min(5.0, round(r, 1)))
        except ValueError:
            return None

    # Try direct numeric conversion if string is purely numeric e.g. "4.1"
    try:
        r = float(s)
        return max(0.0, min(5.0, round(r, 1)))
    except ValueError:
        return None


def parse_cost(val: Any) -> Optional[int]:
    """
    Parses approx_cost strings like '1,200', '300', handling commas and invalid strings.
    Returns positive integer cost or None for invalid/zero/negative values.
    """
    if pd.isna(val) or val is None:
        return None

    s = str(val).strip().replace(",", "")
    if not s:
        return None

    try:
        cost = int(float(s))
        return cost if cost > 0 else None
    except ValueError:
        return None


def assign_budget_tier(cost: Optional[int]) -> Optional[str]:
    """
    Assigns budget tier based on cost for two:
    - low: cost <= 500
    - medium: 501 - 1500
    - high: > 1500
    - None if cost is None or invalid
    """
    if cost is None or cost <= 0:
        return None
    if cost <= 500:
        return "low"
    elif cost <= 1500:
        return "medium"
    else:
        return "high"


def parse_cuisines(val: Any) -> list[str]:
    """
    Splits cuisine string by comma, strips whitespace, converts to lowercase,
    and deduplicates while preserving order.
    """
    if pd.isna(val) or val is None:
        return []

    s = str(val).strip()
    if not s:
        return []

    tokens = [c.strip().lower() for c in s.split(",") if c.strip()]
    seen = set()
    result = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            result.append(token)
    return result


def parse_boolean(val: Any) -> bool:
    """
    Converts 'Yes'/'yes'/True/1 to True, otherwise False.
    """
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ("yes", "true", "1")


def parse_dishes(val: Any) -> list[str]:
    """
    Splits dish_liked string by comma, strips whitespace, and removes empties.
    """
    if pd.isna(val) or val is None:
        return []
    s = str(val).strip()
    if not s:
        return []
    return [d.strip() for d in s.split(",") if d.strip()]


def generate_restaurant_id(name: str, address: str) -> str:
    """
    Generates a deterministic MD5 hash string from lowercased trimmed name and address.
    """
    clean_name = str(name or "").strip().lower()
    clean_addr = str(address or "").strip().lower()
    raw_str = f"{clean_name}::{clean_addr}"
    return hashlib.md5(raw_str.encode("utf-8")).hexdigest()


def preprocess_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw Zomato DataFrame into cleaned, normalized DataFrame.
    Drops missing name/city, generates deterministic ID, deduplicates,
    and parses all fields.
    """
    df = raw_df.copy()

    # Standardize column mapping to handle variations
    column_mapping = {
        "listed_in(city)": "city",
        "approx_cost(for two people)": "cost_raw",
        "rate": "rate_raw",
        "rest_type": "restaurant_type",
        "dish_liked": "dish_liked_raw",
    }
    df = df.rename(
        columns={k: v for k, v in column_mapping.items() if k in df.columns}
    )

    # Ensure required columns exist
    if "city" not in df.columns and "listed_in_city" in df.columns:
        df = df.rename(columns={"listed_in_city": "city"})

    # Clean text for name and city
    if "name" in df.columns:
        df["name"] = df["name"].astype(str).str.strip()
    else:
        df["name"] = ""

    if "city" in df.columns:
        df["city"] = df["city"].astype(str).str.strip()
    else:
        df["city"] = ""

    if "address" in df.columns:
        df["address"] = df["address"].astype(str).str.strip()
    else:
        df["address"] = ""

    if "location" in df.columns:
        df["location"] = df["location"].astype(str).str.strip()
    else:
        df["location"] = ""


    # Drop rows missing essential name or city
    df = df[
        (df["name"].str.len() > 0)
        & (df["name"] != "nan")
        & (df["name"] != "None")
        & (df["city"].str.len() > 0)
        & (df["city"] != "nan")
        & (df["city"] != "None")
    ].copy()

    # Generate IDs
    df["id"] = df.apply(
        lambda r: generate_restaurant_id(r["name"], r["address"]), axis=1
    )

    # Deduplicate by ID (keep first occurrence)
    df = df.drop_duplicates(subset=["id"], keep="first").copy()

    # Clean fields
    if "rate_raw" in df.columns:
        df["rating"] = df["rate_raw"].apply(parse_rating)
    else:
        df["rating"] = None

    if "cost_raw" in df.columns:
        df["cost_for_two"] = df["cost_raw"].apply(parse_cost)
    else:
        df["cost_for_two"] = None

    df["budget_tier"] = df["cost_for_two"].apply(assign_budget_tier)

    if "cuisines" in df.columns:
        df["cuisines"] = df["cuisines"].apply(parse_cuisines)
    else:
        df["cuisines"] = [[]] * len(df)

    if "online_order" in df.columns:
        df["online_order"] = df["online_order"].apply(parse_boolean)
    else:
        df["online_order"] = False

    if "book_table" in df.columns:
        df["book_table"] = df["book_table"].apply(parse_boolean)
    else:
        df["book_table"] = False

    if "votes" in df.columns:
        df["votes"] = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype(int)
    else:
        df["votes"] = 0

    if "dish_liked_raw" in df.columns:
        df["popular_dishes"] = df["dish_liked_raw"].apply(parse_dishes)
    else:
        df["popular_dishes"] = [[]] * len(df)

    if "url" not in df.columns:
        df["url"] = None
    else:
        df["url"] = df["url"].apply(
            lambda v: str(v).strip()
            if pd.notna(v) and str(v).strip() != "nan"
            else None
        )

    if "restaurant_type" not in df.columns:
        df["restaurant_type"] = None
    else:
        df["restaurant_type"] = df["restaurant_type"].apply(
            lambda v: str(v).strip()
            if pd.notna(v) and str(v).strip() != "nan"
            else None
        )


    # Select final columns matching Restaurant domain model
    final_cols = [
        "id",
        "name",
        "city",
        "location",
        "cuisines",
        "rating",
        "cost_for_two",
        "budget_tier",
        "restaurant_type",
        "votes",
        "online_order",
        "book_table",
        "address",
        "url",
        "popular_dishes",
    ]

    return df[final_cols].reset_index(drop=True)
