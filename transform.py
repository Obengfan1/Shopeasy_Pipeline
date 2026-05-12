import pandas as pd
import json
import uuid
import re


# -------------------------------------------------------
# STEP 1: Load raw JSON with explicit UTF-8 encoding
# Â£ means the file was saved without utf-8 and read wrong
# ensure_ascii=False when dumping + utf-8 when loading fixes it
# -------------------------------------------------------
def load_raw_data(filepath="raw_books.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    # Fix any remaining mojibake (Â£ → £) by re-encoding
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(lambda x: fix_encoding(x) if isinstance(x, str) else x)

    print(f"Loaded {len(df)} raw records")
    print("Sample prices:", df["price"].head().tolist())
    return df


def fix_encoding(text):
    """Fix Â£ mojibake caused by latin-1/utf-8 mismatch"""
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text  # already correct, leave it


# -------------------------------------------------------
# STEP 2: Clean price — strip currency symbol, convert to float
# -------------------------------------------------------
def clean_price(df):
    df["price"] = df["price"].astype(str).apply(
        lambda x: re.sub(r"[^\d.]", "", x)   # keep only digits and dot
    )
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    print(f"After price clean — nulls: {df['price'].isna().sum()}")
    print("Sample cleaned prices:", df["price"].head().tolist())
    return df


# -------------------------------------------------------
# STEP 3: Standardise rating
# -------------------------------------------------------
def clean_rating(df):
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["rating"] = df["rating"].apply(lambda x: x if pd.notna(x) and 1 <= x <= 5 else 0)
    return df


# -------------------------------------------------------
# STEP 4: Handle missing values
# -------------------------------------------------------
def handle_missing(df):
    before = len(df)
    df = df.dropna(subset=["name", "price"])   # ✅ reassign instead of inplace
    after = len(df)
    print(f"Dropped {before - after} rows with missing name/price")
    df["category"] = df["category"].fillna("Unknown")
    df["rating"]   = df["rating"].fillna(0).astype(int)
    return df


# -------------------------------------------------------
# STEP 5: Remove duplicates
# -------------------------------------------------------
def remove_duplicates(df):
    before = len(df)
    df = df.drop_duplicates(subset=["name", "price"], keep="first")
    after = len(df)
    print(f"Removed {before - after} duplicate rows")
    return df


# -------------------------------------------------------
# STEP 6: Add unique ID and timestamp
# -------------------------------------------------------
def add_metadata(df):
    df = df.copy()
    df["id"]         = [str(uuid.uuid4()) for _ in range(len(df))]
    df["scraped_at"] = pd.Timestamp.now()
    return df


# -------------------------------------------------------
# STEP 7: Run all steps
# -------------------------------------------------------
def clean_data(filepath="raw_books.json"):
    df = load_raw_data(filepath)
    df = clean_price(df)
    df = clean_rating(df)
    df = handle_missing(df)
    df = remove_duplicates(df)
    df = add_metadata(df)

    df = df[["id", "name", "category", "price", "rating", "scraped_at"]]

    print(f"\nFinal clean records: {len(df)}")
    print(df.head())

    df.to_csv("clean_books.csv", index=False, encoding="utf-8")
    print("Cleaned data saved to clean_books.csv")
    return df


if __name__ == "__main__":
    clean_data()
